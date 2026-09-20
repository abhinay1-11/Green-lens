import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Search, Filter, BookOpen, Plus, Loader2, Info, Compass, ChevronRight, AlertTriangle } from 'lucide-react';
import { searchSpecies, getCollections, deleteCollection } from '../services/api';
import CollectionCard from '../components/collections/CollectionCard';
import CollectionModal from '../components/collections/CollectionModal';
import CollectionDetail from '../components/collections/CollectionDetail';

export default function SpeciesExplorer() {
  const [activeTab, setActiveTab] = useState('EXPLORE'); // 'EXPLORE' | 'COLLECTIONS'
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [speciesResults, setSpeciesResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [selectedSpecies, setSelectedSpecies] = useState(null);

  // Request cancellation and client-side caching refs
  const activeRequestRef = useRef(null);
  const searchCacheRef = useRef(new Map());

  // Collections state
  const [collections, setCollections] = useState([]);
  const [loadingCollections, setLoadingCollections] = useState(false);
  const [activeCollection, setActiveCollection] = useState(null);
  
  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create');
  const [itemToAdd, setItemToAdd] = useState(null);

  const categories = ['ALL', 'BIRDS', 'PLANTS', 'TREES', 'INSECTS', 'OTHER'];

  // Debounced search on typing or category change (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      fetchSpecies(searchQuery, selectedCategory);
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, selectedCategory]);

  useEffect(() => {
    if (activeTab === 'COLLECTIONS') {
      fetchUserCollections();
    }
  }, [activeTab]);

  const fetchSpecies = async (query = '', category = 'ALL') => {
    const trimmedQuery = query.trim();
    if (trimmedQuery.length > 0 && trimmedQuery.length < 2) {
      setSearchError('Enter at least 2 characters.');
      setSpeciesResults([]);
      setSelectedSpecies(null);
      return;
    }

    const cacheKey = `${trimmedQuery.toLowerCase()}:${category.toLowerCase()}`;
    if (searchCacheRef.current.has(cacheKey)) {
      const cachedResults = searchCacheRef.current.get(cacheKey);
      setSpeciesResults(cachedResults || []);
      setSelectedSpecies(cachedResults && cachedResults.length > 0 ? cachedResults[0] : null);
      setSearchError(null);
      setLoading(false);
      return;
    }

    // Cancel in-flight stale request
    if (activeRequestRef.current) {
      activeRequestRef.current.abort();
    }

    const controller = new AbortController();
    activeRequestRef.current = controller;

    setLoading(true);
    setSearchError(null);

    try {
      const data = await searchSpecies(trimmedQuery, category, { signal: controller.signal });
      searchCacheRef.current.set(cacheKey, data || []);
      setSpeciesResults(data || []);
      if (data && data.length > 0) {
        setSelectedSpecies(data[0]);
      } else {
        setSelectedSpecies(null);
      }
    } catch (err) {
      if (err.name === 'CanceledError' || err.name === 'AbortError' || axios.isCancel?.(err)) {
        return; // Stale request safely ignored
      }
      console.error('Error searching species:', err);
      const msg = err.response?.data?.detail || 'Species search is temporarily unavailable. Please try again.';
      setSearchError(typeof msg === 'string' ? msg : 'Species search is temporarily unavailable. Please try again.');
      setSpeciesResults([]);
      setSelectedSpecies(null);
    } finally {
      if (activeRequestRef.current === controller) {
        activeRequestRef.current = null;
        setLoading(false);
      }
    }
  };

  const fetchUserCollections = async () => {
    setLoadingCollections(true);
    try {
      const data = await getCollections();
      setCollections(data);
    } catch (err) {
      console.error('Error fetching collections:', err);
    } finally {
      setLoadingCollections(false);
    }
  };

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    fetchSpecies(searchQuery, selectedCategory);
  };

  const handleAddToCollection = (sp) => {
    setItemToAdd({
      item_type: 'explored',
      scientific_name: sp.scientific_name,
      common_name: sp.common_name,
      category: sp.category,
    });
    setModalMode('add_item');
    setIsModalOpen(true);
  };

  const handleCreateCollectionClick = () => {
    setItemToAdd(null);
    setModalMode('create');
    setIsModalOpen(true);
  };

  const handleModalSuccess = () => {
    if (activeTab === 'COLLECTIONS') {
      fetchUserCollections();
    }
  };

  if (activeCollection) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <CollectionDetail
          collection={activeCollection}
          onBack={() => setActiveCollection(null)}
          onNavigateExplore={() => {
            setActiveCollection(null);
            setActiveTab('EXPLORE');
          }}
          onItemRemoved={async () => {
            const data = await getCollections();
            const updated = data.find(c => c.id === activeCollection.id);
            if (updated) setActiveCollection(updated);
          }}
        />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-fade-in">
      {/* Page Header */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between', gap: '16px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '20px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h1 style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-main)', letterSpacing: '-0.025em' }}>
              Species Explorer
            </h1>
            <span className="badge badge-plant">
              Global Biodiversity
            </span>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Explore plants, trees, birds, insects and other species from around the world.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div style={{ display: 'flex', alignItems: 'center', padding: '4px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-glass)' }}>
          <button
            type="button"
            onClick={() => setActiveTab('EXPLORE')}
            className={activeTab === 'EXPLORE' ? 'btn btn-primary' : 'btn btn-secondary'}
            style={{ padding: '8px 16px', fontSize: '0.82rem', borderRadius: 'var(--radius-sm)' }}
          >
            <Compass size={16} />
            Global Explorer
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('COLLECTIONS')}
            className={activeTab === 'COLLECTIONS' ? 'btn btn-primary' : 'btn btn-secondary'}
            style={{ padding: '8px 16px', fontSize: '0.82rem', borderRadius: 'var(--radius-sm)', marginLeft: '4px' }}
          >
            <BookOpen size={16} />
            My Species Collections
          </button>
        </div>
      </div>

      {/* TAB 1: GLOBAL EXPLORER */}
      {activeTab === 'EXPLORE' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Primary Search Box */}
          <form onSubmit={handleSearchSubmit} style={{ position: 'relative', maxWidth: '720px' }}>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <Search style={{ position: 'absolute', left: '16px', color: 'var(--text-dim)', pointerEvents: 'none' }} size={20} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search species... (e.g., Greater Sage-Grouse, Neem, Monarch Butterfly)"
                style={{
                  width: '100%',
                  paddingLeft: '48px',
                  paddingRight: '120px',
                  paddingTop: '14px',
                  paddingBottom: '14px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border-glass)',
                  color: 'var(--text-main)',
                  fontSize: '0.92rem',
                  outline: 'none',
                  boxShadow: 'inset 0 1px 3px rgba(0,0,0,0.1)'
                }}
              />
              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary"
                style={{ position: 'absolute', right: '6px', padding: '8px 18px', fontSize: '0.85rem' }}
              >
                {loading ? <Loader2 className="animate-spin" size={16} /> : null}
                Search
              </button>
            </div>
            <div style={{ marginTop: '8px', fontSize: '0.78rem', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, color: 'var(--text-dim)' }}>Try searching:</span>
              <button type="button" onClick={() => { setSearchQuery('Greater Sage-Grouse'); fetchSpecies('Greater Sage-Grouse', selectedCategory); }} style={{ color: 'var(--accent-primary)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}>Greater Sage-Grouse</button>
              <span>·</span>
              <button type="button" onClick={() => { setSearchQuery('Neem'); fetchSpecies('Neem', selectedCategory); }} style={{ color: 'var(--accent-primary)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}>Neem</button>
              <span>·</span>
              <button type="button" onClick={() => { setSearchQuery('Apis mellifera'); fetchSpecies('Apis mellifera', selectedCategory); }} style={{ color: 'var(--accent-primary)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}>Apis mellifera</button>
              <span>·</span>
              <button type="button" onClick={() => { setSearchQuery('Black-footed Albatross'); fetchSpecies('Black-footed Albatross', selectedCategory); }} style={{ color: 'var(--accent-primary)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}>Black-footed Albatross</button>
              <span>·</span>
              <button type="button" onClick={() => { setSearchQuery('Monarch Butterfly'); fetchSpecies('Monarch Butterfly', selectedCategory); }} style={{ color: 'var(--accent-primary)', textDecoration: 'underline', background: 'none', border: 'none', cursor: 'pointer' }}>Monarch Butterfly</button>
            </div>
          </form>

          {/* Category Filter Pills (BUG 2 FIX) */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflowX: 'auto', paddingBottom: '8px', borderBottom: '1px solid var(--border-glass)' }}>
            <Filter size={16} style={{ color: 'var(--text-muted)', flexShrink: 0, marginRight: '4px' }} />
            {categories.map((cat) => (
              <button
                key={cat}
                type="button"
                onClick={() => setSelectedCategory(cat)}
                className={selectedCategory === cat ? 'btn btn-primary' : 'btn btn-secondary'}
                style={{ padding: '6px 14px', fontSize: '0.78rem', borderRadius: 'var(--radius-full)', flexShrink: 0 }}
              >
                {cat}
              </button>
            ))}
          </div>

          {/* Explorer Main Content & States (BUG 1 & BUG 2 FIX) */}
          {loading ? (
            <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '12px' }}>
              <Loader2 className="animate-spin" size={32} color="var(--accent-primary)" />
              <p style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--text-main)' }}>Searching global species databases...</p>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Fetching taxonomy, facts and reference media</p>
            </div>
          ) : searchError ? (
            <div style={{ padding: '32px 24px', textAlign: 'center', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
              <AlertTriangle size={36} color="#ef4444" />
              <p style={{ fontSize: '1rem', fontWeight: 700, color: '#ef4444' }}>{searchError}</p>
              <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>Check your network connection or enter another search query.</p>
            </div>
          ) : speciesResults.length === 0 ? (
            <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px' }}>
              <Info size={40} color="var(--text-dim)" />
              <p style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>
                {selectedCategory !== 'ALL' ? 'No species found in this category.' : 'No matching species found globally.'}
              </p>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>Try searching for common names like "Greater Sage-Grouse" or "Neem", or switch categories.</p>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '24px', alignItems: 'start' }}>
              {/* Left Column: Species List Selector (4 cols) */}
              <div style={{ gridColumn: 'span 4', display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '720px', overflowY: 'auto', paddingRight: '4px' }}>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                  Results ({speciesResults.length})
                </span>
                {speciesResults.map((sp) => {
                  const isSelected = selectedSpecies?.scientific_name === sp.scientific_name;
                  const coverImg = sp.reference_images && sp.reference_images.length > 0 ? sp.reference_images[0].url : null;

                  return (
                    <div
                      key={sp.scientific_name}
                      onClick={() => setSelectedSpecies(sp)}
                      className={`glass-panel ${isSelected ? '' : 'glass-panel-hover'}`}
                      style={{
                        padding: '14px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justify: 'space-between',
                        borderColor: isSelected ? 'var(--accent-primary)' : 'var(--border-glass)',
                        background: isSelected ? 'var(--color-plant-bg)' : 'var(--bg-card)'
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', overflow: 'hidden' }}>
                        <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tertiary)', overflow: 'hidden', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          {coverImg ? (
                            <img src={coverImg} alt={sp.common_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          ) : (
                            <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase' }}>{sp.category.slice(0, 2)}</span>
                          )}
                        </div>
                        <div style={{ overflow: 'hidden' }}>
                          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {sp.common_name || sp.scientific_name}
                          </h4>
                          <p style={{ fontSize: '0.78rem', fontStyle: 'italic', color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                            {sp.scientific_name}
                          </p>
                          <span className={`badge badge-${sp.category === 'bird' ? 'bird' : sp.category === 'plant' ? 'plant' : sp.category === 'insect' ? 'insect' : 'unknown'}`} style={{ marginTop: '4px' }}>
                            {sp.category}
                          </span>
                        </div>
                      </div>
                      <ChevronRight size={18} color={isSelected ? 'var(--accent-primary)' : 'var(--text-dim)'} style={{ flexShrink: 0 }} />
                    </div>
                  );
                })}
              </div>

              {/* Right Column: Polished Species Profile Card (8 cols) */}
              <div style={{ gridColumn: 'span 8' }}>
                {selectedSpecies && (
                  <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                    {/* Header Split: Left visual image, Right taxonomy info */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: '20px', alignItems: 'center' }}>
                      {/* Left: Species Visual */}
                      <div style={{ gridColumn: 'span 5', height: '220px', borderRadius: 'var(--radius-md)', background: 'var(--bg-tertiary)', overflow: 'hidden', position: 'relative', border: '1px solid var(--border-glass)' }}>
                        {selectedSpecies.reference_images && selectedSpecies.reference_images.length > 0 ? (
                          <img
                            key={selectedSpecies.scientific_name}
                            src={selectedSpecies.reference_images[0].url}
                            alt={selectedSpecies.common_name}
                            loading="lazy"
                            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                            onError={(e) => { e.target.style.display = 'none'; }}
                          />
                        ) : (
                          <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-dim)' }}>
                            <Info size={36} opacity={0.5} />
                            <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 600, marginTop: '6px' }}>Reference Image Unavailable</span>
                          </div>
                        )}
                        <div style={{ position: 'absolute', top: '10px', left: '10px' }}>
                          <span className={`badge badge-${selectedSpecies.category === 'bird' ? 'bird' : selectedSpecies.category === 'plant' ? 'plant' : selectedSpecies.category === 'insect' ? 'insect' : 'unknown'}`}>
                            {selectedSpecies.category}
                          </span>
                        </div>
                      </div>

                      {/* Right: Primary Names & Actions */}
                      <div style={{ gridColumn: 'span 7', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', height: '100%', gap: '14px' }}>
                        <div>
                          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                            {selectedSpecies.taxonomic_rank || 'Species'}
                          </span>
                          <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-main)', marginTop: '2px', lineHeight: 1.25 }}>
                            {selectedSpecies.common_name || selectedSpecies.scientific_name}
                          </h2>
                          <p style={{ fontSize: '0.95rem', fontStyle: 'italic', color: 'var(--text-muted)', marginTop: '4px' }}>
                            {selectedSpecies.scientific_name}
                          </p>
                        </div>

                        {/* Observation Status pill */}
                        <div style={{ padding: '10px 14px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-secondary)', border: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.8rem' }}>
                          <span style={{ color: 'var(--text-muted)' }}>Observation History:</span>
                          <span style={{ fontWeight: 700, color: selectedSpecies.observation_count > 0 ? 'var(--accent-primary)' : 'var(--text-muted)' }}>
                            {selectedSpecies.observation_count > 0
                              ? `Observed ${selectedSpecies.observation_count} ${selectedSpecies.observation_count === 1 ? 'time' : 'times'}`
                              : 'No observations recorded yet'}
                          </span>
                        </div>

                        {/* Add to Collection Button */}
                        <button
                          type="button"
                          onClick={() => handleAddToCollection(selectedSpecies)}
                          className="btn btn-primary"
                          style={{ width: 'fit-content', padding: '10px 20px', fontSize: '0.88rem' }}
                        >
                          <Plus size={16} />
                          Add to Collection
                        </button>
                      </div>
                    </div>

                    {/* About This Species */}
                    <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                      <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                        About This Species
                      </h3>
                      <p className="editorial-desc">
                        {selectedSpecies.description || 'Information unavailable'}
                      </p>
                    </div>

                    {/* Quick Facts Grid */}
                    <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                        Quick Facts
                      </h3>
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px' }}>
                        <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Habitat</span>
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{selectedSpecies.habitat || 'Information unavailable'}</span>
                        </div>
                        <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Diet</span>
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{selectedSpecies.diet || 'Information unavailable'}</span>
                        </div>
                        <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Behavior</span>
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{selectedSpecies.behavior || 'Information unavailable'}</span>
                        </div>
                        <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Reproduction</span>
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{selectedSpecies.reproduction || 'Information unavailable'}</span>
                        </div>
                        <div style={{ padding: '12px 14px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                          <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '2px' }}>Conservation</span>
                          <span style={{ fontSize: '0.82rem', color: 'var(--text-main)' }}>{selectedSpecies.conservation || 'Information unavailable'}</span>
                        </div>
                      </div>
                    </div>

                    {/* Taxonomy Breakdown */}
                    <div style={{ borderTop: '1px solid var(--border-glass)', paddingTop: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <h3 style={{ fontSize: '0.82rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)' }}>
                        Taxonomy
                      </h3>
                      <div className="taxonomy-flow">
                        {selectedSpecies.kingdom && <div className="taxonomy-item"><span>Kingdom:</span> <strong>{selectedSpecies.kingdom}</strong></div>}
                        {selectedSpecies.phylum && <div className="taxonomy-item"><span>Phylum:</span> <strong>{selectedSpecies.phylum}</strong></div>}
                        {selectedSpecies.class_name && <div className="taxonomy-item"><span>Class:</span> <strong>{selectedSpecies.class_name}</strong></div>}
                        {selectedSpecies.order && <div className="taxonomy-item"><span>Order:</span> <strong>{selectedSpecies.order}</strong></div>}
                        {selectedSpecies.family && <div className="taxonomy-item"><span>Family:</span> <strong>{selectedSpecies.family}</strong></div>}
                        {selectedSpecies.genus && <div className="taxonomy-item"><span>Genus:</span> <strong>{selectedSpecies.genus}</strong></div>}
                        <div className="taxonomy-item" style={{ borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}><span>Species:</span> <strong style={{ fontStyle: 'italic' }}>{selectedSpecies.scientific_name}</strong></div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: MY SPECIES COLLECTIONS */}
      {activeTab === 'COLLECTIONS' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h2 style={{ fontSize: '1.3rem', fontWeight: 700, color: 'var(--text-main)' }}>
                My Biodiversity Collection Books
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                Personal collection books combining your field observations and explored species.
              </p>
            </div>
            <button
              type="button"
              onClick={handleCreateCollectionClick}
              className="btn btn-primary"
              style={{ padding: '10px 20px', fontSize: '0.85rem' }}
            >
              <Plus size={16} />
              Create Collection
            </button>
          </div>

          {loadingCollections ? (
            <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px', color: 'var(--text-muted)' }}>
              <Loader2 className="animate-spin" size={24} color="var(--accent-primary)" />
              <span>Loading collections...</span>
            </div>
          ) : collections.length === 0 ? (
            <div className="glass-panel" style={{ padding: '60px 24px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
              <BookOpen size={44} color="var(--accent-primary)" opacity={0.8} />
              <div>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-main)' }}>No Collections Created Yet</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', maxWidth: '400px', margin: '4px auto 0' }}>
                  Create digital collection books like "My Bird Collection" or "Campus Plants" to group your species and export field reports.
                </p>
              </div>
              <button
                type="button"
                onClick={handleCreateCollectionClick}
                className="btn btn-primary"
                style={{ padding: '10px 20px', fontSize: '0.85rem' }}
              >
                + Create First Collection
              </button>
            </div>
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px' }}>
              {collections.map((coll) => (
                <CollectionCard
                  key={coll.id}
                  collection={coll}
                  onOpen={(c) => setActiveCollection(c)}
                  onEdit={() => {}}
                  onDelete={async (c) => {
                    if (window.confirm(`Delete collection "${c.name}"? (Your recorded observations will NOT be deleted)`)) {
                      try {
                        await deleteCollection(c.id);
                        await fetchUserCollections();
                      } catch (err) {
                        console.error('Error deleting collection:', err);
                      }
                    }
                  }}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Collection Modal */}
      <CollectionModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        mode={modalMode}
        itemToAdd={itemToAdd}
        onSuccess={handleModalSuccess}
      />
    </div>
  );
}
