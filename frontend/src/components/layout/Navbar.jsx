import React from 'react';
import { Leaf, PlusCircle, ShieldCheck, Activity } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar({ providerStatus }) {
  const location = useLocation();

  return (
    <header style={{
      height: '64px',
      borderBottom: '1px solid var(--border-glass)',
      background: 'var(--bg-glass)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 1000,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '0 24px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <div style={{
            width: '38px',
            height: '38px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #10b981 0%, #06b6d4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 15px rgba(16, 185, 129, 0.4)'
          }}>
            <Leaf size={22} color="#ffffff" />
          </div>
          <div>
            <span style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.03em' }}>
              Green<span style={{ color: 'var(--accent-primary)' }}>Lens</span>
            </span>
            <span style={{
              fontSize: '0.65rem',
              display: 'block',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              marginTop: '-4px'
            }}>
              AI Biodiversity Monitor
            </span>
          </div>
        </Link>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <Link
          to="/observe"
          state={{ reset: Date.now() }}
          className="btn btn-primary"
        >
          <PlusCircle size={18} />
          <span>New Observation</span>
        </Link>
      </div>
    </header>
  );
}
