import React from 'react';
import { Feather, Leaf, Bug, TreePine, Compass } from 'lucide-react';

export default function BiodiversityImagePlaceholder({ category = 'other', title = '', className = '', style = {} }) {
  const cat = (category || 'other').toLowerCase();

  const getCategoryIcon = () => {
    if (cat.includes('bird')) {
      return <Feather size={32} style={{ color: 'var(--color-bird, #3b82f6)' }} />;
    }
    if (cat.includes('plant') || cat.includes('flower')) {
      return <Leaf size={32} style={{ color: 'var(--color-plant, #10b981)' }} />;
    }
    if (cat.includes('tree')) {
      return <TreePine size={32} style={{ color: 'var(--color-plant, #10b981)' }} />;
    }
    if (cat.includes('insect') || cat.includes('bug')) {
      return <Bug size={32} style={{ color: 'var(--color-insect, #f59e0b)' }} />;
    }
    return <Compass size={32} style={{ color: 'var(--accent-primary, #10b981)' }} />;
  };

  const getBadgeClass = () => {
    if (cat.includes('bird')) return 'badge-bird';
    if (cat.includes('plant') || cat.includes('flower') || cat.includes('tree')) return 'badge-plant';
    if (cat.includes('insect') || cat.includes('bug')) return 'badge-insect';
    return 'badge-unknown';
  };

  return (
    <div
      className={`w-full h-full flex flex-col items-center justify-center p-4 text-center select-none ${className}`}
      style={{
        background: 'var(--bg-tertiary)',
        border: '1px solid var(--border-glass)',
        aspectRatio: '16 / 10',
        width: '100%',
        height: '100%',
        boxSizing: 'border-box',
        ...style
      }}
    >
      <div
        style={{
          width: '48px',
          height: '48px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--bg-secondary)',
          border: '1px solid var(--border-glass)',
          display: 'flex',
          alignItems: 'center',
          justify: 'center',
          marginBottom: '8px'
        }}
      >
        {getCategoryIcon()}
      </div>
      <span className={`badge ${getBadgeClass()}`} style={{ fontSize: '0.7rem', padding: '2px 9px' }}>
        {category.toUpperCase()}
      </span>
      {title && (
        <span
          style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            marginTop: '6px',
            maxWidth: '90%',
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis'
          }}
        >
          {title}
        </span>
      )}
    </div>
  );
}
