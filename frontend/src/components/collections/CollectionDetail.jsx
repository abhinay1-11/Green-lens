import React, { useState, useEffect } from 'react';
import { ArrowLeft, Download, FileText, Trash2, Calendar, MapPin, Filter, BookOpen, Compass, Info, CheckCircle } from 'lucide-react';
import { removeCollectionItem, getCollectionExportPdfUrl, getCollectionExportCsvUrl, getSpeciesProfile } from '../../services/api';
import BiodiversityImagePlaceholder from './BiodiversityImagePlaceholder';

export function normalizeCollectionItem(item) {
  if (!item) return null;
  const id = item.id;
  const item_type = item.item_type || (item.observation_id ? 'observation' : 'explored');
  const scientific_name = item.scientific_name || item.scientificName || '';
  const common_name = item.common_name || item.commonName || null;
  const category = (item.category || 'other').toLowerCase();
  const observation_id = item.observation_id || item.observationId || null;
  const observation_image = item.observation_image_url || item.observation_image || item.observationImageUrl || null;
  const reference_image = item.reference_image_url || item.reference_image || item.referenceImageUrl || null;
  const confidence = item.confidence ?? null;
  const observation_date = item.observation_date || item.observationDate || null;
  const latitude = item.latitude ?? null;
  const longitude = item.longitude ?? null;
  const notes = item.notes || null;

  return {
    id,
    item_type,
    scientific_name,
    common_name,
    category,
    observation_id,
    observation_image,
    reference_image,
    confidence,
    observation_date,
    latitude,
    longitude,
    notes
  };
}

export default function CollectionDetail({ collection, onBack, onItemRemoved, onNavigateExplore }) {
  const [activeCategoryFilter, setActiveCategoryFilter] = useState('ALL');
  const [removingItemId, setRemovingItemId] = useState(null);
  const [resolvedImages, setResolvedImages] = useState({});
  const [failedImages, setFailedImages] = useState({});
  const [selectedDetailItem, setSelectedDetailItem] = useState(null);
  const [detailProfile, setDetailProfile] = useState(null);

  useEffect(() => {
    if (selectedDetailItem) {
      getSpeciesProfile(selectedDetailItem.scientific_name, selectedDetailItem.common_name, selectedDetailItem.category)
        .then((data) => setDetailProfile(data))
        .catch(() => setDetailProfile(null));
    } else {
      setDetailProfile(null);
    }
  }, [selectedDetailItem]);

  const itemsRaw = collection?.items || [];
  const normalizedItems = itemsRaw.map(normalizeCollectionItem).filter(Boolean);

  // Dynamic image resolver for reference images if missing
  useEffect(() => {
    normalizedItems.forEach((item) => {
      if (!item.observation_image && !item.reference_image && item.scientific_name) {
        if (!resolvedImages[item.scientific_name]) {
          getSpeciesProfile(item.scientific_name, item.common_name || '', item.category || '')
            .then((prof) => {
              if (prof && prof.reference_images && prof.reference_images.length > 0) {
                setResolvedImages((prev) => ({
                  ...prev,
                  [item.scientific_name]: prof.reference_images[0].url
                }));
              }
            })
            .catch(() => {});
        }
      }
    });
  }, [collection]);

  if (!collection) return null;

  const categories = ['ALL', 'BIRDS', 'PLANTS', 'TREES', 'INSECTS', 'OTHER'];

  const filteredItems = normalizedItems.filter((item) => {
    if (activeCategoryFilter === 'ALL') return true;
    const cat = item.category.toUpperCase();
    if (activeCategoryFilter === 'BIRDS') return cat.includes('BIRD');
    if (activeCategoryFilter === 'PLANTS') return cat.includes('PLANT') || cat.includes('FLOWER');
    if (activeCategoryFilter === 'TREES') return cat.includes('TREE');
    if (activeCategoryFilter === 'INSECTS') return cat.includes('INSECT') || cat.includes('BUG');
    if (activeCategoryFilter === 'OTHER') {
      return !['BIRD', 'PLANT', 'FLOWER', 'TREE', 'INSECT', 'BUG'].some((c) => cat.includes(c));
    }
    return true;
  });

  const handleRemoveItem = async (itemId) => {
    if (!window.confirm('Remove this item from the collection? (Your recorded observation will NOT be deleted)')) return;
    setRemovingItemId(itemId);
    try {
      await removeCollectionItem(collection.id, itemId);
      if (onItemRemoved) onItemRemoved(itemId);
    } catch (err) {
      console.error('Error removing item from collection:', err);
    } finally {
      setRemovingItemId(null);
    }
  };

  const handleExportPdf = () => {
    const url = getCollectionExportPdfUrl(collection.id);
    window.open(url, '_blank');
  };

  const handleExportCsv = () => {
    const url = getCollectionExportCsvUrl(collection.id);
    window.open(url, '_blank');
  };

  const speciesCount = collection.species_count || new Set(normalizedItems.map((i) => i.scientific_name.toLowerCase())).size;
  const observationCount = collection.observation_count || normalizedItems.filter((i) => i.item_type === 'observation').length;
  const exploredCount = normalizedItems.length - observationCount;

  return (
    <div className="space-y-8 animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Bar */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justify: 'space-between',
          gap: '16px',
          borderBottom: '1px solid var(--border-glass)',
          paddingBottom: '20px'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            type="button"
            onClick={onBack}
            className="btn btn-secondary"
            style={{ padding: '10px 14px', borderRadius: 'var(--radius-md)' }}
            title="Back to Collections"
          >
            <ArrowLeft size={18} />
            <span>Collections</span>
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.025em' }}>
                {collection.name}
              </h1>
              <span className="badge badge-plant">Collection Book</span>
            </div>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              {collection.description || 'Species and observations recorded in this collection.'}
            </p>
          </div>
        </div>

        {/* Export Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            type="button"
            onClick={handleExportCsv}
            className="btn btn-secondary"
            style={{ padding: '9px 16px', fontSize: '0.82rem' }}
          >
            <Download size={15} color="var(--accent-secondary)" />
            Export CSV
          </button>
          <button
            type="button"
            onClick={handleExportPdf}
            className="btn btn-primary"
            style={{ padding: '9px 18px', fontSize: '0.82rem' }}
          >
            <FileText size={15} />
            Export PDF Report
          </button>
        </div>
      </div>

      {/* Compact Metrics Summary */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '14px'
        }}
      >
        <div
          className="glass-panel"
          style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '4px', background: 'var(--bg-card)' }}
        >
          <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Recorded Species
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-primary)' }}>
            {speciesCount}
          </span>
        </div>
        <div
          className="glass-panel"
          style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '4px', background: 'var(--bg-card)' }}
        >
          <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Observations
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-bird, #3b82f6)' }}>
            {observationCount}
          </span>
        </div>
        <div
          className="glass-panel"
          style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '4px', background: 'var(--bg-card)' }}
        >
          <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Explored Records
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--color-insect, #f59e0b)' }}>
            {exploredCount}
          </span>
        </div>
        <div
          className="glass-panel"
          style={{ padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '4px', background: 'var(--bg-card)' }}
        >
          <span style={{ fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
            Total Records
          </span>
          <span style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)' }}>
            {normalizedItems.length}
          </span>
        </div>
      </div>

      {/* Category Filter Pills (Matching Species Explorer) */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          overflowX: 'auto',
          paddingBottom: '8px',
          borderBottom: '1px solid var(--border-glass)'
        }}
      >
        <Filter size={16} style={{ color: 'var(--text-muted)', flexShrink: 0, marginRight: '4px' }} />
        {categories.map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategoryFilter(cat)}
            className={activeCategoryFilter === cat ? 'btn btn-primary' : 'btn btn-secondary'}
            style={{ padding: '6px 14px', fontSize: '0.78rem', borderRadius: 'var(--radius-full)', flexShrink: 0 }}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Collection Species Grid */}
      {filteredItems.length === 0 ? (
        <div
          className="glass-panel"
          style={{
            padding: '60px 24px',
            textAlign: 'center',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justify: 'center',
            gap: '14px',
            background: 'var(--bg-card)'
          }}
        >
          <BookOpen size={48} color="var(--accent-primary)" opacity={0.7} />
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)' }}>
              {normalizedItems.length === 0 ? 'Your collection is empty' : 'No species match this category filter'}
            </h3>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '420px', margin: '6px auto 0', lineHeight: 1.5 }}>
              {normalizedItems.length === 0
                ? 'Add species from Global Species Explorer or save field observations to this collection.'
                : 'Try selecting another category filter above or add more species to this collection.'}
            </p>
          </div>
          {onNavigateExplore && (
            <button
              type="button"
              onClick={onNavigateExplore}
              className="btn btn-primary"
              style={{ padding: '10px 20px', fontSize: '0.85rem', marginTop: '6px' }}
            >
              <Compass size={16} />
              Explore Species
            </button>
          )}
        </div>
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
            gap: '20px'
          }}
        >
          {filteredItems.map((item) => {
            const isObs = item.item_type === 'observation';
            const primaryImg = item.observation_image || item.reference_image || resolvedImages[item.scientific_name];
            const hasFailed = failedImages[item.id];

            const categoryBadgeClass = item.category.includes('bird')
              ? 'badge-bird'
              : item.category.includes('plant') || item.category.includes('flower') || item.category.includes('tree')
              ? 'badge-plant'
              : item.category.includes('insect')
              ? 'badge-insect'
              : 'badge-unknown';

            return (
              <div
                key={item.id}
                className="glass-panel glass-panel-hover"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justify: 'space-between',
                  overflow: 'hidden',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-glass)'
                }}
              >
                {/* Fixed 16:10 Thumbnail Container */}
                <div
                  style={{
                    width: '100%',
                    aspectRatio: '16 / 10',
                    position: 'relative',
                    overflow: 'hidden',
                    background: 'var(--bg-tertiary)',
                    borderBottom: '1px solid var(--border-glass)'
                  }}
                >
                  {primaryImg && !hasFailed ? (
                    <img
                      src={primaryImg}
                      alt={item.common_name || item.scientific_name}
                      onError={() => setFailedImages((prev) => ({ ...prev, [item.id]: true }))}
                      style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    />
                  ) : (
                    <BiodiversityImagePlaceholder category={item.category} title={item.common_name || item.scientific_name} />
                  )}

                  {/* Top-Left Source Badge */}
                  <div style={{ position: 'absolute', top: '10px', left: '10px' }}>
                    {isObs ? (
                      <span
                        className="badge"
                        style={{
                          background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                          color: '#ffffff',
                          fontSize: '0.68rem',
                          padding: '3px 9px',
                          boxShadow: '0 2px 6px rgba(0,0,0,0.25)'
                        }}
                      >
                        YOUR OBSERVATION
                      </span>
                    ) : (
                      <span
                        className="badge"
                        style={{
                          background: 'linear-gradient(135deg, #0284c7 0%, #0369a1 100%)',
                          color: '#ffffff',
                          fontSize: '0.68rem',
                          padding: '3px 9px',
                          boxShadow: '0 2px 6px rgba(0,0,0,0.25)'
                        }}
                      >
                        SPECIES REFERENCE
                      </span>
                    )}
                  </div>

                  {/* Top-Right Category Pill */}
                  <div style={{ position: 'absolute', top: '10px', right: '10px' }}>
                    <span className={`badge ${categoryBadgeClass}`} style={{ fontSize: '0.7rem', padding: '3px 9px' }}>
                      {item.category}
                    </span>
                  </div>
                </div>

                {/* Card Content & Taxonomy */}
                <div style={{ padding: '16px 18px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '12px' }}>
                  <div>
                    <h3
                      style={{
                        fontSize: '1.05rem',
                        fontWeight: 800,
                        color: 'var(--text-main)',
                        lineHeight: 1.3,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                    >
                      {item.common_name || item.scientific_name}
                    </h3>
                    <p style={{ fontSize: '0.82rem', fontStyle: 'italic', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {item.scientific_name}
                    </p>

                    {/* Metadata Section */}
                    <div style={{ marginTop: '12px', display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
                      {isObs && item.confidence !== null && (
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <span>AI Confidence:</span>
                          <span style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
                            {(item.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}
                      {isObs && item.observation_date && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Calendar size={13} color="var(--text-dim)" />
                          <span>Recorded {new Date(item.observation_date).toLocaleDateString()}</span>
                        </div>
                      )}
                      {isObs && item.latitude && item.longitude && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <MapPin size={13} color="var(--text-dim)" />
                          <span>{item.latitude.toFixed(4)}, {item.longitude.toFixed(4)}</span>
                        </div>
                      )}
                      {!isObs && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-dim)' }}>
                          <Info size={13} />
                          <span>Explored Global Species Record</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Actions Footer */}
                  <div
                    style={{
                      borderTop: '1px solid var(--border-glass)',
                      paddingTop: '10px',
                      display: 'flex',
                      alignItems: 'center',
                      justify: 'space-between'
                    }}
                  >
                    <button
                      type="button"
                      onClick={() => setSelectedDetailItem(item)}
                      className="btn btn-secondary"
                      style={{ padding: '6px 12px', fontSize: '0.78rem', borderRadius: 'var(--radius-sm)' }}
                    >
                      View Details
                    </button>
                    <button
                      type="button"
                      onClick={() => handleRemoveItem(item.id)}
                      disabled={removingItemId === item.id}
                      className="btn btn-secondary"
                      style={{
                        padding: '6px 10px',
                        fontSize: '0.78rem',
                        borderRadius: 'var(--radius-sm)',
                        borderColor: 'rgba(239, 68, 68, 0.3)',
                        color: '#ef4444'
                      }}
                    >
                      <Trash2 size={14} />
                      Remove
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Full Species Profile Dialog Modal */}
      {selectedDetailItem && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            display: 'flex',
            alignItems: 'center',
            justify: 'center',
            padding: '20px',
            background: 'rgba(0,0,0,0.78)',
            backdropFilter: 'blur(8px)'
          }}
          onClick={() => setSelectedDetailItem(null)}
        >
          <div
            className="glass-panel animate-fade-in"
            style={{
              width: '100%',
              maxWidth: '680px',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: '28px',
              borderRadius: 'var(--radius-lg)',
              background: 'var(--bg-card)',
              display: 'flex',
              flexDirection: 'column',
              gap: '20px'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className={`badge badge-${selectedDetailItem.category === 'bird' ? 'bird' : selectedDetailItem.category === 'plant' ? 'plant' : selectedDetailItem.category === 'insect' ? 'insect' : 'unknown'}`}>
                    {selectedDetailItem.category}
                  </span>
                  {selectedDetailItem.item_type === 'observation' ? (
                    <span className="badge" style={{ background: 'var(--color-plant-bg)', color: 'var(--accent-primary)', border: '1px solid var(--border-glass)' }}>
                      YOUR OBSERVATION
                    </span>
                  ) : (
                    <span className="badge" style={{ background: 'var(--bg-tertiary)', color: 'var(--accent-secondary)', border: '1px solid var(--border-glass)' }}>
                      SPECIES REFERENCE
                    </span>
                  )}
                </div>
                <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '6px' }}>
                  {selectedDetailItem.common_name || selectedDetailItem.scientific_name}
                </h2>
                <p style={{ fontSize: '0.92rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                  {selectedDetailItem.scientific_name}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDetailItem(null)}
                className="btn btn-secondary"
                style={{ padding: '8px 16px', fontSize: '0.82rem' }}
              >
                Close
              </button>
            </div>

            {/* Modal Primary Visual Image */}
            <div style={{ width: '100%', height: '240px', borderRadius: 'var(--radius-md)', overflow: 'hidden', background: 'var(--bg-tertiary)', border: '1px solid var(--border-glass)', position: 'relative' }}>
              {selectedDetailItem.observation_image ? (
                <img
                  src={selectedDetailItem.observation_image}
                  alt={selectedDetailItem.common_name || selectedDetailItem.scientific_name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : selectedDetailItem.reference_image || (detailProfile?.reference_images && detailProfile.reference_images.length > 0) ? (
                <img
                  src={selectedDetailItem.reference_image || detailProfile.reference_images[0].url}
                  alt={selectedDetailItem.common_name || selectedDetailItem.scientific_name}
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
              ) : (
                <BiodiversityImagePlaceholder category={selectedDetailItem.category} title={selectedDetailItem.common_name} />
              )}
            </div>

            {/* Observation Details (If User Observation) */}
            {selectedDetailItem.item_type === 'observation' && (
              <div style={{ padding: '14px 16px', background: 'var(--color-plant-bg)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-hover)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-primary)' }}>
                  Field Observation Record
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px', fontSize: '0.82rem' }}>
                  {selectedDetailItem.confidence !== null && (
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>AI Confidence: </span>
                      <strong style={{ color: 'var(--accent-primary)' }}>{(selectedDetailItem.confidence * 100).toFixed(1)}%</strong>
                    </div>
                  )}
                  {selectedDetailItem.observation_date && (
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Recorded Date: </span>
                      <strong style={{ color: 'var(--text-main)' }}>{new Date(selectedDetailItem.observation_date).toLocaleDateString()}</strong>
                    </div>
                  )}
                  {selectedDetailItem.latitude && selectedDetailItem.longitude && (
                    <div>
                      <span style={{ color: 'var(--text-muted)' }}>Coordinates: </span>
                      <strong style={{ color: 'var(--text-main)' }}>{selectedDetailItem.latitude.toFixed(4)}, {selectedDetailItem.longitude.toFixed(4)}</strong>
                    </div>
                  )}
                </div>
                {selectedDetailItem.notes && (
                  <p style={{ fontSize: '0.82rem', color: 'var(--text-main)', marginTop: '4px' }}>
                    <strong>Notes:</strong> {selectedDetailItem.notes}
                  </p>
                )}
              </div>
            )}

            {/* About This Species */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                About This Species
              </h3>
              <p className="editorial-desc">
                {detailProfile?.description || 'Information unavailable'}
              </p>
            </div>

            {/* Quick Facts Grid */}
            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                Quick Facts
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '10px' }}>
                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Habitat</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{detailProfile?.habitat || 'Information unavailable'}</span>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Diet</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{detailProfile?.diet || 'Information unavailable'}</span>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Behavior</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{detailProfile?.behavior || 'Information unavailable'}</span>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Reproduction</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{detailProfile?.reproduction || 'Information unavailable'}</span>
                </div>
                <div style={{ padding: '12px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                  <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Conservation</span>
                  <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{detailProfile?.conservation || 'Information unavailable'}</span>
                </div>
              </div>
            </div>

            {/* Taxonomy Breakdown Flow */}
            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                Taxonomy
              </h3>
              <div className="taxonomy-flow">
                <div className="taxonomy-item"><span>Kingdom:</span> <strong>{detailProfile?.kingdom || 'Information unavailable'}</strong></div>
                <div className="taxonomy-item"><span>Phylum:</span> <strong>{detailProfile?.phylum || 'Information unavailable'}</strong></div>
                <div className="taxonomy-item"><span>Class:</span> <strong>{detailProfile?.class_name || 'Information unavailable'}</strong></div>
                <div className="taxonomy-item"><span>Order:</span> <strong>{detailProfile?.order || 'Information unavailable'}</strong></div>
                <div className="taxonomy-item"><span>Family:</span> <strong>{detailProfile?.family || 'Information unavailable'}</strong></div>
                <div className="taxonomy-item"><span>Genus:</span> <strong>{detailProfile?.genus || 'Information unavailable'}</strong></div>
                <div className="taxonomy-item" style={{ borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}>
                  <span>Species:</span> <strong style={{ fontStyle: 'italic' }}>{selectedDetailItem.scientific_name}</strong>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
