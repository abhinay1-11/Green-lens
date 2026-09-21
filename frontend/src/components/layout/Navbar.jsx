import React from 'react';
import { PlusCircle, Menu, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Navbar({ providerStatus, onToggleMobileMenu, isMobileOpen }) {
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
      padding: '0 16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <button
          onClick={onToggleMobileMenu}
          className="mobile-nav-btn"
          aria-label="Toggle navigation menu"
        >
          {isMobileOpen ? <X size={22} /> : <Menu size={22} />}
        </button>

        <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: '10px', textDecoration: 'none' }}>
          <img
            src="/logo.png"
            alt="GreenLens Logo"
            style={{
              width: '36px',
              height: '36px',
              objectFit: 'contain',
              filter: 'drop-shadow(0 0 8px rgba(16, 185, 129, 0.4))'
            }}
          />
          <div>
            <span style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.03em' }}>
              Green<span style={{ color: 'var(--accent-primary)' }}>Lens</span>
            </span>
            <span style={{
              fontSize: '0.62rem',
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

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <Link
          to="/observe"
          state={{ reset: Date.now() }}
          className="btn btn-primary"
          style={{ padding: '8px 14px', fontSize: '0.85rem' }}
        >
          <PlusCircle size={16} />
          <span className="hide-on-mobile">New Observation</span>
        </Link>
      </div>
    </header>
  );
}

