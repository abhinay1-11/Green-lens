import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  Leaf, Bird, Bug, HelpCircle, Upload, Camera, Check, RefreshCw, 
  AlertCircle, ArrowRight, X, Search, AlertTriangle, Image as ImageIcon, 
  BookOpen, ExternalLink, ShieldCheck, Layers, ChevronRight, Info, Plus,
  MapPin, Loader2
} from 'lucide-react';
import { predictSpecies, createObservation, searchSpecies, API_BASE } from '../services/api';

import { CategoryBadge, MockBadge } from '../components/common/Badge';
import LoadingSpinner from '../components/common/LoadingSpinner';
import CameraCapture from '../components/identification/CameraCapture';
import CollectionModal from '../components/collections/CollectionModal';

export default function Observe() {
  const navigate = useNavigate();
  const location = useLocation();

  // Wizard Steps: 1: Category, 2: Upload, 3: AI Review, 4: Location & Notes, 5: Success
  const [step, setStep] = useState(1);

  // Form State
  const [category, setCategory] = useState('bird');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [organTags, setOrganTags] = useState(['auto']);
  const [previewUrls, setPreviewUrls] = useState([]);
  const [showCameraMode, setShowCameraMode] = useState(false);

  // Identification State
  const [loading, setLoading] = useState(false);
  const [predictionResponse, setPredictionResponse] = useState(null);
  const [selectedSpecies, setSelectedSpecies] = useState(null);
  const [verificationStatus, setVerificationStatus] = useState('user_confirmed');
  const [errorDetails, setErrorDetails] = useState(null);

  // Manual search modal state
  const [showManualSearch, setShowManualSearch] = useState(false);
  const [manualQuery, setManualQuery] = useState('');
  const [manualResults, setManualResults] = useState([]);

  // Collection modal state
  const [isCollectionModalOpen, setIsCollectionModalOpen] = useState(false);
  const [savedObservationId, setSavedObservationId] = useState(null);

  // Location state (Live vs Manual)
  const [locationMode, setLocationMode] = useState('live'); // 'live' | 'manual'
  const [manualLocation, setManualLocation] = useState('');
  const [latitude, setLatitude] = useState(null);
  const [longitude, setLongitude] = useState(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoError, setGeoError] = useState(null);
  const [geoSuccess, setGeoSuccess] = useState(false);
  const [notes, setNotes] = useState('');

  const handleDetectLiveLocation = () => {
    if (!navigator.geolocation) {
      setGeoError('Geolocation is not supported by your browser. You can enter the location manually instead.');
      setLocationMode('manual');
      return;
    }

    setGeoLoading(true);
    setGeoError(null);

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLatitude(position.coords.latitude);
        setLongitude(position.coords.longitude);
        setGeoSuccess(true);
        setGeoLoading(false);
      },
      (error) => {
        setGeoLoading(false);
        setGeoSuccess(false);
        if (error.code === error.PERMISSION_DENIED) {
          setGeoError('Location access was denied. You can enter the location manually instead.');
        } else {
          setGeoError('Failed to detect location automatically. You can enter the location manually instead.');
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  };

  // Reset function
  const resetWizardState = () => {
    setStep(1);
    setCategory('bird');
    setSelectedFiles([]);
    setOrganTags(['auto']);
    setPreviewUrls([]);
    setShowCameraMode(false);
    setLoading(false);
    setPredictionResponse(null);
    setSelectedSpecies(null);
    setVerificationStatus('user_confirmed');
    setErrorDetails(null);
    setShowManualSearch(false);
    setNotes('');
    setSavedObservationId(null);
    setLocationMode('live');
    setManualLocation('');
    setLatitude(null);
    setLongitude(null);
    setGeoLoading(false);
    setGeoError(null);
    setGeoSuccess(false);
  };

  useEffect(() => {
    if (location.state?.reset) {
      resetWizardState();
    }
  }, [location.state]);

  const handleSelectCategory = (cat) => {
    setCategory(cat);
    setStep(2);
  };

  const handleFileChange = (e) => {
    const files = Array.from(e.target.files);
    if (!files.length) return;

    const maxAllowed = category === 'plant' ? 5 : 1;
    const combinedFiles = [...selectedFiles, ...files].slice(0, maxAllowed);
    setSelectedFiles(combinedFiles);

    const urls = combinedFiles.map((file) => URL.createObjectURL(file));
    setPreviewUrls(urls);

    const organs = combinedFiles.map((_, idx) => organTags[idx] || 'auto');
    setOrganTags(organs);
  };

  const handleCameraCapturedFile = (file) => {
    if (!file) return;

    const maxAllowed = category === 'plant' ? 5 : 1;
    const combinedFiles = [...selectedFiles, file].slice(0, maxAllowed);
    setSelectedFiles(combinedFiles);

    const url = URL.createObjectURL(file);
    const updatedUrls = [...previewUrls, url].slice(0, maxAllowed);
    setPreviewUrls(updatedUrls);

    const organs = combinedFiles.map((_, idx) => organTags[idx] || 'auto');
    setOrganTags(organs);

    setShowCameraMode(false);
  };

  const handleRemoveFile = (index) => {
    const updatedFiles = selectedFiles.filter((_, i) => i !== index);
    const updatedUrls = previewUrls.filter((_, i) => i !== index);
    const updatedOrgans = organTags.filter((_, i) => i !== index);

    setSelectedFiles(updatedFiles);
    setPreviewUrls(updatedUrls);
    setOrganTags(updatedOrgans);
  };

  const handleIdentify = async () => {
    if (!selectedFiles.length || loading) return;

    setLoading(true);
    setErrorDetails(null);


    try {
      const formData = new FormData();
      formData.append('category', category);
      selectedFiles.forEach((file) => formData.append('images', file));
      organTags.forEach((org) => formData.append('organs', org));

      const res = await predictSpecies(formData);
      setPredictionResponse(res);

      if (!res.success) {
        setErrorDetails(res.error || { code: 'IDENTIFICATION_FAILED', message: 'Identification service unavailable.' });
      } else if (res.predictions && res.predictions.length > 0) {
        const top = res.predictions[0];
        setSelectedSpecies({
          scientific_name: top.scientific_name,
          common_name: top.common_names?.[0] || '',
          confidence: top.confidence
        });
        setVerificationStatus('user_confirmed');
      }

      setStep(3);
    } catch (err) {
      console.error('Identification Error:', err);
      let code = 'NETWORK_ERROR';
      let message = 'Failed to connect to identification provider.';

      if (err.code === 'ECONNABORTED' || err.response?.status === 504 || (err.message && err.message.toLowerCase().includes('timeout'))) {
        code = 'IDENTIFICATION_TIMEOUT';
        message = 'Identification is taking longer than expected. Please try again.';
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        code = 'BACKEND_UNAVAILABLE';
        message = 'FastAPI backend is unreachable. Please verify network connection.';
      } else if (err.response?.data?.detail?.message) {
        code = err.response.data.detail.code || 'IDENTIFICATION_FAILED';
        message = err.response.data.detail.message;
      } else if (err.response?.data?.message) {
        code = err.response.data.code || 'IDENTIFICATION_FAILED';
        message = err.response.data.message;
      }

      setErrorDetails({ code, message });
      setStep(3);
    } finally {
      setLoading(false);
    }
  };

  const handleRefineCategory = async (targetCategory) => {
    if (!selectedFiles.length) return;
    setCategory(targetCategory);
    setLoading(true);
    setErrorDetails(null);

    try {
      const formData = new FormData();
      formData.append('category', targetCategory);
      selectedFiles.forEach((file) => formData.append('images', file));
      organTags.forEach((org) => formData.append('organs', org));

      const res = await predictSpecies(formData);
      setPredictionResponse(res);

      if (!res.success) {
        setErrorDetails(res.error || { code: 'IDENTIFICATION_FAILED', message: 'Identification service unavailable.' });
      } else if (res.predictions && res.predictions.length > 0) {
        const top = res.predictions[0];
        setSelectedSpecies({
          scientific_name: top.scientific_name,
          common_name: top.common_names?.[0] || '',
          confidence: top.confidence
        });
        setVerificationStatus('user_confirmed');
      }
    } catch (err) {
      console.error('Refine Error:', err);
      let code = 'NETWORK_ERROR';
      let message = 'Failed to connect to identification provider.';

      if (err.code === 'ECONNABORTED' || err.response?.status === 504 || (err.message && err.message.toLowerCase().includes('timeout'))) {
        code = 'IDENTIFICATION_TIMEOUT';
        message = 'Identification is taking longer than expected. Please try again.';
      } else if (err.code === 'ERR_NETWORK' || !err.response) {
        code = 'BACKEND_UNAVAILABLE';
        message = 'FastAPI backend is unreachable. Please verify network connection.';
      } else if (err.response?.data?.detail?.message) {
        code = err.response.data.detail.code || 'IDENTIFICATION_FAILED';
        message = err.response.data.detail.message;
      } else if (err.response?.data?.message) {
        code = err.response.data.code || 'IDENTIFICATION_FAILED';
        message = err.response.data.message;
      }

      setErrorDetails({ code, message });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmTop = () => {
    setVerificationStatus('user_confirmed');
    setStep(4);
  };

  const handleSelectAlternative = (pred) => {
    setSelectedSpecies({
      scientific_name: pred.scientific_name,
      common_name: pred.common_names?.[0] || '',
      confidence: pred.confidence
    });
    setVerificationStatus('user_corrected');
    setStep(4);
  };

  const handleManualSearch = async () => {
    if (!manualQuery.trim()) return;
    try {
      const res = await searchSpecies(manualQuery, category);
      setManualResults(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectManual = (sp) => {
    setSelectedSpecies({
      scientific_name: sp.scientific_name,
      common_name: sp.common_name || '',
      confidence: 0.0
    });
    setVerificationStatus('user_corrected');
    setShowManualSearch(false);
    setStep(4);
  };

  const handleSubmitObservation = async () => {
    setLoading(true);
    try {
      const imagePaths = previewUrls.length ? previewUrls : ['/uploads/sample.jpg'];

      const payload = {
        category: category,
        scientific_name: selectedSpecies?.scientific_name || 'Unidentified',
        common_name: selectedSpecies?.common_name || '',
        latitude: locationMode === 'live' ? latitude : null,
        longitude: locationMode === 'live' ? longitude : null,
        campus_zone: locationMode === 'manual'
          ? (manualLocation.trim() || 'Manual Location')
          : (latitude && longitude ? `Live Location (${latitude.toFixed(4)}, ${longitude.toFixed(4)})` : 'Live Location'),
        notes: notes,
        ai_provider: predictionResponse?.provider || 'unconfigured',
        ai_model_version: predictionResponse?.model_version || 'v1.0',
        ai_confidence: selectedSpecies?.confidence || 0.0,
        ai_predicted_scientific_name: predictionResponse?.predictions?.[0]?.scientific_name || null,
        ai_predicted_common_name: predictionResponse?.predictions?.[0]?.common_names?.[0] || null,
        verification_status: verificationStatus,
        image_paths: imagePaths,
        organ_tags: organTags,
        predictions_history: predictionResponse?.predictions || []
      };

      const obsRes = await createObservation(payload);
      if (obsRes && obsRes.id) {
        setSavedObservationId(obsRes.id);
      }
      setStep(5);
    } catch (err) {
      console.error('Submit error:', err);
      alert('Failed to save observation record.');
    } finally {
      setLoading(false);
    }
  };

  const topPrediction = predictionResponse?.predictions?.[0];
  const speciesProfile = predictionResponse?.species_profile;
  const taxonomy = speciesProfile?.taxonomy;
  const facts = speciesProfile?.facts;

  // Visual Theme accents per category
  const categoryThemes = {
    bird: {
      accentColor: '#38bdf8', // sky blue
      borderColor: 'rgba(56, 189, 248, 0.4)',
      bgColor: 'rgba(56, 189, 248, 0.05)',
      title: 'BIRD IDENTIFICATION',
      desc: 'Identify birds from your observation.'
    },
    plant: {
      accentColor: '#10b981', // emerald green
      borderColor: 'rgba(16, 185, 129, 0.4)',
      bgColor: 'rgba(16, 185, 129, 0.05)',
      title: 'PLANT IDENTIFICATION',
      desc: 'Identify plants, trees and flowers from your observation.'
    },
    insect: {
      accentColor: '#f59e0b', // amber
      borderColor: 'rgba(245, 158, 11, 0.4)',
      bgColor: 'rgba(245, 158, 11, 0.05)',
      title: 'INSECT IDENTIFICATION',
      desc: 'Identify insects from your observation.'
    }
  };

  const currentTheme = categoryThemes[category] || categoryThemes.bird;

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '28px', padding: '0 8px' }}>
      
      {/* Wizard Header Bar */}
      <div className="glass-panel" style={{ padding: '18px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 800 }}>Observe & Identify</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Step {step} of 4 — {step === 1 ? 'Select Classifier Engine' : step === 2 ? 'Upload Photo' : step === 3 ? 'AI Review & Results' : 'Confirm Location'}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              style={{
                width: '28px',
                height: '6px',
                borderRadius: '3px',
                background: step >= i ? currentTheme.accentColor : 'rgba(255, 255, 255, 0.12)',
                transition: 'var(--transition-fast)'
              }}
            />
          ))}
        </div>
      </div>

      {/* STEP 1: Select Classifier */}
      {step === 1 && (
        <div className="glass-panel" style={{ padding: '36px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
          <div style={{ textAlign: 'center' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800 }}>Select Classifier Engine</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '6px' }}>
              Choose a dedicated AI classifier tailored for birds, plants, or insects.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
            {/* Bird Classifier Card */}
            <button
              onClick={() => handleSelectCategory('bird')}
              className="glass-panel-hover"
              style={{
                padding: '32px 24px',
                borderRadius: 'var(--radius-lg, 24px)',
                background: category === 'bird' ? 'rgba(56, 189, 248, 0.12)' : 'var(--bg-tertiary)',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                color: '#ffffff',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '14px',
                transition: 'all 0.3s ease'
              }}
            >
              <div style={{ padding: '16px', borderRadius: '50%', background: 'rgba(56, 189, 248, 0.15)' }}>
                <Bird size={42} color="#38bdf8" />
              </div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#38bdf8' }}>BIRD IDENTIFICATION</span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.4 }}>
                Identify birds from your observation. Powered by BioCLIP 2.
              </span>
            </button>

            {/* Plant Classifier Card */}
            <button
              onClick={() => handleSelectCategory('plant')}
              className="glass-panel-hover"
              style={{
                padding: '32px 24px',
                borderRadius: 'var(--radius-lg, 24px)',
                background: category === 'plant' ? 'rgba(16, 185, 129, 0.12)' : 'var(--bg-tertiary)',
                border: '1px solid rgba(16, 185, 129, 0.35)',
                color: '#ffffff',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '14px',
                transition: 'all 0.3s ease'
              }}
            >
              <div style={{ padding: '16px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)' }}>
                <Leaf size={42} color="#10b981" />
              </div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#10b981' }}>PLANT IDENTIFICATION</span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.4 }}>
                Identify plants, trees and flowers from your observation. Powered by Pl@ntNet API.
              </span>
            </button>

            {/* Insect Classifier Card */}
            <button
              onClick={() => handleSelectCategory('insect')}
              className="glass-panel-hover"
              style={{
                padding: '32px 24px',
                borderRadius: 'var(--radius-lg, 24px)',
                background: category === 'insect' ? 'rgba(245, 158, 11, 0.12)' : 'var(--bg-tertiary)',
                border: '1px solid rgba(245, 158, 11, 0.35)',
                color: '#ffffff',
                cursor: 'pointer',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: '14px',
                transition: 'all 0.3s ease'
              }}
            >
              <div style={{ padding: '16px', borderRadius: '50%', background: 'rgba(245, 158, 11, 0.15)' }}>
                <Bug size={42} color="#f59e0b" />
              </div>
              <span style={{ fontSize: '1.15rem', fontWeight: 800, color: '#f59e0b' }}>INSECT IDENTIFICATION</span>
              <span style={{ fontSize: '0.82rem', color: 'var(--text-muted)', textAlign: 'center', lineHeight: 1.4 }}>
                Identify insects from your observation. Powered by Insecta Vision AI.
              </span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Upload or Capture Images */}
      {step === 2 && (
        <div className="glass-panel" style={{ padding: '36px', display: 'flex', flexDirection: 'column', gap: '28px', border: `1px solid ${currentTheme.borderColor}`, background: currentTheme.bgColor }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: currentTheme.accentColor }}>{currentTheme.title}</h2>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '2px' }}>
                {currentTheme.desc}
              </p>
            </div>
            <CategoryBadge category={category} />
          </div>

          {showCameraMode ? (
            <CameraCapture
              onCapture={handleCameraCapturedFile}
              onCancel={() => setShowCameraMode(false)}
              onSwitchToUpload={() => setShowCameraMode(false)}
            />
          ) : (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
              <button
                type="button"
                onClick={() => setShowCameraMode(true)}
                className="glass-panel-hover"
                style={{
                  padding: '28px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-glass)',
                  color: '#ffffff',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '12px'
                }}
              >
                <Camera size={38} color={currentTheme.accentColor} />
                <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>Take Photo</span>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Camera or webcam</span>
              </button>

              <label
                className="glass-panel-hover"
                style={{
                  padding: '28px',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--bg-tertiary)',
                  border: '1px solid var(--border-glass)',
                  color: '#ffffff',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  gap: '12px'
                }}
              >
                <Upload size={38} color={currentTheme.accentColor} />
                <span style={{ fontWeight: 700, fontSize: '1.05rem' }}>Upload File</span>
                <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>Browse JPG, PNG, WEBP</span>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  multiple={category === 'plant'}
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                />
              </label>
            </div>
          )}

          {previewUrls.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Selected Image ({previewUrls.length})
              </h4>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: '16px' }}>
                {previewUrls.map((url, idx) => (
                  <div key={idx} className="glass-panel" style={{ padding: '8px', position: 'relative' }}>
                    <button
                      onClick={() => handleRemoveFile(idx)}
                      style={{
                        position: 'absolute',
                        top: '12px',
                        right: '12px',
                        background: 'rgba(0, 0, 0, 0.8)',
                        color: '#fff',
                        border: 'none',
                        borderRadius: '50%',
                        width: '26px',
                        height: '26px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <X size={14} />
                    </button>
                    <img src={url} alt={`Upload ${idx}`} style={{ width: '100%', height: '140px', objectFit: 'cover', borderRadius: 'var(--radius-sm)' }} />
                  </div>
                ))}
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
            <button className="btn btn-secondary" onClick={() => setStep(1)}>Back</button>
            <button
              className="btn btn-primary"
              disabled={!selectedFiles.length || loading}
              onClick={handleIdentify}
              style={{ background: currentTheme.accentColor, borderColor: currentTheme.accentColor, color: '#000' }}
            >
              {loading ? 'Running AI Identification...' : 'Identify Organism'}
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: AI REVIEW & SPECIES ENRICHMENT RESULT */}
      {step === 3 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
          {loading ? (
            <LoadingSpinner text="Identifying species with BioCLIP 2 and retrieving enrichment facts..." />
          ) : errorDetails ? (
            <div className="glass-panel" style={{ padding: '36px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px', color: '#f87171' }}>
                <AlertTriangle size={36} />
                <div>
                  <h2 style={{ fontSize: '1.35rem', color: '#ffffff' }}>Identification Unavailable</h2>
                  <div style={{ fontSize: '0.85rem', color: '#fca5a5' }}>Code: {errorDetails.code}</div>
                </div>
              </div>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>{errorDetails.message}</p>
              
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button className="btn btn-primary" onClick={() => setShowManualSearch(true)}>
                  <Search size={18} /> Enter Species Manually
                </button>
                <button className="btn btn-secondary" onClick={() => setStep(2)}>
                  <RefreshCw size={18} /> Try Another Image
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* PRIMARY HERO IDENTIFICATION PASSPORT */}
              {topPrediction && (
                <div className="glass-panel" style={{
                  padding: '32px',
                  background: 'linear-gradient(145deg, rgba(16, 26, 29, 0.95) 0%, rgba(22, 38, 42, 0.95) 100%)',
                  border: `1px solid ${currentTheme.borderColor}`,
                  boxShadow: 'var(--shadow-glow)'
                }}>
                  {/* Category Refinement Bar */}
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '24px',
                    paddingBottom: '16px',
                    borderBottom: '1px solid var(--border-glass)',
                    flexWrap: 'wrap',
                    gap: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span className="badge" style={{ padding: '6px 12px', fontSize: '0.8rem', background: currentTheme.bgColor, color: currentTheme.accentColor, border: `1px solid ${currentTheme.borderColor}` }}>
                        {predictionResponse?.provider === 'bird_local_ai' ? 'Bird Species ONNX Engine' : predictionResponse?.provider === 'insect_local_onnx' ? 'Insect EfficientNet-B0 ONNX Engine' : predictionResponse?.provider || (category === 'bird' ? 'Bird Species ONNX Engine' : category === 'plant' ? 'Pl@ntNet API' : 'Insecta Vision AI')}
                      </span>
                      <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        Model: {predictionResponse?.model_name || 'Species Classifier'}
                      </span>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)', fontWeight: 600 }}>Refine:</span>
                      <button onClick={() => handleRefineCategory('bird')} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>Bird</button>
                      <button onClick={() => handleRefineCategory('plant')} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>Plant</button>
                      <button onClick={() => handleRefineCategory('insect')} className="btn btn-secondary" style={{ padding: '4px 10px', fontSize: '0.75rem' }}>Insect</button>
                    </div>
                  </div>

                  {/* Hero Result Grid */}
                  <div className="hero-result-grid" style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '32px', alignItems: 'center' }}>
                    
                    {/* LEFT COLUMN: User Image */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{
                        position: 'relative',
                        borderRadius: 'var(--radius-md)',
                        overflow: 'hidden',
                        border: '1px solid var(--border-glass)',
                        boxShadow: 'var(--shadow-lg)'
                      }}>
                        {previewUrls[0] ? (
                          <img
                            src={previewUrls[0]}
                            alt="Uploaded observation"
                            style={{
                              width: '100%',
                              maxHeight: '340px',
                              minHeight: '200px',
                              objectFit: 'contain',
                              background: 'rgba(0, 0, 0, 0.4)',
                              display: 'block'
                            }}
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <div style={{ height: '200px', background: 'var(--bg-tertiary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                            No Photo Uploaded
                          </div>
                        )}
                        <div style={{
                          position: 'absolute',
                          bottom: 0,
                          left: 0,
                          right: 0,
                          background: 'linear-gradient(0deg, rgba(0,0,0,0.85) 0%, transparent 100%)',
                          padding: '12px 14px',
                          color: '#ffffff',
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          letterSpacing: '0.05em',
                          textTransform: 'uppercase',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '6px'
                        }}>
                          <ImageIcon size={14} color={currentTheme.accentColor} /> YOUR OBSERVATION PHOTO
                        </div>
                      </div>
                    </div>

                    {/* RIGHT COLUMN: SPECIES & ACTIONS */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      <div>
                        <span style={{ fontSize: '0.75rem', textTransform: 'uppercase', color: currentTheme.accentColor, fontWeight: 800, letterSpacing: '0.08em' }}>
                          {predictionResponse?.identification_status === 'LOW_CONFIDENCE'
                            ? 'Possible Species Identification (Low Confidence)'
                            : predictionResponse?.identification_status === 'AMBIGUOUS'
                            ? 'Ambiguous Species Identification'
                            : 'Primary Species Identification'}
                        </span>
                        <h1 style={{ fontSize: '2.4rem', fontWeight: 800, color: '#ffffff', margin: '4px 0 2px 0', lineHeight: 1.15 }}>
                          {topPrediction.common_names?.[0] || topPrediction.scientific_name}
                        </h1>
                        <div style={{ fontSize: '1.2rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>
                          {topPrediction.scientific_name}
                        </div>
                      </div>

                      {/* Confidence & Action Bar */}
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '16px',
                        padding: '14px 20px',
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderRadius: 'var(--radius-md)',
                        border: '1px solid var(--border-glass)',
                        flexWrap: 'wrap'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                          <div style={{ fontSize: '2.4rem', fontWeight: 800, color: currentTheme.accentColor, lineHeight: 1 }}>
                            {(topPrediction.confidence > 1 ? topPrediction.confidence : topPrediction.confidence * 100).toFixed(1)}%
                          </div>
                          <div>
                            <span className={`badge ${predictionResponse?.identification_status === 'HIGH_CONFIDENCE' ? 'badge-confirmed' : predictionResponse?.identification_status === 'MEDIUM_CONFIDENCE' ? 'badge-medium' : 'badge-low'}`}>
                              {predictionResponse?.identification_status === 'HIGH_CONFIDENCE' ? 'High Confidence' : predictionResponse?.identification_status === 'MEDIUM_CONFIDENCE' ? 'Medium Confidence' : predictionResponse?.identification_status === 'AMBIGUOUS' ? 'Ambiguous Match' : 'Possible Match'}
                            </span>
                          </div>
                        </div>

                        <div style={{ display: 'flex', items: 'center', gap: '10px' }}>
                          <button
                            className="btn btn-secondary"
                            onClick={() => {
                              setIsCollectionModalOpen(true);
                            }}
                            style={{ padding: '10px 16px', fontSize: '0.85rem' }}
                          >
                            <Plus size={16} /> Add to Collection
                          </button>
                          <button
                            className="btn btn-primary"
                            onClick={handleConfirmTop}
                            style={{ padding: '10px 20px', fontSize: '0.9rem', background: currentTheme.accentColor, borderColor: currentTheme.accentColor, color: '#000' }}
                          >
                            <Check size={18} /> Confirm Observation
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ABOUT THIS SPECIES SECTION */}
              <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <BookOpen size={20} color={currentTheme.accentColor} /> About This Species
                  </h3>
                  {speciesProfile?.sources && speciesProfile.sources.length > 0 && (
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                      Sources: {speciesProfile.sources.join(', ')}
                    </span>
                  )}
                </div>

                <div className="editorial-desc">
                  {speciesProfile?.description || "Information unavailable."}
                </div>
              </div>

              {/* SPECIES QUICK FACTS */}
              <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
                <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Species Quick Facts</h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
                  <div style={{ padding: '14px 18px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: currentTheme.accentColor, marginBottom: '4px' }}>🌿 Habitat</div>
                    <div style={{ fontSize: '0.92rem', color: facts?.habitat ? 'var(--text-main)' : 'var(--text-dim)' }}>
                      {facts?.habitat || "Information unavailable"}
                    </div>
                  </div>

                  <div style={{ padding: '14px 18px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--accent-secondary)', marginBottom: '4px' }}>🍃 Diet</div>
                    <div style={{ fontSize: '0.92rem', color: facts?.diet ? 'var(--text-main)' : 'var(--text-dim)' }}>
                      {facts?.diet || "Information unavailable"}
                    </div>
                  </div>

                  <div style={{ padding: '14px 18px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#60a5fa', marginBottom: '4px' }}>🐦 Behavior</div>
                    <div style={{ fontSize: '0.92rem', color: facts?.behavior ? 'var(--text-main)' : 'var(--text-dim)' }}>
                      {facts?.behavior || "Information unavailable"}
                    </div>
                  </div>

                  <div style={{ padding: '14px 18px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f472b6', marginBottom: '4px' }}>🪺 Reproduction</div>
                    <div style={{ fontSize: '0.92rem', color: facts?.reproduction ? 'var(--text-main)' : 'var(--text-dim)' }}>
                      {facts?.reproduction || "Information unavailable"}
                    </div>
                  </div>

                  <div style={{ padding: '14px 18px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)' }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f59e0b', marginBottom: '4px' }}>🛡 Conservation Status</div>
                    <div style={{ fontSize: '0.92rem', color: facts?.conservation ? 'var(--text-main)' : 'var(--text-dim)' }}>
                      {facts?.conservation || "Information unavailable"}
                    </div>
                  </div>
                </div>
              </div>

              {/* REFERENCE IMAGES GALLERY */}
              <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Reference Images</h3>
                    <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                      Authenticated web reference photographs of <em>{topPrediction?.scientific_name}</em>
                    </p>
                  </div>
                  <span className="badge" style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-muted)' }}>
                    {speciesProfile?.reference_images?.length || 0} Images
                  </span>
                </div>

                {speciesProfile?.reference_images?.length > 0 ? (
                  <div className="ref-gallery-carousel">
                    {speciesProfile.reference_images.map((img, idx) => (
                      <div key={idx} className="ref-gallery-card" style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        <img
                          src={img.url}
                          alt={`Reference ${idx + 1}`}
                          style={{
                            width: '100%',
                            height: '160px',
                            objectFit: 'contain',
                            background: 'rgba(0, 0, 0, 0.4)',
                            borderRadius: 'var(--radius-sm)'
                          }}
                          onError={(e) => {
                            e.currentTarget.onerror = null;
                            e.currentTarget.style.display = 'none';
                          }}
                        />
                        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <div><strong>Photo:</strong> {img.creator || 'Unknown'}</div>
                          <div><strong>Source:</strong> {img.source || 'GBIF / Wikimedia'}</div>
                          {img.license && (
                            <span className="badge" style={{ width: 'fit-content', marginTop: '4px', fontSize: '0.65rem' }}>
                              {img.license}
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div style={{ padding: '24px', textAlign: 'center', color: 'var(--text-dim)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                    Additional reference images are currently unavailable for this species.
                  </div>
                )}
              </div>

              {/* TAXONOMIC HIERARCHY */}
              <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Taxonomic Hierarchy</h3>

                <div className="taxonomy-flow">
                  <div className="taxonomy-item"><span>Kingdom:</span> <strong>{taxonomy?.kingdom || 'Animalia'}</strong></div>
                  <ChevronRight size={14} color="var(--text-dim)" />
                  <div className="taxonomy-item"><span>Phylum:</span> <strong>{taxonomy?.phylum || 'Chordata'}</strong></div>
                  <ChevronRight size={14} color="var(--text-dim)" />
                  <div className="taxonomy-item"><span>Class:</span> <strong>{taxonomy?.class || taxonomy?.class_name || 'Aves'}</strong></div>
                  <ChevronRight size={14} color="var(--text-dim)" />
                  <div className="taxonomy-item"><span>Order:</span> <strong>{taxonomy?.order || '—'}</strong></div>
                  <ChevronRight size={14} color="var(--text-dim)" />
                  <div className="taxonomy-item"><span>Family:</span> <strong>{taxonomy?.family || '—'}</strong></div>
                  <ChevronRight size={14} color="var(--text-dim)" />
                  <div className="taxonomy-item"><span>Genus:</span> <strong>{taxonomy?.genus || '—'}</strong></div>
                  <ChevronRight size={14} color="var(--text-dim)" />
                  <div className="taxonomy-item" style={{ borderColor: currentTheme.accentColor, background: currentTheme.bgColor }}>
                    <span>Species:</span> <strong style={{ color: currentTheme.accentColor, fontStyle: 'italic' }}>{topPrediction?.scientific_name}</strong>
                  </div>
                </div>
              </div>

              {/* OTHER POSSIBILITIES */}
              {predictionResponse?.predictions?.length > 1 && (
                <div className="glass-panel" style={{ padding: '28px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Other Possibilities</h3>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {predictionResponse.predictions.slice(1).map((pred) => (
                      <div
                        key={pred.rank}
                        style={{
                          padding: '12px 16px',
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--border-glass)',
                          borderRadius: 'var(--radius-sm)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center'
                        }}
                      >
                        <div>
                          <strong style={{ color: '#ffffff', fontSize: '0.95rem' }}>{pred.common_names?.[0] || pred.scientific_name}</strong>
                          <span style={{ fontStyle: 'italic', color: 'var(--text-muted)', marginLeft: '10px', fontSize: '0.85rem' }}>
                            ({pred.scientific_name})
                          </span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                          <span style={{ fontWeight: 700, color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                            {(pred.confidence > 1 ? pred.confidence : pred.confidence * 100).toFixed(1)}%
                          </span>
                          <button
                            className="btn btn-secondary"
                            style={{ padding: '5px 12px', fontSize: '0.8rem' }}
                            onClick={() => handleSelectAlternative(pred)}
                          >
                            Select
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* ACTIONS */}
              <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
                <button className="btn btn-secondary" onClick={() => setShowManualSearch(true)}>
                  <Search size={18} /> Search Different Species Manually
                </button>
                <button className="btn btn-secondary" onClick={() => setStep(2)}>
                  <RefreshCw size={18} /> Upload Another Image
                </button>
              </div>
            </>
          )}

          {/* Manual Search Modal */}
          {showManualSearch && (
            <div style={{
              position: 'fixed',
              inset: 0,
              background: 'rgba(0, 0, 0, 0.8)',
              backdropFilter: 'blur(10px)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 2000,
              padding: '20px'
            }}>
              <div className="glass-panel" style={{ width: '100%', maxWidth: '520px', padding: '28px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '18px' }}>
                  <h3 style={{ fontSize: '1.2rem' }}>Manual Species Lookup</h3>
                  <button onClick={() => setShowManualSearch(false)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}><X size={20} /></button>
                </div>

                <div style={{ display: 'flex', gap: '10px', marginBottom: '18px' }}>
                  <input
                    type="text"
                    placeholder="Search scientific or common name..."
                    value={manualQuery}
                    onChange={(e) => setManualQuery(e.target.value)}
                    style={{ flex: 1, padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--bg-tertiary)', color: '#fff', border: '1px solid var(--border-glass)' }}
                  />
                  <button className="btn btn-primary" onClick={handleManualSearch}>Search</button>
                </div>

                <div style={{ maxHeight: '280px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {manualResults.map((sp) => (
                    <div key={sp.id} onClick={() => handleSelectManual(sp)} style={{ padding: '12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-sm)', cursor: 'pointer' }}>
                      <strong style={{ color: '#fff' }}>{sp.common_name || sp.scientific_name}</strong>
                      <div style={{ fontSize: '0.8rem', fontStyle: 'italic', color: 'var(--text-muted)' }}>{sp.scientific_name}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* STEP 4: Location & Notes */}
      {step === 4 && (
        <div className="glass-panel" style={{ padding: '36px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800 }}>Confirm Observation Log</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '2px' }}>
              Finalizing record for: <strong>{selectedSpecies?.common_name || selectedSpecies?.scientific_name}</strong> (<em>{selectedSpecies?.scientific_name}</em>)
            </p>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* LOCATION SECTION */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div>
                <label style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-main)', display: 'block' }}>
                  Location
                </label>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                  Choose how you want to record where this observation was made.
                </p>
              </div>

              {/* Mode Selection Buttons */}
              <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
                <button
                  type="button"
                  onClick={() => {
                    setLocationMode('live');
                    if (!geoSuccess && !geoLoading && !latitude) {
                      handleDetectLiveLocation();
                    }
                  }}
                  className={locationMode === 'live' ? 'btn btn-primary' : 'btn btn-secondary'}
                  style={{
                    flex: '1 1 200px',
                    padding: '12px 18px',
                    fontSize: '0.88rem',
                    justifyContent: 'center',
                    border: locationMode === 'live' ? '1px solid var(--accent-primary)' : '1px solid var(--border-glass)',
                    background: locationMode === 'live' ? 'var(--color-plant-bg)' : 'var(--bg-tertiary)',
                    color: locationMode === 'live' ? 'var(--accent-primary)' : 'var(--text-main)',
                    fontWeight: 700
                  }}
                >
                  <MapPin size={18} /> Use Live Location {locationMode === 'live' && '✓'}
                </button>

                <button
                  type="button"
                  onClick={() => setLocationMode('manual')}
                  className={locationMode === 'manual' ? 'btn btn-primary' : 'btn btn-secondary'}
                  style={{
                    flex: '1 1 200px',
                    padding: '12px 18px',
                    fontSize: '0.88rem',
                    justifyContent: 'center',
                    border: locationMode === 'manual' ? '1px solid var(--accent-primary)' : '1px solid var(--border-glass)',
                    background: locationMode === 'manual' ? 'var(--color-plant-bg)' : 'var(--bg-tertiary)',
                    color: locationMode === 'manual' ? 'var(--accent-primary)' : 'var(--text-main)',
                    fontWeight: 700
                  }}
                >
                  ✍️ Enter Location Manually {locationMode === 'manual' && '✓'}
                </button>
              </div>

              {/* Live Location Panel */}
              {locationMode === 'live' && (
                <div style={{ padding: '16px 20px', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {geoLoading ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--text-muted)', fontSize: '0.88rem' }}>
                      <Loader2 className="animate-spin" size={18} color="var(--accent-primary)" />
                      <span>Detecting location...</span>
                    </div>
                  ) : geoError ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontSize: '0.85rem', fontWeight: 600 }}>
                        <AlertTriangle size={16} color="#ef4444" />
                        <span>{geoError}</span>
                      </div>
                      <button
                        type="button"
                        onClick={handleDetectLiveLocation}
                        style={{ width: 'fit-content', background: 'none', border: 'none', color: 'var(--accent-primary)', textDecoration: 'underline', fontSize: '0.78rem', cursor: 'pointer', padding: 0 }}
                      >
                        Try detecting live location again
                      </button>
                    </div>
                  ) : latitude && longitude ? (
                    <div>
                      <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--accent-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <MapPin size={16} /> 📍 Location detected
                      </div>
                      <div style={{ fontSize: '0.82rem', color: 'var(--text-muted)', marginTop: '4px' }}>
                        Latitude: {latitude.toFixed(4)} &nbsp;|&nbsp; Longitude: {longitude.toFixed(4)}
                      </div>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '10px' }}>
                      <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>No location detected yet.</span>
                      <button
                        type="button"
                        onClick={handleDetectLiveLocation}
                        className="btn btn-secondary"
                        style={{ padding: '6px 14px', fontSize: '0.78rem' }}
                      >
                        <MapPin size={14} /> Detect Location Now
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Manual Location Input Panel */}
              {locationMode === 'manual' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                  <input
                    type="text"
                    placeholder="Enter location, place, campus, park, etc. (e.g., Botanical Garden, Western Ghats)"
                    value={manualLocation}
                    onChange={(e) => setManualLocation(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '12px 14px',
                      borderRadius: 'var(--radius-sm)',
                      background: 'var(--bg-tertiary)',
                      color: '#ffffff',
                      border: '1px solid var(--border-glass)',
                      fontSize: '0.9rem'
                    }}
                  />
                </div>
              )}
            </div>

            {/* FIELD NOTES */}
            <div>
              <label style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>
                Field Notes & Habitat Observations
              </label>
              <textarea
                rows={3}
                placeholder="Enter field notes, ambient weather, specimen conditions..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--bg-tertiary)',
                  color: '#ffffff',
                  border: '1px solid var(--border-glass)',
                  fontSize: '0.9rem'
                }}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '12px' }}>
            <button className="btn btn-secondary" onClick={() => setStep(3)}>Back to Review</button>
            <button className="btn btn-primary" onClick={handleSubmitObservation} disabled={loading}>
              {loading ? 'Saving Record...' : 'Save Observation Record'}
            </button>
          </div>
        </div>
      )}

      {/* STEP 5: Success Confirmation */}
      {step === 5 && (
        <div className="glass-panel" style={{ padding: '48px 36px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px' }}>
          <div style={{ width: '64px', height: '64px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Check size={36} color="#10b981" />
          </div>
          <h2 style={{ fontSize: '1.8rem', fontWeight: 800 }}>Observation Successfully Saved!</h2>
          <p style={{ color: 'var(--text-muted)', maxWidth: '480px' }}>
            Your biodiversity observation record for <strong>{selectedSpecies?.common_name || selectedSpecies?.scientific_name}</strong> has been saved.
          </p>

          <div style={{ display: 'flex', gap: '14px', marginTop: '12px', flexWrap: 'wrap', justifyContent: 'center' }}>
            <button
              className="btn btn-primary"
              onClick={() => setIsCollectionModalOpen(true)}
              style={{ padding: '12px 20px', background: '#10b981', borderColor: '#10b981', color: '#fff' }}
            >
              <Plus size={18} /> Add to Collection
            </button>
            <button className="btn btn-secondary" onClick={resetWizardState}>
              <RefreshCw size={18} /> Record Another Observation
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/species')}>
              <BookOpen size={18} /> View in Species Explorer
            </button>
          </div>
        </div>
      )}

      {/* Collection Modal Popup */}
      <CollectionModal
        isOpen={isCollectionModalOpen}
        onClose={() => setIsCollectionModalOpen(false)}
        mode="add_item"
        itemToAdd={{
          item_type: 'observation',
          scientific_name: selectedSpecies?.scientific_name || topPrediction?.scientific_name || 'Unknown',
          common_name: selectedSpecies?.common_name || topPrediction?.common_names?.[0] || '',
          category: category,
          observation_id: savedObservationId
        }}
        onSuccess={() => {
          alert('Observation successfully added to your collection!');
        }}
      />
    </div>
  );
}
