import React, { useState } from 'react';
import { BookOpen, Edit3, Trash2, ChevronRight, Calendar } from 'lucide-react';
import BiodiversityImagePlaceholder from './BiodiversityImagePlaceholder';

export default function CollectionCard({ collection, onOpen, onEdit, onDelete }) {
  const [imageError, setImageError] = useState(false);

  if (!collection) return null;

  const speciesCount = collection.species_count || 0;
  const obsCount = collection.observation_count || 0;
  const updatedDate = collection.updated_at
    ? new Date(collection.updated_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
    : 'Recently';

  const coverUrl = collection.cover_image_url;

  return (
    <div
      onClick={() => onOpen(collection)}
      className="glass-panel glass-panel-hover"
      style={{
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        justify: 'space-between',
        overflow: 'hidden',
        position: 'relative',
        borderRadius: 'var(--radius-md)',
        background: 'var(--bg-card)',
        border: '1px solid var(--border-glass)'
      }}
    >
      {/* 1. Fixed 16:10 Aspect Ratio Cover Container */}
      <div
        style={{
          width: '100%',
          aspectRatio: '16 / 10',
          position: 'relative',
          overflow: 'hidden',
          background: 'var(--bg-tertiary)',
          borderBottom: '1px solid var(--border-glass)'
        }}
      >
        {coverUrl && !imageError ? (
          <img
            src={coverUrl}
            alt={collection.name}
            onError={() => setImageError(true)}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              transition: 'var(--transition-smooth)'
            }}
          />
        ) : (
          <BiodiversityImagePlaceholder category="collection" title={collection.name} />
        )}

        {/* Floating Top Badge: Species & Observations summary */}
        <div
          style={{
            position: 'absolute',
            top: '10px',
            right: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px'
          }}
        >
          <span
            className="badge badge-plant"
            style={{
              background: 'rgba(16, 185, 129, 0.9)',
              color: '#ffffff',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
              fontSize: '0.7rem',
              padding: '3px 10px'
            }}
          >
            {speciesCount} {speciesCount === 1 ? 'species' : 'species'}
          </span>
          <span
            className="badge badge-bird"
            style={{
              background: 'rgba(59, 130, 246, 0.9)',
              color: '#ffffff',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.3)',
              fontSize: '0.7rem',
              padding: '3px 10px'
            }}
          >
            {obsCount} {obsCount === 1 ? 'obs' : 'obs'}
          </span>
        </div>
      </div>

      {/* 2. Collection Details & Action Footer */}
      <div
        style={{
          padding: '16px 18px',
          display: 'flex',
          flexDirection: 'column',
          justify: 'space-between',
          flex: 1,
          gap: '12px'
        }}
      >
        <div>
          <h3
            style={{
              fontSize: '1.05rem',
              fontWeight: 800,
              color: 'var(--text-main)',
              letterSpacing: '-0.015em',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}
          >
            {collection.name}
          </h3>
          <p
            style={{
              fontSize: '0.82rem',
              color: 'var(--text-muted)',
              marginTop: '4px',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              lineHeight: 1.45
            }}
          >
            {collection.description || 'Personal digital biodiversity collection book.'}
          </p>
        </div>

        {/* Metrics pill line */}
        <div
          style={{
            fontSize: '0.78rem',
            fontWeight: 600,
            color: 'var(--text-dim)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <span>{speciesCount} species</span>
          <span>·</span>
          <span>{obsCount} observations</span>
        </div>

        {/* Divider & Action Bar */}
        <div
          style={{
            borderTop: '1px solid var(--border-glass)',
            paddingTop: '10px',
            display: 'flex',
            alignItems: 'center',
            justify: 'space-between'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            <Calendar size={13} color="var(--text-dim)" />
            <span>{updatedDate}</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }} onClick={(e) => e.stopPropagation()}>
            {onEdit && (
              <button
                type="button"
                onClick={() => onEdit(collection)}
                title="Edit Collection"
                className="btn btn-secondary"
                style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)' }}
              >
                <Edit3 size={14} color="var(--text-muted)" />
              </button>
            )}
            {onDelete && (
              <button
                type="button"
                onClick={() => onDelete(collection)}
                title="Delete Collection"
                className="btn btn-secondary"
                style={{ padding: '6px 8px', borderRadius: 'var(--radius-sm)', borderColor: 'rgba(239, 68, 68, 0.3)', color: '#ef4444' }}
              >
                <Trash2 size={14} color="#ef4444" />
              </button>
            )}
            <button
              type="button"
              onClick={() => onOpen(collection)}
              className="btn btn-primary"
              style={{ padding: '6px 14px', fontSize: '0.78rem', borderRadius: 'var(--radius-sm)' }}
            >
              Open
              <ChevronRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
