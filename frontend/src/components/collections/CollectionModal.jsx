import React, { useState, useEffect } from 'react';
import { X, Plus, BookOpen, Check, Loader2 } from 'lucide-react';
import { getCollections, createCollection, addCollectionItem } from '../../services/api';

export default function CollectionModal({
  isOpen,
  onClose,
  mode = 'create', // 'create' | 'add_item'
  itemToAdd = null, // { item_type: 'observation' | 'explored', scientific_name, common_name, category, observation_id }
  onSuccess
}) {
  const [collections, setCollections] = useState([]);
  const [selectedCollectionId, setSelectedCollectionId] = useState('');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [fetchingCollections, setFetchingCollections] = useState(false);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(mode === 'create');

  useEffect(() => {
    if (isOpen) {
      setError(null);
      setName('');
      setDescription('');
      if (mode === 'add_item') {
        fetchCollectionsList();
      }
    }
  }, [isOpen, mode]);

  const fetchCollectionsList = async () => {
    setFetchingCollections(true);
    try {
      const data = await getCollections();
      setCollections(data);
      if (data.length > 0) {
        setSelectedCollectionId(data[0].id);
      } else {
        setShowCreateForm(true);
      }
    } catch (err) {
      console.error('Error fetching collections:', err);
      setError('Failed to load collections.');
    } finally {
      setFetchingCollections(false);
    }
  };

  if (!isOpen) return null;

  const handleCreate = async (e) => {
    e.preventDefault();
    if (loading) return;
    if (!name.trim()) {
      setError('Collection name is required.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const newColl = await createCollection({ name: name.trim(), description: description.trim() });
      if (mode === 'add_item' && itemToAdd) {
        await addCollectionItem(newColl.id, itemToAdd);
      }
      if (onSuccess) onSuccess(newColl);
      onClose();
    } catch (err) {
      console.error('Error creating collection:', err);
      const apiDetail = err.response?.data?.detail;
      setError(typeof apiDetail === 'string' ? apiDetail : 'Unable to create collection. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddItem = async (e) => {
    e.preventDefault();
    if (!selectedCollectionId) {
      setError('Please select a collection.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await addCollectionItem(selectedCollectionId, itemToAdd);
      if (onSuccess) onSuccess();
      onClose();
    } catch (err) {
      console.error('Error adding item to collection:', err);
      setError('Failed to add item to collection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      justify: 'center',
      padding: '20px',
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)'
    }}>
      <div className="glass-panel" style={{
        position: 'relative',
        width: '100%',
        maxWidth: '520px',
        padding: '28px',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-lg)',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        background: 'var(--bg-card)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '42px', height: '42px', borderRadius: 'var(--radius-md)', background: 'var(--color-plant-bg)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <BookOpen size={22} color="var(--accent-primary)" />
            </div>
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-main)' }}>
                {mode === 'create' || showCreateForm ? 'Create New Collection' : 'Add to Collection'}
              </h2>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                {itemToAdd
                  ? `Add "${itemToAdd.common_name || itemToAdd.scientific_name}" to your biodiversity collection.`
                  : 'Organize your observations and explored species.'}
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="btn btn-secondary"
            style={{ padding: '8px', borderRadius: 'var(--radius-full)', border: 'none', background: 'transparent' }}
          >
            <X size={20} color="var(--text-muted)" />
          </button>
        </div>

        {error && (
          <div style={{ padding: '12px 16px', borderRadius: 'var(--radius-sm)', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#ef4444', fontSize: '0.82rem', fontWeight: 600 }}>
            {error}
          </div>
        )}

        {/* Mode: Add Item to Existing Collection */}
        {mode === 'add_item' && !showCreateForm ? (
          <form onSubmit={handleAddItem} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {fetchingCollections ? (
              <div style={{ padding: '32px 0', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--text-muted)' }}>
                <Loader2 className="animate-spin" size={20} color="var(--accent-primary)" />
                <span>Loading your collections...</span>
              </div>
            ) : collections.length === 0 ? (
              <div style={{ padding: '24px 0', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
                <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>You have no collections yet.</p>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(true)}
                  className="btn btn-primary"
                  style={{ padding: '10px 20px', fontSize: '0.85rem' }}
                >
                  + Create First Collection
                </button>
              </div>
            ) : (
              <>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  <label style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                    Select Collection
                  </label>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '200px', overflowY: 'auto', paddingRight: '4px' }}>
                    {collections.map((coll) => (
                      <label
                        key={coll.id}
                        className="glass-panel"
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justify: 'space-between',
                          padding: '12px 16px',
                          cursor: 'pointer',
                          borderColor: selectedCollectionId === coll.id ? 'var(--accent-primary)' : 'var(--border-glass)',
                          background: selectedCollectionId === coll.id ? 'var(--color-plant-bg)' : 'var(--bg-secondary)'
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                          <input
                            type="radio"
                            name="collectionSelect"
                            value={coll.id}
                            checked={selectedCollectionId === coll.id}
                            onChange={() => setSelectedCollectionId(coll.id)}
                            style={{ display: 'none' }}
                          />
                          <div>
                            <p style={{ fontSize: '0.92rem', fontWeight: 700, color: 'var(--text-main)' }}>{coll.name}</p>
                            <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{coll.species_count} species · {coll.observation_count} observations</p>
                          </div>
                        </div>
                        {selectedCollectionId === coll.id && (
                          <div style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--accent-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <Check size={14} color="#ffffff" />
                          </div>
                        )}
                      </label>
                    ))}
                  </div>
                </div>

                <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(true)}
                    style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--accent-primary)', background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
                  >
                    <Plus size={14} /> Create New Collection
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="btn btn-primary"
                    style={{ padding: '10px 20px', fontSize: '0.85rem' }}
                  >
                    {loading ? <Loader2 className="animate-spin" size={16} /> : null}
                    Add to Collection
                  </button>
                </div>
              </>
            )}
          </form>
        ) : (
          /* Form: Create Collection */
          <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                Collection Name *
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder='e.g., "My Bird Collection", "Campus Plants"'
                required
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              />
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                Description (Optional)
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Short description of this collection book..."
                rows={3}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.9rem',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>

            <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: '12px' }}>
              {mode === 'add_item' && collections.length > 0 && (
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="btn btn-secondary"
                  style={{ padding: '10px 18px', fontSize: '0.85rem' }}
                >
                  Back to List
                </button>
              )}
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
                style={{ padding: '10px 22px', fontSize: '0.85rem' }}
              >
                {loading ? <Loader2 className="animate-spin" size={16} /> : null}
                {itemToAdd ? 'Create & Add Item' : 'Create Collection'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
