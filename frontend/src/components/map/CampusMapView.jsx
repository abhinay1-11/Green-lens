import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon } from 'leaflet';
import L from 'leaflet';
import { CategoryBadge, VerificationBadge } from '../common/Badge';

const DEFAULT_POLYGON = [
  [12.9700, 77.5850],
  [12.9700, 77.5950],
  [12.9780, 77.5950],
  [12.9780, 77.5850],
];

// Create custom colored emoji markers for species categories
const createCustomIcon = (category) => {
  const cat = (category || '').toLowerCase();
  let emoji = '🌱';
  let color = '#10b981';

  if (cat === 'bird') { emoji = '🐦'; color = '#3b82f6'; }
  else if (cat === 'insect') { emoji = '🐛'; color = '#f59e0b'; }
  else if (cat === 'unknown') { emoji = '❓'; color = '#8b5cf6'; }

  return L.divIcon({
    className: 'custom-leaflet-marker',
    html: `<div style="
      background: ${color};
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 0 12px ${color};
      border: 2px solid white;
      font-size: 16px;
    ">${emoji}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16],
    popupAnchor: [0, -16]
  });
};

export default function CampusMapView({ observations = [] }) {
  const defaultCenter = [12.9740, 77.5900];

  return (
    <div style={{ height: '600px', width: '100%', borderRadius: 'var(--radius-lg)', overflow: 'hidden', border: '1px solid var(--border-glass)', boxShadow: 'var(--shadow-lg)' }}>
      <MapContainer center={defaultCenter} zoom={15} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Campus Boundary Overlay */}
        <Polygon
          positions={DEFAULT_POLYGON}
          pathOptions={{ color: '#10b981', weight: 2.5, dashArray: '6, 6', fillOpacity: 0.12 }}
        />

        {/* Observation Markers */}
        {observations.map((obs) => {
          const lat = obs.geometry?.coordinates[1] || obs.latitude;
          const lon = obs.geometry?.coordinates[0] || obs.longitude;
          const props = obs.properties || obs;

          if (!lat || !lon) return null;

          return (
            <Marker
              key={props.id}
              position={[lat, lon]}
              icon={createCustomIcon(props.category)}
            >
              <Popup>
                <div style={{ padding: '6px', minWidth: '180px' }}>
                  {props.image_url && (
                    <img
                      src={props.image_url}
                      alt={props.scientific_name}
                      style={{ width: '100%', height: '100px', objectFit: 'cover', borderRadius: '6px', marginBottom: '8px' }}
                    />
                  )}
                  <div style={{ display: 'flex', gap: '6px', marginBottom: '4px' }}>
                    <CategoryBadge category={props.category} />
                    <VerificationBadge status={props.verification_status} />
                  </div>
                  <h4 style={{ margin: '4px 0 2px 0', fontSize: '1rem', color: '#111827' }}>
                    {props.common_name || props.scientific_name}
                  </h4>
                  <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: '#4b5563', marginBottom: '6px' }}>
                    {props.scientific_name}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#6b7280', borderTop: '1px solid #e5e7eb', paddingTop: '4px' }}>
                    📍 Zone: <strong>{props.campus_zone || 'General Campus'}</strong><br/>
                    🤖 AI Confidence: <strong>{props.confidence ? `${Math.round(props.confidence * 100)}%` : 'N/A'}</strong><br/>
                    🗓 Date: {props.observation_date}
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
    </div>
  );
}
