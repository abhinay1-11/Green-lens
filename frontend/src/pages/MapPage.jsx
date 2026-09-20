import React, { useEffect, useState } from 'react';
import { getMapObservations } from '../services/api';
import CampusMapView from '../components/map/CampusMapView';
import { Filter, RefreshCw } from 'lucide-react';

export default function MapPage() {
  const [observations, setObservations] = useState([]);
  const [category, setCategory] = useState('all');
  const [campusZone, setCampusZone] = useState('all');
  const [verificationStatus, setVerificationStatus] = useState('all');
  const [loading, setLoading] = useState(false);

  const fetchMapData = async () => {
    setLoading(true);
    try {
      const data = await getMapObservations({
        category,
        campus_zone: campusZone,
        verification_status: verificationStatus
      });
      setObservations(data.features || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMapData();
  }, [category, campusZone, verificationStatus]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Campus Biodiversity Map</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
            Interactive spatial mapping of campus species observations with GeoJSON boundary validation
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel" style={{ padding: '16px 20px', display: 'flex', gap: '16px', alignItems: 'center', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--accent-primary)', fontWeight: 600, fontSize: '0.9rem' }}>
          <Filter size={18} /> Filters:
        </div>

        {/* Category Filter */}
        <select
          value={category}
          onChange={(e) => setCategory(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-tertiary)',
            color: '#fff',
            border: '1px solid var(--border-glass)'
          }}
        >
          <option value="all">Category: All</option>
          <option value="plant">Plants 🌱</option>
          <option value="bird">Birds 🐦</option>
          <option value="insect">Insects 🐛</option>
          <option value="unknown">Unknown ❓</option>
        </select>

        {/* Campus Zone Filter */}
        <select
          value={campusZone}
          onChange={(e) => setCampusZone(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-tertiary)',
            color: '#fff',
            border: '1px solid var(--border-glass)'
          }}
        >
          <option value="all">Zone: All Campus</option>
          <option value="botanical_garden">Botanical Garden</option>
          <option value="academic_block">Academic Block</option>
          <option value="library_quad">Library Quad</option>
          <option value="hostel_grounds">Hostel Grounds</option>
          <option value="lake_pond">Campus Lake & Wetlands</option>
          <option value="sports_ground">Sports Ground</option>
        </select>

        {/* Verification Status Filter */}
        <select
          value={verificationStatus}
          onChange={(e) => setVerificationStatus(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: 'var(--radius-sm)',
            background: 'var(--bg-tertiary)',
            color: '#fff',
            border: '1px solid var(--border-glass)'
          }}
        >
          <option value="all">Status: All</option>
          <option value="user_confirmed">User Confirmed</option>
          <option value="user_corrected">User Corrected</option>
          <option value="ai_suggested">AI Suggested</option>
          <option value="pending">Pending</option>
        </select>

        <button className="btn btn-secondary" style={{ padding: '8px 12px', fontSize: '0.85rem' }} onClick={fetchMapData}>
          <RefreshCw size={14} /> Refresh
        </button>

        <div style={{ marginLeft: 'auto', fontSize: '0.85rem', color: 'var(--text-muted)' }}>
          Showing <strong>{observations.length}</strong> markers
        </div>
      </div>

      {/* Map View */}
      <CampusMapView observations={observations} />
    </div>
  );
}
