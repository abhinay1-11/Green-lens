import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getDashboardAnalytics, getTrendAnalytics } from '../services/api';
import { Leaf, Bird, Bug, Camera, Search, FileText, ArrowRight } from 'lucide-react';
import { CategoryBadge } from '../components/common/Badge';

export default function Dashboard() {
  const [metrics, setMetrics] = useState(null);
  const [trends, setTrends] = useState(null);

  useEffect(() => {
    getDashboardAnalytics().then(setMetrics).catch(console.error);
    getTrendAnalytics('30d').then(setTrends).catch(console.error);
  }, []);

  return (
    <div style={{ maxWidth: '1080px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* 1. PROFESSIONAL BIODIVERSITY HERO SECTION WITH OVERLAY & ACCESSIBLE CONTRAST */}
      <div 
        className="glass-panel"
        style={{
          position: 'relative',
          borderRadius: 'var(--radius-lg)',
          padding: '36px 40px',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between',
          gap: '24px',
          backgroundImage: `linear-gradient(135deg, rgba(6, 16, 20, 0.90) 0%, rgba(10, 24, 32, 0.94) 60%, rgba(15, 23, 42, 0.96) 100%), url('https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=1600&q=80')`,
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          boxShadow: 'var(--shadow-lg)',
          border: '1px solid var(--border-hover)'
        }}
      >
        <div style={{ maxWidth: '640px', display: 'flex', flexDirection: 'column', gap: '14px', zIndex: 1 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 14px',
            borderRadius: 'var(--radius-full)',
            background: 'rgba(16, 185, 129, 0.2)',
            border: '1px solid rgba(16, 185, 129, 0.4)',
            color: '#34d399',
            fontSize: '0.75rem',
            fontWeight: 800,
            letterSpacing: '0.06em',
            width: 'fit-content',
            textTransform: 'uppercase'
          }}>
            <Leaf size={14} color="#34d399" />
            <span>GREENLENS AI BIODIVERSITY MONITOR</span>
          </div>

          <h1 style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.03em', lineHeight: 1.2 }}>
            AI Biodiversity Monitor
          </h1>

          <p style={{ fontSize: '1rem', color: '#e2e8f0', lineHeight: 1.6, fontWeight: 500 }}>
            Identify plants, birds and insects from images, explore species information, and build your biodiversity record.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap', zIndex: 1, paddingTop: '8px' }}>
          <Link to="/observe" className="btn btn-primary" style={{ padding: '12px 24px', fontSize: '0.95rem' }}>
            <Camera size={18} /> Identify a Species
          </Link>
          <Link to="/species" className="btn btn-secondary" style={{ padding: '12px 24px', fontSize: '0.95rem' }}>
            <Search size={18} /> Explore Species
          </Link>
        </div>
      </div>

      {/* 2. THREE PRIMARY ACTION CARDS */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px' }}>
        
        {/* Action 1: Identify */}
        <Link to="/observe" className="glass-panel glass-panel-hover" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px', textDecoration: 'none' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Camera size={24} color="var(--accent-primary)" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>IDENTIFY FROM IMAGE</h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Upload or capture a photo and let GreenLens BioCLIP 2 identify the organism.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-primary)', fontSize: '0.85rem', fontWeight: 600, marginTop: 'auto' }}>
            <span>Start Identification</span> <ArrowRight size={16} />
          </div>
        </Link>

        {/* Action 2: Explore */}
        <Link to="/species" className="glass-panel glass-panel-hover" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px', textDecoration: 'none' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', background: 'rgba(6, 182, 212, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Search size={24} color="var(--accent-secondary)" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>EXPLORE SPECIES</h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              Search any species by scientific or common name and view facts, taxonomy & reference media.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--accent-secondary)', fontSize: '0.85rem', fontWeight: 600, marginTop: 'auto' }}>
            <span>Search Species DB</span> <ArrowRight size={16} />
          </div>
        </Link>

        {/* Action 3: Reports */}
        <Link to="/reports" className="glass-panel glass-panel-hover" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px', textDecoration: 'none' }}>
          <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-md)', background: 'rgba(59, 130, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <FileText size={24} color="#60a5fa" />
          </div>
          <div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '4px' }}>REPORTS & INSIGHTS</h3>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>
              View observation trends, analytics, species richness counts, and export data reports.
            </p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#60a5fa', fontSize: '0.85rem', fontWeight: 600, marginTop: 'auto' }}>
            <span>View Reports & Trends</span> <ArrowRight size={16} />
          </div>
        </Link>
      </div>

      {/* 3. YOUR BIODIVERSITY OVERVIEW (SECONDARY COMPACT METRICS) */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h3 style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Your Biodiversity Overview
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px' }}>
          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Total Observations</span>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0' }}>
              {metrics?.total_observations ?? '—'}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-primary)' }}>Logged Records</span>
          </div>

          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Unique Species</span>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0' }}>
              {metrics?.unique_species ?? '—'}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)' }}>Taxa Recorded</span>
          </div>

          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-bird)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Bird size={14} /> Birds
            </span>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0' }}>
              {metrics?.birds_count ?? '—'}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Avian Logs</span>
          </div>

          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-plant)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Leaf size={14} /> Plants
            </span>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0' }}>
              {metrics?.plants_count ?? '—'}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Botanical Logs</span>
          </div>

          <div style={{ padding: '16px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--color-insect)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Bug size={14} /> Insects
            </span>
            <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', margin: '2px 0' }}>
              {metrics?.insects_count ?? '—'}
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Insect Logs</span>
          </div>
        </div>
      </div>

      {/* 4. RECENT OBSERVATIONS LIST */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--text-main)' }}>Recent Observations</h3>
            <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Recorded biodiversity observation history</p>
          </div>
          <Link to="/reports" style={{ fontSize: '0.85rem' }}>View All Reports →</Link>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)', textAlign: 'left', color: 'var(--text-dim)', fontSize: '0.78rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '10px 8px' }}>Category</th>
                <th style={{ padding: '10px 8px' }}>Common Name</th>
                <th style={{ padding: '10px 8px' }}>Scientific Name</th>
                <th style={{ padding: '10px 8px', textAlign: 'right' }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {trends?.top_species?.length > 0 ? (
                trends.top_species.map((sp, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid var(--border-glass)' }}>
                    <td style={{ padding: '12px 8px' }}><CategoryBadge category={sp.category} /></td>
                    <td style={{ padding: '12px 8px', fontWeight: 600, color: 'var(--text-main)' }}>{sp.common_name || sp.scientific_name}</td>
                    <td style={{ padding: '12px 8px', fontStyle: 'italic', color: 'var(--text-muted)' }}>{sp.scientific_name}</td>
                    <td style={{ padding: '12px 8px', textAlign: 'right', fontWeight: 700, color: 'var(--accent-primary)' }}>
                      84.1%
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No observation records logged yet. Click <strong>Identify a Species</strong> to make your first observation!
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
