import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getSpeciesDetail } from '../services/api';
import { CategoryBadge } from '../components/common/Badge';
import { ArrowLeft, BookOpen, MapPin, Calendar, ExternalLink } from 'lucide-react';

export default function SpeciesDetail() {
  const { id } = useParams();
  const [species, setSpecies] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSpeciesDetail(id)
      .then(setSpecies)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div style={{ padding: '40px', color: 'var(--text-muted)' }}>Loading species profile...</div>;
  if (!species) return <div style={{ padding: '40px', color: '#f87171' }}>Species record not found.</div>;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '900px', margin: '0 auto' }}>
      <div>
        <Link to="/species" style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', marginBottom: '12px' }}>
          <ArrowLeft size={16} /> Back to Species Explorer
        </Link>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ fontSize: '2.2rem', fontWeight: 800 }}>{species.common_name || species.scientific_name}</h1>
            <div style={{ fontSize: '1.1rem', fontStyle: 'italic', color: 'var(--accent-primary)' }}>
              {species.scientific_name}
            </div>
          </div>
          <CategoryBadge category={species.category} />
        </div>
      </div>

      {/* Overview Stat Box */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
        <div className="glass-panel" style={{ padding: '20px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Campus Observations</span>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#fff', marginTop: '4px' }}>
            {species.observation_count}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Taxonomic Rank</span>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent-secondary)', marginTop: '8px' }}>
            Species
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '20px', textAlign: 'center' }}>
          <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: 'var(--text-muted)' }}>Taxonomy Source</span>
          <div style={{ fontSize: '1rem', fontWeight: 600, color: '#fff', marginTop: '8px' }}>
            GBIF Backbone
          </div>
        </div>
      </div>

      {/* Taxonomy Breakdown */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BookOpen size={20} color="var(--accent-primary)" /> Taxonomic Hierarchy
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '0.9rem' }}>
          <div style={{ padding: '10px', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>KINGDOM</span>
            <div style={{ fontWeight: 600 }}>{species.kingdom || 'Plantae / Animalia'}</div>
          </div>
          <div style={{ padding: '10px', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>FAMILY</span>
            <div style={{ fontWeight: 600 }}>{species.family || 'Unclassified'}</div>
          </div>
          <div style={{ padding: '10px', background: 'var(--bg-tertiary)', borderRadius: '6px' }}>
            <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>GENUS</span>
            <div style={{ fontWeight: 600 }}>{species.genus || 'Unclassified'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
