import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Camera, Search, FileText, Settings, X } from 'lucide-react';

export default function Sidebar({ isMobileOpen, onCloseMobileMenu }) {
  const location = useLocation();

  const navItems = [
    { label: 'Dashboard', path: '/', icon: LayoutDashboard },
    { label: 'Observe', path: '/observe', icon: Camera },
    { label: 'Species Explorer', path: '/species', icon: Search },
    { label: 'Reports & Export', path: '/reports', icon: FileText },
    { label: 'Settings', path: '/settings', icon: Settings },
  ];

  const renderNavLinks = () => (
    <>
      <div style={{ padding: '0 12px 12px 12px', fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
        Navigation
      </div>
      {navItems.map((item) => {
        const Icon = item.icon;
        const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
        return (
          <Link
            key={item.path}
            to={item.path}
            onClick={onCloseMobileMenu}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '10px 14px',
              borderRadius: 'var(--radius-md)',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? 'var(--accent-primary)' : 'var(--text-muted)',
              background: isActive ? 'var(--color-plant-bg)' : 'transparent',
              borderLeft: isActive ? '3px solid var(--accent-primary)' : '3px solid transparent',
              transition: 'var(--transition-fast)'
            }}
          >
            <Icon size={18} color={isActive ? 'var(--accent-primary)' : 'var(--text-muted)'} />
            <span>{item.label}</span>
          </Link>
        );
      })}
    </>
  );

  return (
    <>
      {/* Desktop Permanent Sidebar */}
      <aside className="desktop-sidebar" style={{
        width: '240px',
        flexShrink: 0,
        borderRight: '1px solid var(--border-glass)',
        background: 'var(--bg-secondary)',
        padding: '20px 12px',
        display: 'flex',
        flexDirection: 'column',
        gap: '6px'
      }}>
        {renderNavLinks()}
      </aside>

      {/* Mobile Drawer Overlay */}
      <div
        className={`sidebar-overlay ${isMobileOpen ? 'open' : ''}`}
        onClick={onCloseMobileMenu}
      />

      {/* Mobile Drawer Container */}
      <aside className={`sidebar-drawer ${isMobileOpen ? 'open' : ''}`} style={{ padding: '20px 16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', paddingBottom: '12px', borderBottom: '1px solid var(--border-glass)' }}>
          <span style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--text-main)' }}>
            Green<span style={{ color: 'var(--accent-primary)' }}>Lens</span> Menu
          </span>
          <button
            onClick={onCloseMobileMenu}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {renderNavLinks()}
        </div>
      </aside>
    </>
  );
}

