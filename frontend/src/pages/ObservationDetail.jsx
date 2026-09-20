import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getObservationById, updateObservation } from '../services/api';
import { CategoryBadge, VerificationBadge } from '../components/common/Badge';
import { ArrowLeft, CheckCircle, Edit2, MapPin, Calendar, ShieldCheck, AlertCircle } from 'lucide-react';

export default function ObservationDetail() {
  const { id } = useParams();
  const [obs, setObs] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getObservationById(id)
      .then(setObs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  const handleUpdateStatus = async (newStatus) => {
    try {
      const updated = await updateObservation(id, { verification_status: newStatus });
      setObs(updated);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading observation...</div>;
  if (!obs) return <div style={{ padding: '40px', color: '#f87171' }}>Observation not found.</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <div>
        <Link to="/map" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', marginBottom: '12px' }}>
          <ArrowLeft size={16} /> Back to Campus Map
        </Link>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '2rem', fontWeight: 800 }}>{obs.common_name || obs.scientific_name}</h1>
            <div style={{ fontSize: '1rem', fontStyle: 'italic', color: 'var(--accent-primary)' }}>
              {obs.scientific_name}
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <CategoryBadge category={obs.category} />
            <VerificationBadge status={obs.verification_status} />
          </div>
        </div>
      </div>

      {/* Images Gallery */}
      {obs.images && obs.images.length > 0 && (
        <div className="glass-panel" style={{ padding: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '12px' }}>
            {obs.images.map((img) => (
              <img
                key={img.id}
                src={img.file_path}
                alt={obs.scientific_name}
                style={{ width: '100%', height: '180px', objectFit: 'cover', borderRadius: 'var(--radius-sm)' }}
              />
            ))}
          </div>
        </div>
      )}

      {/* Details Box */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Observation Details</h3>
          
          <div style={{ fontSize: '0.9rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div><strong>Zone:</strong> {obs.campus_zone || 'General Campus'}</div>
            <div><strong>Recorded Date:</strong> {new Date(obs.observation_date).toLocaleString()}</div>
            <div><strong>Coordinates:</strong> {obs.latitude?.toFixed(4)}, {obs.longitude?.toFixed(4)}</div>
            <div><strong>Notes:</strong> {obs.notes || 'No observation notes recorded.'}</div>
          </div>

          <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px' }}>
            <h4 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '10px' }}>Verification Controls</h4>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-primary" style={{ fontSize: '0.8rem' }} onClick={() => handleUpdateStatus('user_confirmed')}>
                Confirm Species
              </button>
              <button className="btn btn-secondary" style={{ fontSize: '0.8rem' }} onClick={() => handleUpdateStatus('user_corrected')}>
                Mark Corrected
              </button>
            </div>
          </div>
        </div>

        {/* AI Audit History Card */}
        <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <h4 style={{ fontSize: '1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={18} color="var(--accent-primary)" /> AI Audit History
          </h4>

          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Provider: <strong>{obs.ai_provider || 'Mock'}</strong><br/>
            Top Model Score: <strong>{obs.ai_confidence ? `${Math.round(obs.ai_confidence * 100)}%` : 'N/A'}</strong>
          </div>

          {obs.identification_results && obs.identification_results.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.8rem' }}>
              <div style={{ textTransform: 'uppercase', fontSize: '0.7rem', color: 'var(--text-dim)', fontWeight: 700 }}>
                Predictions History
              </div>
              {obs.identification_results.map((res) => (
                <div key={res.id} style={{ padding: '6px', background: 'var(--bg-tertiary)', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }}>
                  <span>#{res.rank} {res.common_name || res.scientific_name}</span>
                  <strong>{Math.round(res.confidence * 100)}%</strong>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
