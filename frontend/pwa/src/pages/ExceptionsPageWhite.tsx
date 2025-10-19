/**
 * ExceptionsPage - White Enterprise Theme
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Input, Select, message } from 'antd';
import { ArrowLeft, AlertTriangle } from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { whiteTheme } from '../theme-white';
import client from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';
import { useTranslation } from '../hooks/useTranslation';

const ExceptionsPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [exceptionType, setExceptionType] = useState<string>('shortage');
  const [sku, setSku] = useState<string>('');
  const [location, setLocation] = useState<string>('');
  const [description, setDescription] = useState<string>('');

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    networkManager.addListener(handleNetworkChange);
    return () => networkManager.removeListener(handleNetworkChange);
  }, []);

  const submitExceptionMutation = useMutation({
    mutationFn: async (payload: any) => client.post('/exceptions', payload),
    onSuccess: () => {
      message.success('Exception reported');
      setSku('');
      setLocation('');
      setDescription('');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Error');
    },
  });

  const handleSubmit = () => {
    if (!sku.trim() || !description.trim()) {
      message.error('SKU and description required');
      return;
    }

    const payload = {
      type: exceptionType,
      sku: sku.trim(),
      location: location.trim() || undefined,
      description: description.trim(),
      operation_id: `exception-${Date.now()}`,
    };

    if (networkManager.isConnected()) {
      submitExceptionMutation.mutate(payload);
    } else {
      offlineQueue.addAction('exception' as any, sku, payload);
      message.info('Offline - queued');
      setSku('');
      setLocation('');
      setDescription('');
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: whiteTheme.colors.background }}>
      <div
        style={{
          background: whiteTheme.colors.cardBackground,
          borderBottom: `1px solid ${whiteTheme.colors.border}`,
          padding: whiteTheme.spacing.lg,
          boxShadow: whiteTheme.shadows.sm,
        }}
      >
        <button onClick={() => navigate('/')} className="wms-btn wms-btn-secondary" style={{ marginBottom: whiteTheme.spacing.md }}>
          <ArrowLeft size={16} /> Home
        </button>
        <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0, display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.sm }}>
          <AlertTriangle size={28} color={whiteTheme.colors.warning} /> Exceptions
        </h1>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        <div className="wms-card">
          <div style={{ marginBottom: whiteTheme.spacing.lg }}>
            <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
              Exception Type
            </label>
            <Select
              size="large"
              value={exceptionType}
              onChange={setExceptionType}
              style={{ width: '100%' }}
              options={[
                { value: 'shortage', label: 'Shortage' },
                { value: 'damage', label: 'Damage' },
                { value: 'mismatch', label: 'Mismatch' },
                { value: 'other', label: 'Other' },
              ]}
            />
          </div>

          <div style={{ marginBottom: whiteTheme.spacing.lg }}>
            <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
              SKU *
            </label>
            <Input size="large" placeholder="Enter SKU" value={sku} onChange={(e) => setSku(e.target.value)} />
          </div>

          <div style={{ marginBottom: whiteTheme.spacing.lg }}>
            <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
              Location (Optional)
            </label>
            <Input size="large" placeholder="e.g. A-01-01" value={location} onChange={(e) => setLocation(e.target.value)} />
          </div>

          <div style={{ marginBottom: whiteTheme.spacing.lg }}>
            <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
              Description *
            </label>
            <Input.TextArea placeholder="Describe the issue..." value={description} onChange={(e) => setDescription(e.target.value)} rows={4} />
          </div>

          <Button
            type="primary"
            size="large"
            block
            onClick={handleSubmit}
            loading={submitExceptionMutation.isPending}
          >
            Submit Exception
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ExceptionsPageWhite;

