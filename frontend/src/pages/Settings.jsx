import React, { useEffect, useState } from 'react';
import { getProviderStatus } from '../services/api';
import { ShieldCheck, Sun, Moon, Laptop, Globe } from 'lucide-react';
import { applyTheme, getThemePreference } from '../utils/theme';

export default function Settings() {
  const [status, setStatus] = useState(null);
  const [themeMode, setThemeMode] = useState(() => getThemePreference());

  useEffect(() => {
    getProviderStatus().then(setStatus).catch(console.error);
  }, []);

  const handleSelectTheme = (mode) => {
    setThemeMode(mode);
    applyTheme(mode);
  };

  return (
    <div style={{ maxWidth: '840px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px', padding: '0 8px' }}>
      
      {/* Title */}
      <div>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800 }}>Settings</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '4px' }}>
          View GreenLens AI engines, appearance preferences, and application configuration.
        </p>
      </div>

      {/* 1. APPEARANCE (THEME SELECTOR) */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sun size={20} color="var(--accent-primary)" /> Appearance
          </h3>
          <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', marginTop: '4px' }}>
            Choose how GreenLens looks across all devices and observation tools.
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
          <button
            onClick={() => handleSelectTheme('dark')}
            className="btn"
            style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: themeMode === 'dark' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
              color: themeMode === 'dark' ? '#ffffff' : 'var(--text-main)',
              border: '1px solid var(--border-glass)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <Moon size={22} color={themeMode === 'dark' ? '#ffffff' : 'var(--text-muted)'} />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Dark</span>
          </button>

          <button
            onClick={() => handleSelectTheme('light')}
            className="btn"
            style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: themeMode === 'light' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
              color: themeMode === 'light' ? '#ffffff' : 'var(--text-main)',
              border: '1px solid var(--border-glass)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <Sun size={22} color={themeMode === 'light' ? '#ffffff' : 'var(--text-muted)'} />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>Light</span>
          </button>

          <button
            onClick={() => handleSelectTheme('system')}
            className="btn"
            style={{
              padding: '16px',
              borderRadius: 'var(--radius-md)',
              background: themeMode === 'system' ? 'var(--accent-primary)' : 'var(--bg-tertiary)',
              color: themeMode === 'system' ? '#ffffff' : 'var(--text-main)',
              border: '1px solid var(--border-glass)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            <Laptop size={22} color={themeMode === 'system' ? '#ffffff' : 'var(--text-muted)'} />
            <span style={{ fontWeight: 700, fontSize: '0.95rem' }}>System</span>
          </button>
        </div>
      </div>

      {/* 2. IDENTIFICATION ENGINES STATUS */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <ShieldCheck size={20} color="var(--accent-primary)" /> Identification Engines
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {/* Bird Engine */}
          <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ color: 'var(--text-main)', fontSize: '1rem' }}>Bird Identification Engine</strong>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                BioCLIP 2 (<code>imageomics/bioclip-2</code>)
              </div>
            </div>
            <span className="badge badge-confirmed">Status: Active</span>
          </div>

          {/* Plant Engine */}
          <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ color: 'var(--text-main)', fontSize: '1rem' }}>Plant Identification Engine</strong>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {status?.plant?.provider === 'plantnet' ? 'Pl@ntNet API v2 + Biodiversity Fallback' : 'Pl@ntNet API'}
              </div>
            </div>
            <span className="badge badge-confirmed">Status: Active</span>
          </div>

          {/* Insect Engine */}
          <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <strong style={{ color: 'var(--text-main)', fontSize: '1rem' }}>Insect Identification Engine</strong>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Insecta Vision AI Engine
              </div>
            </div>
            <span className="badge badge-confirmed">Status: Active</span>
          </div>
        </div>
      </div>

      {/* 3. DATA & ATTRIBUTION */}
      <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Globe size={20} color="var(--accent-secondary)" /> Data & Attribution
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', lineHeight: 1.6 }}>
          Species profiles, factual summaries, taxonomic breakdown, and reference media displayed across GreenLens are retrieved dynamically from open biodiversity APIs including <strong>GBIF (Global Biodiversity Information Facility)</strong> and <strong>Wikipedia / Wikimedia Commons</strong>. Original creator rights and Creative Commons licensing terms are preserved on all reference images.
        </p>
      </div>

      {/* 4. ABOUT GREENLENS */}
      <div className="glass-panel" style={{ padding: '24px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        <div>
          <strong>GreenLens Biodiversity Monitor</strong> v2.0.0
        </div>
        <div>
          AI Models: BioCLIP 2, Pl@ntNet API, Insecta Vision
        </div>
      </div>

    </div>
  );
}
