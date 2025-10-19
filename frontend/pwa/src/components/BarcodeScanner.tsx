/**
 * BarcodeScanner - Camera-based barcode scanning component
 * 
 * Features:
 * - Uses device camera with getUserMedia
 * - Real barcode scanning via ZXing library
 * - Fallback to manual entry if permission denied
 * - Haptic feedback on scan
 * - Support for multiple barcode formats (EAN, UPC, Code128, QR, etc.)
 */

import React, { useEffect, useRef, useState } from 'react';
import { Modal, Button, message } from 'antd';
import { CameraOutlined, CloseOutlined, EditOutlined } from '@ant-design/icons';
import { BrowserMultiFormatReader, NotFoundException } from '@zxing/library';
import { whiteTheme } from '../theme-white';
import { useTranslation } from '../hooks/useTranslation';

interface BarcodeScannerProps {
  visible: boolean;
  onScan: (barcode: string) => void;
  onCancel: () => void;
  title?: string;
}

const BarcodeScanner: React.FC<BarcodeScannerProps> = ({
  visible,
  onScan,
  onCancel,
  title = 'Scan Barcode',
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [manualMode, setManualMode] = useState(false);
  const [manualInput, setManualInput] = useState('');
  const streamRef = useRef<MediaStream | null>(null);
  const codeReaderRef = useRef<BrowserMultiFormatReader | null>(null);
  const [scanning, setScanning] = useState(false);

  useEffect(() => {
    if (visible && !manualMode) {
      startCamera();
    }

    return () => {
      stopCamera();
    };
  }, [visible, manualMode]);

  const startCamera = async () => {
    try {
      setScanning(true);
      setCameraError(null);

      // Initialize ZXing code reader
      const codeReader = new BrowserMultiFormatReader();
      codeReaderRef.current = codeReader;

      // Get available video devices
      const videoInputDevices = await codeReader.listVideoInputDevices();
      
      // Prefer back camera (environment facing)
      const backCamera = videoInputDevices.find(device => 
        device.label.toLowerCase().includes('back') || 
        device.label.toLowerCase().includes('rear') ||
        device.label.toLowerCase().includes('environment')
      );
      
      const selectedDeviceId = backCamera?.deviceId || videoInputDevices[0]?.deviceId;

      if (!selectedDeviceId) {
        throw new Error('No camera found');
      }

      // Start decoding from video device
      await codeReader.decodeFromVideoDevice(
        selectedDeviceId,
        videoRef.current!,
        (result, error) => {
          if (result) {
            // Barcode detected!
            const barcode = result.getText();
            console.log('Barcode scanned:', barcode);
            
            // Haptic feedback
            if ('vibrate' in navigator) {
              navigator.vibrate([100, 50, 100]);
            }

            // Stop scanning and return result
            stopCamera();
            onScan(barcode);
          }

          if (error && !(error instanceof NotFoundException)) {
            console.error('Scanning error:', error);
          }
        }
      );

      setCameraActive(true);
      setScanning(true);

      // Initial haptic feedback
      if ('vibrate' in navigator) {
        navigator.vibrate(50);
      }
    } catch (error: any) {
      console.error('Camera access error:', error);
      setCameraError(error.message || 'Camera access denied');
      setManualMode(true);
      setScanning(false);
      message.warning('Camera not available - switching to manual entry');
    }
  };

  const stopCamera = () => {
    if (codeReaderRef.current) {
      codeReaderRef.current.reset();
      codeReaderRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
    setScanning(false);
  };

  const handleManualSubmit = () => {
    if (manualInput.trim()) {
      onScan(manualInput.trim());
      setManualInput('');
      
      // Haptic feedback
      if ('vibrate' in navigator) {
        navigator.vibrate([50, 100, 50]);
      }
    } else {
      message.error('Please enter a barcode');
    }
  };

  const handleCancel = () => {
    stopCamera();
    setManualInput('');
    setCameraError(null);
    setManualMode(false);
    onCancel();
  };

  // Manual scan trigger (for testing)
  const simulateScan = (code: string) => {
    stopCamera();
    onScan(code);
    
    // Haptic feedback
    if ('vibrate' in navigator) {
      navigator.vibrate([50, 100, 50]);
    }
  };

  return (
    <Modal
      open={visible}
      title={title}
      onCancel={handleCancel}
      footer={null}
      width="100%"
      style={{ maxWidth: '600px', top: 20 }}
      styles={{
        body: {
          background: whiteTheme.colors.background,
          padding: 0,
        },
      }}
    >
      {manualMode || cameraError ? (
        // Manual Entry Mode
        <div style={{ padding: whiteTheme.spacing.lg }}>
          <div
            style={{
              marginBottom: whiteTheme.spacing.lg,
              padding: whiteTheme.spacing.md,
              background: whiteTheme.colors.cardBackground,
              borderRadius: whiteTheme.borderRadius.md,
              border: `1px solid ${whiteTheme.colors.border}`,
            }}
          >
            <div style={{ color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
              <EditOutlined style={{ marginRight: whiteTheme.spacing.sm }} />
              Manual Entry Mode
            </div>
            {cameraError && (
              <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.sm }}>
                {cameraError}
              </div>
            )}
          </div>

          <input
            type="text"
            placeholder="Enter barcode manually"
            value={manualInput}
            onChange={(e) => setManualInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleManualSubmit();
              }
            }}
            autoFocus
            style={{
              width: '100%',
              padding: whiteTheme.spacing.md,
              fontSize: whiteTheme.typography.sizes.lg,
              background: whiteTheme.colors.cardBackground,
              border: `1px solid ${whiteTheme.colors.border}`,
              borderRadius: whiteTheme.borderRadius.md,
              color: whiteTheme.colors.text,
              marginBottom: whiteTheme.spacing.md,
            }}
          />

          <div style={{ display: 'flex', gap: whiteTheme.spacing.sm }}>
            <Button size="large" onClick={handleCancel} style={{ flex: 1 }}>
              {t('common.cancel')}
            </Button>
            <Button
              type="primary"
              size="large"
              onClick={handleManualSubmit}
              style={{ flex: 1 }}
            >
              {t('common.confirm')}
            </Button>
          </div>

          {!cameraError && (
            <Button
              type="link"
              onClick={() => {
                setManualMode(false);
                setCameraError(null);
              }}
              style={{ marginTop: whiteTheme.spacing.md, width: '100%' }}
            >
              <CameraOutlined /> Try camera again
            </Button>
          )}
        </div>
      ) : (
        // Camera Mode
        <div
          style={{
            position: 'relative',
            width: '100%',
            paddingTop: '75%', // 4:3 aspect ratio
            background: '#000',
            borderRadius: whiteTheme.borderRadius.md,
            overflow: 'hidden',
          }}
        >
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
          />

          {/* Scanning Reticle */}
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '80%',
              height: '40%',
              border: `2px solid ${whiteTheme.colors.accent}`,
              borderRadius: whiteTheme.borderRadius.md,
              boxShadow: `0 0 0 9999px rgba(0, 0, 0, 0.5)`,
            }}
          >
            <div
              style={{
                position: 'absolute',
                top: '-2px',
                left: '-2px',
                width: '20px',
                height: '20px',
                borderTop: `4px solid ${whiteTheme.colors.accent}`,
                borderLeft: `4px solid ${whiteTheme.colors.accent}`,
              }}
            />
            <div
              style={{
                position: 'absolute',
                top: '-2px',
                right: '-2px',
                width: '20px',
                height: '20px',
                borderTop: `4px solid ${whiteTheme.colors.accent}`,
                borderRight: `4px solid ${whiteTheme.colors.accent}`,
              }}
            />
            <div
              style={{
                position: 'absolute',
                bottom: '-2px',
                left: '-2px',
                width: '20px',
                height: '20px',
                borderBottom: `4px solid ${whiteTheme.colors.accent}`,
                borderLeft: `4px solid ${whiteTheme.colors.accent}`,
              }}
            />
            <div
              style={{
                position: 'absolute',
                bottom: '-2px',
                right: '-2px',
                width: '20px',
                height: '20px',
                borderBottom: `4px solid ${whiteTheme.colors.accent}`,
                borderRight: `4px solid ${whiteTheme.colors.accent}`,
              }}
            />
          </div>

          {/* Instructions */}
          <div
            style={{
              position: 'absolute',
              bottom: whiteTheme.spacing.lg,
              left: '50%',
              transform: 'translateX(-50%)',
              color: 'white',
              textAlign: 'center',
              background: 'rgba(0, 0, 0, 0.7)',
              padding: `${whiteTheme.spacing.sm} ${whiteTheme.spacing.lg}`,
              borderRadius: whiteTheme.borderRadius.md,
              fontSize: whiteTheme.typography.sizes.sm,
              whiteSpace: 'nowrap',
            }}
          >
            {scanning ? 'Scanning... Position barcode in frame' : 'Initializing camera...'}
          </div>

          {/* Manual Entry Button */}
          <Button
            type="primary"
            icon={<EditOutlined />}
            onClick={() => setManualMode(true)}
            style={{
              position: 'absolute',
              top: whiteTheme.spacing.md,
              right: whiteTheme.spacing.md,
            }}
          >
            Manual
          </Button>

          {/* Close Button */}
          <Button
            type="text"
            icon={<CloseOutlined />}
            onClick={handleCancel}
            style={{
              position: 'absolute',
              top: whiteTheme.spacing.md,
              left: whiteTheme.spacing.md,
              color: 'white',
            }}
          />

          {/* Demo: Simulate Scan Button (remove in production) */}
          <Button
            type="primary"
            onClick={() => simulateScan('1234567890123')}
            style={{
              position: 'absolute',
              bottom: whiteTheme.spacing.xl,
              left: '50%',
              transform: 'translateX(-50%)',
            }}
          >
            [DEMO] Simulate Scan
          </Button>
        </div>
      )}
    </Modal>
  );
};

export default BarcodeScanner;

