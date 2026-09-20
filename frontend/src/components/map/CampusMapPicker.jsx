import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon, useMapEvents } from 'leaflet';
import L from 'leaflet';

// Fix Leaflet marker icon URLs
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Default campus boundary coordinates
const DEFAULT_POLYGON = [
  [12.9700, 77.5850],
  [12.9700, 77.5950],
  [12.9780, 77.5950],
  [12.9780, 77.5850],
];

function LocationMarker({ position, setPosition }) {
  useMapEvents({
    click(e) {
      setPosition([e.latlng.lat, e.latlng.lng]);
    },
  });

  return position === null ? null : (
    <Marker position={position}>
      <Popup>Selected Observation Coordinates</Popup>
    </Marker>
  );
}

export default function CampusMapPicker({ latitude, longitude, onChangeLocation, style }) {
  const [position, setPosition] = useState(
    latitude && longitude ? [latitude, longitude] : [12.9740, 77.5900]
  );

  useEffect(() => {
    if (latitude && longitude) {
      setPosition([latitude, longitude]);
    }
  }, [latitude, longitude]);

  const handleSetPosition = (pos) => {
    setPosition(pos);
    if (onChangeLocation) {
      onChangeLocation(pos[0], pos[1]);
    }
  };

  return (
    <div style={{ height: '300px', width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-glass)', ...style }}>
      <MapContainer center={position} zoom={15} style={{ height: '100%', width: '100%' }}>
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <Polygon positions={DEFAULT_POLYGON} pathOptions={{ color: '#10b981', weight: 2, fillOpacity: 0.1 }} />
        <LocationMarker position={position} setPosition={handleSetPosition} />
      </MapContainer>
    </div>
  );
}
