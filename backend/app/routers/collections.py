import csv
import io
import os
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.collection import Collection, CollectionItem
from app.models.observation import Observation
from app.models.image import ObservationImage
from app.schemas.collection import (
    CollectionCreate, CollectionUpdate, CollectionResponse,
    CollectionItemCreate, CollectionItemResponse
)
from app.services.species_enrichment import SpeciesEnrichmentService

router = APIRouter(prefix="/api/collections", tags=["Species Collections"])


def _enrich_item_response(item: CollectionItem, db: Session) -> CollectionItemResponse:
    item_res = CollectionItemResponse.model_validate(item)
    
    # 1. If linked observation exists, attach observation details
    if item.observation_id:
        obs = db.query(Observation).filter(Observation.id == item.observation_id).first()
        if obs:
            item_res.confidence = obs.ai_confidence
            item_res.observation_date = obs.observation_date
            item_res.latitude = obs.latitude
            item_res.longitude = obs.longitude
            item_res.notes = obs.notes
            
            # Fetch first image path
            img = db.query(ObservationImage).filter(ObservationImage.observation_id == obs.id).first()
            if img:
                # Provide web static path
                item_res.observation_image_url = f"/static/uploads/{os.path.basename(img.file_path)}"

    # 2. Get reference image from enrichment service
    try:
        profile = SpeciesEnrichmentService.get_species_profile(item.scientific_name, common_name=item.common_name, category=item.category)
        if profile and profile.reference_images and len(profile.reference_images) > 0:
            item_res.reference_image_url = profile.reference_images[0].url
    except Exception as e:
        print(f"[Collections] Error fetching reference image for {item.scientific_name}: {e}")

    return item_res


def _build_collection_response(coll: Collection, db: Session) -> CollectionResponse:
    items_enriched = [_enrich_item_response(item, db) for item in coll.items]
    
    # Calculate unique species count
    unique_species = set(item.scientific_name.lower() for item in coll.items)
    species_count = len(unique_species)
    obs_count = sum(1 for item in coll.items if item.item_type == "observation")
    
    # Pick cover image URL
    cover_url = None
    for item_res in items_enriched:
        if item_res.observation_image_url:
            cover_url = item_res.observation_image_url
            break
        elif item_res.reference_image_url and not cover_url:
            cover_url = item_res.reference_image_url
            
    return CollectionResponse(
        id=coll.id,
        name=coll.name,
        description=coll.description,
        created_at=coll.created_at,
        updated_at=coll.updated_at,
        species_count=species_count,
        observation_count=obs_count,
        cover_image_url=cover_url,
        items=items_enriched
    )


@router.get("", response_model=List[CollectionResponse])
def list_collections(db: Session = Depends(get_db)):
    collections = db.query(Collection).order_by(Collection.updated_at.desc()).all()
    return [_build_collection_response(coll, db) for coll in collections]


@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
def create_collection(payload: CollectionCreate, db: Session = Depends(get_db)):
    clean_name = payload.name.strip() if payload.name else ""
    if not clean_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Collection name cannot be empty")
        
    coll = Collection(
        name=clean_name,
        description=payload.description.strip() if payload.description else None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(coll)
    db.commit()
    db.refresh(coll)
    return _build_collection_response(coll, db)


@router.get("/{id}", response_model=CollectionResponse)
def get_collection(id: int, db: Session = Depends(get_db)):
    coll = db.query(Collection).filter(Collection.id == id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    return _build_collection_response(coll, db)


@router.put("/{id}", response_model=CollectionResponse)
def update_collection(id: int, payload: CollectionUpdate, db: Session = Depends(get_db)):
    coll = db.query(Collection).filter(Collection.id == id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    if payload.name is not None:
        coll.name = payload.name.strip()
    if payload.description is not None:
        coll.description = payload.description.strip()
        
    coll.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(coll)
    return _build_collection_response(coll, db)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(id: int, db: Session = Depends(get_db)):
    coll = db.query(Collection).filter(Collection.id == id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    db.delete(coll)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{id}/items", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
def add_collection_item(id: int, payload: CollectionItemCreate, db: Session = Depends(get_db)):
    coll = db.query(Collection).filter(Collection.id == id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    # Check if duplicate item already exists in collection
    existing = db.query(CollectionItem).filter(
        CollectionItem.collection_id == id,
        CollectionItem.scientific_name == payload.scientific_name,
        CollectionItem.observation_id == payload.observation_id
    ).first()
    
    if existing:
        return _enrich_item_response(existing, db)
        
    item = CollectionItem(
        collection_id=id,
        item_type=payload.item_type,
        scientific_name=payload.scientific_name.strip(),
        common_name=payload.common_name.strip() if payload.common_name else None,
        category=(payload.category or "other").lower(),
        observation_id=payload.observation_id,
        created_at=datetime.utcnow()
    )
    
    coll.updated_at = datetime.utcnow()
    db.add(item)
    db.commit()
    db.refresh(item)
    return _enrich_item_response(item, db)


@router.delete("/{id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_collection_item(id: int, item_id: int, db: Session = Depends(get_db)):
    item = db.query(CollectionItem).filter(
        CollectionItem.id == item_id,
        CollectionItem.collection_id == id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in collection")
    
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{id}/export/csv")
def export_collection_csv(id: int, db: Session = Depends(get_db)):
    coll = db.query(Collection).filter(Collection.id == id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
    
    enriched = _build_collection_response(coll, db)
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Collection Name", "Item Type", "Source Type", "Common Name", "Scientific Name", 
        "Category", "AI Confidence", "Observation Date", "Latitude", "Longitude", 
        "Notes", "Observation ID", "Item Created At"
    ])
    
    for item in enriched.items:
        source_type = "OBSERVATION" if item.item_type == "observation" else "REFERENCE / EXPLORED"
        writer.writerow([
            coll.name,
            item.item_type,
            source_type,
            item.common_name or "",
            item.scientific_name,
            item.category or "other",
            f"{item.confidence * 100:.1f}%" if item.confidence is not None else "",
            item.observation_date.strftime("%Y-%m-%d %H:%M:%S") if item.observation_date else "",
            item.latitude if item.latitude is not None else "",
            item.longitude if item.longitude is not None else "",
            item.notes or "",
            item.observation_id or "",
            item.created_at.strftime("%Y-%m-%d %H:%M:%S")
        ])
        
    output.seek(0)
    filename = f"GreenLens_Collection_{coll.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.csv"
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{id}/export/pdf")
def export_collection_pdf(id: int, db: Session = Depends(get_db)):
    coll = db.query(Collection).filter(Collection.id == id).first()
    if not coll:
        raise HTTPException(status_code=404, detail="Collection not found")
        
    enriched = _build_collection_response(coll, db)
    
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Brand Palette
    COLOR_PRIMARY = colors.HexColor("#1b4332") # Dark green
    COLOR_ACCENT = colors.HexColor("#2d6a4f")  # Medium green
    COLOR_TEXT = colors.HexColor("#1f2937")    # Slate text
    COLOR_MUTED = colors.HexColor("#6b7280")   # Muted gray
    COLOR_BG_CARD = colors.HexColor("#f8fafc") # Card background
    
    title_style = ParagraphStyle(
        'CoverTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=28,
        leading=34,
        textColor=COLOR_PRIMARY,
        spaceAfter=12
    )
    
    subtitle_style = ParagraphStyle(
        'CoverSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=12,
        leading=16,
        textColor=COLOR_MUTED,
        spaceAfter=20
    )

    section_heading = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        textColor=COLOR_PRIMARY,
        spaceBefore=14,
        spaceAfter=8
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=COLOR_TEXT
    )
    
    badge_obs_style = ParagraphStyle(
        'BadgeObs',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#15803d") # Green badge text
    )
    
    badge_ref_style = ParagraphStyle(
        'BadgeRef',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.HexColor("#0369a1") # Blue badge text
    )

    elements = []

    # 1. Cover Page Header
    elements.append(Paragraph("GREENLENS AI BIODIVERSITY REPORT", ParagraphStyle('BrandHeader', fontName='Helvetica-Bold', fontSize=10, textColor=COLOR_ACCENT, leading=12, spaceAfter=8)))
    elements.append(Paragraph(coll.name, title_style))
    if coll.description:
        elements.append(Paragraph(coll.description, subtitle_style))
    elements.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%B %d, %Y')} | Personal Biodiversity Collection Record", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=COLOR_PRIMARY, spaceBefore=5, spaceAfter=20))
    
    # 2. Collection Overview Summary Table
    categories = {}
    for item in enriched.items:
        cat = (item.category or "other").capitalize()
        categories[cat] = categories.get(cat, 0) + 1
        
    summary_data = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Count</b>", body_style)],
        [Paragraph("Total Species", body_style), Paragraph(str(enriched.species_count), body_style)],
        [Paragraph("Total Observations", body_style), Paragraph(str(enriched.observation_count), body_style)],
        [Paragraph("Explored / Reference Records", body_style), Paragraph(str(len(enriched.items) - enriched.observation_count), body_style)],
    ]
    for cat_name, cat_count in sorted(categories.items()):
        summary_data.append([Paragraph(f"Category: {cat_name}", body_style), Paragraph(str(cat_count), body_style)])

    summary_table = Table(summary_data, colWidths=[250, 250])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('TEXTCOLOR', (0,0), (-1,0), COLOR_PRIMARY),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")])
    ]))
    
    elements.append(Paragraph("Collection Summary", section_heading))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # 3. Species Records Section
    elements.append(Paragraph("Species Records", section_heading))
    elements.append(HRFlowable(width="100%", thickness=1, color=COLOR_ACCENT, spaceBefore=4, spaceAfter=15))
    
    if not enriched.items:
        elements.append(Paragraph("No species or observations have been added to this collection yet.", body_style))
    else:
        for idx, item in enumerate(enriched.items, 1):
            is_obs = item.item_type == "observation"
            tag_text = "YOUR OBSERVATION" if is_obs else "REFERENCE / EXPLORED"
            badge = Paragraph(f"<b>[{tag_text}]</b>", badge_obs_style if is_obs else badge_ref_style)
            
            common = item.common_name or "Common name unavailable"
            sci = item.scientific_name
            cat = (item.category or "other").capitalize()
            
            details_text = f"<b>{common}</b> (<i>{sci}</i>)<br/>Category: {cat}"
            if is_obs:
                if item.observation_date:
                    details_text += f"<br/>Date: {item.observation_date.strftime('%Y-%m-%d %H:%M')}"
                if item.confidence is not None:
                    details_text += f" | AI Confidence: {item.confidence * 100:.1f}%"
                if item.latitude and item.longitude:
                    details_text += f"<br/>Location: {item.latitude:.4f}, {item.longitude:.4f}"
                if item.notes:
                    details_text += f"<br/>Notes: {item.notes}"

            card_content = [
                [Paragraph(f"<b>#{idx}</b>", body_style), Paragraph(details_text, body_style), badge]
            ]
            
            card_table = Table(card_content, colWidths=[30, 320, 150])
            card_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), COLOR_BG_CARD),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            
            elements.append(card_table)
            elements.append(Spacer(1, 10))
            
    # Build PDF Document
    doc.build(elements)
    buffer.seek(0)
    
    filename = f"GreenLens_Report_{coll.name.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
