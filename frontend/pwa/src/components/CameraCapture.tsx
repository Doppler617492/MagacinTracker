/**
 * Camera Capture Component for Photo Attachments
 * Manhattan Active WMS - Receiving photo documentation
 * Optimized for Zebra TC21/MC3300 devices
 */

import React, { useRef, useState, useEffect } from 'react';
import { Modal, Button, Space, Alert } from 'antd';
import { 
  CameraOutlined, 
  DeleteOutlined, 
  CheckOutlined,
  ReloadOutlined 
} from '@ant-design/icons';
import { sr } from '../i18n/sr-comprehensive';
import './CameraCapture.css';

interface CameraCaptureProps {
  visible: boolean;
  onCapture: (base64Data: string, filename: string) => void;
  onCancel: () => void;
}

export const CameraCapture: React.FC<CameraCaptureProps> = ({
  visible,
  onCapture,
  onCancel,
}) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Open camera when modal becomes visible
  useEffect(() => {
    if (visible && !stream && !capturedPhoto) {
      openCamera();
    }
    
    return () => {
      if (stream) {
        closeCamera();
      }
    };
  }, [visible]);

  const openCamera = async () => {
    try {
      setError(null);
      
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: 'environment',  // Rear camera (Zebra scanner side)
          width: { ideal: 1280 },
          height: { ideal: 720 },
        }
      });
      
      setStream(mediaStream);
      
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }
    } catch (err) {
      console.error('Camera access error:', err);
      setError('Nije moguće pristupiti kameri. Provjerite dozvole.');
    }
  };

  const closeCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    // Set canvas dimensions to match video
    canvas.width = 1280;
    canvas.height = 720;
    
    const context = canvas.getContext('2d');
    if (!context) return;

    // Draw video frame to canvas
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert to base64 JPEG (0.8 quality for smaller file size)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    
    setCapturedPhoto(dataUrl);
    closeCamera();
  };

  const retakePhoto = () => {
    setCapturedPhoto(null);
    setError(null);
    openCamera();
  };

  const confirmPhoto = () => {
    if (!capturedPhoto) return;
    
    const filename = `receiving-photo-${Date.now()}.jpg`;
    onCapture(capturedPhoto, filename);
    
    // Reset state
    setCapturedPhoto(null);
    setError(null);
  };

  const handleCancel = () => {
    closeCamera();
    setCapturedPhoto(null);
    setError(null);
    onCancel();
  };

  return (
    <Modal
      title="Dodaj fotografiju"
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={800}
      className="camera-capture-modal"
      centered
    >
      <div className="camera-capture">
        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        {!capturedPhoto ? (
          // Camera View
          <div className="camera-capture__view">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="camera-capture__video"
            />
            
            <div className="camera-capture__controls">
              <Button
                type="primary"
                size="large"
                icon={<CameraOutlined />}
                onClick={capturePhoto}
                disabled={!stream}
                className="camera-capture__button camera-capture__button--capture"
              >
                Slikaj
              </Button>
            </div>
          </div>
        ) : (
          // Photo Preview
          <div className="camera-capture__preview">
            <img
              src={capturedPhoto}
              alt="Captured photo"
              className="camera-capture__image"
            />
            
            <div className="camera-capture__actions">
              <Space size="large">
                <Button
                  size="large"
                  icon={<ReloadOutlined />}
                  onClick={retakePhoto}
                  className="camera-capture__button"
                >
                  Ponovo
                </Button>
                <Button
                  type="primary"
                  size="large"
                  icon={<CheckOutlined />}
                  onClick={confirmPhoto}
                  className="camera-capture__button camera-capture__button--confirm"
                >
                  Potvrdi
                </Button>
              </Space>
            </div>
          </div>
        )}

        {/* Hidden canvas for photo capture */}
        <canvas ref={canvasRef} style={{ display: 'none' }} />
      </div>
    </Modal>
  );
};

export default CameraCapture;

