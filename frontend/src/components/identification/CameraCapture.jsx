import React, { useState, useRef, useEffect } from 'react';
import { Camera, RefreshCw, Check, X, SwitchCamera, AlertTriangle, Image as ImageIcon } from 'lucide-react';

export default function CameraCapture({ onCapture, onCancel, onSwitchToUpload }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const [stream, setStream] = useState(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [capturedBlob, setCapturedBlob] = useState(null);
  const [error, setError] = useState(null);
  const [facingMode, setFacingMode] = useState('environment'); // Default to rear camera for field observations
  const [hasMultipleCameras, setHasMultipleCameras] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // Check available camera devices
  useEffect(() => {
    async function checkDevices() {
      if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
        try {
          const devices = await navigator.mediaDevices.enumerateDevices();
          const videoInputCount = devices.filter((d) => d.kind === 'videoinput').length;
          setHasMultipleCameras(videoInputCount > 1);
        } catch (e) {
          console.warn('Could not enumerate media devices:', e);
        }
      }
    }
    checkDevices();
  }, []);

  // Start camera stream
  const startCamera = async (mode = facingMode) => {
    setIsLoading(true);
    setError(null);

    // Stop any existing stream
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Camera API is not supported in this browser. You can upload an image instead.');
      setIsLoading(false);
      return;
    }

    try {
      const constraints = {
        video: {
          facingMode: { ideal: mode },
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        }
      };

      let newStream;
      try {
        newStream = await navigator.mediaDevices.getUserMedia(constraints);
      } catch (idealErr) {
        // Fallback to basic video constraint if ideal facingMode fails
        newStream = await navigator.mediaDevices.getUserMedia({ video: true });
      }

      setStream(newStream);

      if (videoRef.current) {
        videoRef.current.srcObject = newStream;
        await videoRef.current.play();
      }
      setIsLoading(false);
    } catch (err) {
      console.error('Camera access error:', err);
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setError('Camera permission was denied. You can upload an image from your gallery instead.');
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setError('No camera device found. You can upload an image instead.');
      } else {
        setError('Camera unavailable. You can upload an image instead.');
      }
      setIsLoading(false);
    }
  };

  // Start camera on component mount
  useEffect(() => {
    startCamera(facingMode);

    return () => {
      // Cleanup stream on component unmount
      if (stream) {
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, [facingMode]);

  // Stop camera tracks
  const stopCameraStream = () => {
    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }
  };

  // Flip between front and rear cameras
  const toggleCamera = () => {
    const newMode = facingMode === 'environment' ? 'user' : 'environment';
    setFacingMode(newMode);
  };

  // Capture photo snapshot
  const handleCapture = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (!video || !canvas) return;

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, width, height);

    // Convert canvas to high-quality JPEG Blob
    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setError('Failed to capture photo frame.');
          return;
        }
        const previewUrl = URL.createObjectURL(blob);
        setCapturedBlob(blob);
        setCapturedImage(previewUrl);

        // Pause stream during review
        stopCameraStream();
      },
      'image/jpeg',
      0.92
    );
  };

  // Retake photo
  const handleRetake = () => {
    if (capturedImage) {
      URL.revokeObjectURL(capturedImage);
    }
    setCapturedImage(null);
    setCapturedBlob(null);
    startCamera(facingMode);
  };

  // Accept photo and pass File back to parent
  const handleAccept = () => {
    if (!capturedBlob) return;

    const fileName = `camera_photo_${Date.now()}.jpg`;
    const capturedFile = new File([capturedBlob], fileName, { type: 'image/jpeg' });

    stopCameraStream();
    onCapture(capturedFile);
  };

  const handleCancelClick = () => {
    stopCameraStream();
    if (onCancel) onCancel();
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        maxWidth: '650px',
        margin: '0 auto',
        borderRadius: 'var(--radius-lg)'
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Camera size={22} color="var(--accent-primary)" />
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700 }}>Mobile Camera Capture</h3>
        </div>
        <button
          onClick={handleCancelClick}
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

      {/* Hidden canvas for image snapshot */}
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Error State */}
      {error ? (
        <div
          style={{
            padding: '24px',
            borderRadius: 'var(--radius-md)',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '16px',
            textAlign: 'center'
          }}
        >
          <AlertTriangle size={36} color="#ef4444" />
          <div>
            <h4 style={{ fontSize: '1rem', fontWeight: 700, color: '#fca5a5', marginBottom: '6px' }}>
              Camera Unavailable
            </h4>
            <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)' }}>{error}</p>
          </div>
          <button className="btn btn-primary" onClick={onSwitchToUpload}>
            <ImageIcon size={18} />
            <span>Upload Image from Gallery</span>
          </button>
        </div>
      ) : capturedImage ? (
        /* Captured Photo Preview Mode */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
          <div
            style={{
              position: 'relative',
              width: '100%',
              maxHeight: '400px',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              background: '#000'
            }}
          >
            <img
              src={capturedImage}
              alt="Captured observation"
              style={{ width: '100%', height: '100%', objectFit: 'contain', maxHeight: '400px' }}
            />
          </div>

          <div style={{ display: 'flex', gap: '16px', width: '100%', justifyContent: 'center' }}>
            <button className="btn btn-secondary" onClick={handleRetake} style={{ flex: 1 }}>
              <RefreshCw size={18} />
              <span>Retake Photo</span>
            </button>
            <button className="btn btn-primary" onClick={handleAccept} style={{ flex: 1 }}>
              <Check size={18} />
              <span>Use Photo</span>
            </button>
          </div>
        </div>
      ) : (
        /* Live Camera Video Mode */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', alignItems: 'center' }}>
          <div
            style={{
              position: 'relative',
              width: '100%',
              height: '350px',
              borderRadius: 'var(--radius-md)',
              overflow: 'hidden',
              background: '#000000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover'
              }}
            />

            {isLoading && (
              <div
                style={{
                  position: 'absolute',
                  color: 'var(--text-muted)',
                  fontSize: '0.9rem',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <RefreshCw className="spin" size={20} />
                <span>Starting camera...</span>
              </div>
            )}

            {/* Flip camera button overlay */}
            {hasMultipleCameras && !isLoading && (
              <button
                onClick={toggleCamera}
                title="Switch Camera"
                style={{
                  position: 'absolute',
                  top: '12px',
                  right: '12px',
                  background: 'rgba(0, 0, 0, 0.6)',
                  backdropFilter: 'blur(4px)',
                  color: '#ffffff',
                  border: '1px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '50%',
                  width: '42px',
                  height: '42px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer'
                }}
              >
                <SwitchCamera size={20} />
              </button>
            )}
          </div>

          <div style={{ display: 'flex', gap: '16px', width: '100%' }}>
            <button className="btn btn-secondary" onClick={onSwitchToUpload} style={{ flex: 1 }}>
              <ImageIcon size={18} />
              <span>Upload from Gallery</span>
            </button>
            <button className="btn btn-primary" onClick={handleCapture} disabled={isLoading} style={{ flex: 1.5 }}>
              <Camera size={20} />
              <span>Capture Photo</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
