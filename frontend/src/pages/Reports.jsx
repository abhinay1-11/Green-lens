import React, { useState } from 'react';
import { getExportCsvUrl, getExportPdfUrl } from '../services/api';
import { Download, FileSpreadsheet, FileText, CheckCircle2, TrendingUp, BarChart2, PieChart as PieIcon } from 'lucide-react';
import Trends from './Trends';

export default function Reports() {
  const [activeTab, setActiveTab] = useState('exports');
  const csvUrl = getExportCsvUrl();
  const pdfUrl = getExportPdfUrl();

  return (
    <div style={{ maxWidth: '1040px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px', padding: '0 8px' }}>
      
      {/* Page Title & Subtitle */}
      <div>
        <h1 style={{ fontSize: '2.2rem', fontWeight: 800 }}>Reports & Export</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '4px' }}>
          Historical observations, species activity analytics, and downloadable biodiversity reports.
        </p>
      </div>

      {/* Tabs */}
      <div className="glass-panel" style={{ padding: '6px', display: 'flex', gap: '8px', width: 'fit-content' }}>
        <button
          onClick={() => setActiveTab('exports')}
          className="btn"
          style={{
            padding: '8px 18px',
            fontSize: '0.9rem',
            background: activeTab === 'exports' ? 'var(--accent-primary)' : 'transparent',
            color: activeTab === 'exports' ? '#ffffff' : 'var(--text-muted)'
          }}
        >
          Overview & Exports
        </button>
        <button
          onClick={() => setActiveTab('trends')}
          className="btn"
          style={{
            padding: '8px 18px',
            fontSize: '0.9rem',
            background: activeTab === 'trends' ? 'var(--accent-primary)' : 'transparent',
            color: activeTab === 'trends' ? '#ffffff' : 'var(--text-muted)'
          }}
        >
          Trends & Analytics
        </button>
      </div>

      {activeTab === 'exports' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
            {/* CSV Export Box */}
            <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: 'var(--radius-md)', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FileSpreadsheet size={30} color="var(--accent-primary)" />
              </div>

              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>CSV Raw Data Export</h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '6px', lineHeight: 1.5 }}>
                  Full spreadsheet export containing Observation ID, Date, Species, AI Confidence, GPS Coordinates, Campus Zone, and Notes.
                </p>
              </div>

              <a href={csvUrl} download className="btn btn-primary" style={{ marginTop: 'auto', padding: '12px' }}>
                <Download size={18} /> Download CSV Dump
              </a>
            </div>

            {/* PDF / HTML Printable Report Box */}
            <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
              <div style={{ width: '52px', height: '52px', borderRadius: 'var(--radius-md)', background: 'rgba(59, 130, 246, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <FileText size={30} color="#60a5fa" />
              </div>

              <div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Printable Audit Report (PDF)</h3>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '6px', lineHeight: 1.5 }}>
                  Formatted PDF report document complete with executive summary, category breakdown metrics, and observation log table.
                </p>
              </div>

              <a href={pdfUrl} target="_blank" rel="noopener noreferrer" className="btn btn-secondary" style={{ marginTop: 'auto', padding: '12px' }}>
                <Download size={18} /> View Printable PDF Report
              </a>
            </div>
          </div>

          {/* Compliance Box */}
          <div className="glass-panel" style={{ padding: '20px 24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <CheckCircle2 size={24} color="var(--accent-primary)" />
            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              <strong>Data Governance:</strong> All exported reports preserve original AI prediction confidence scores alongside human verification audit trails.
            </div>
          </div>
        </div>
      ) : (
        <Trends />
      )}

    </div>
  );
}
