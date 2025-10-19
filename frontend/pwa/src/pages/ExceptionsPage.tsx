/**
 * ExceptionsPage - Quick forms for reporting exceptions
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Input, Select, message, Card } from 'antd';
import { ArrowLeftOutlined, WarningOutlined, CameraOutlined } from '@ant-design/icons';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { theme } from '../theme';
import { t } from '../i18n/translations';
import HeaderStatusBar from '../components/HeaderStatusBar';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';

const ExceptionsPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? 'Warehouse'
  );

  const [exceptionType, setExceptionType] = useState<string>('shortage');
  const [sku, setSku] = useState<string>('');
  const [location, setLocation] = useState<string>('');
  const [description, setDescription] = useState<string>('');

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    const handleQueue = (state: OfflineQueueState) => {
      setPendingSync(state.pending);
      setLastSyncedAt(state.lastSyncedAt);
    };
    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueue);
    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueue);
    };
  }, []);

  const submitExceptionMutation = useMutation({
    mutationFn: async (payload: any) => {
      return client.post('/exceptions', payload);
    },
    onSuccess: () => {
      message.success('Exception reported successfully');
      setSku('');
      setLocation('');
      setDescription('');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Error reporting exception');
    },
  });

  const handleSubmit = () => {
    if (!sku.trim() || !description.trim()) {
      message.error('SKU and description are required');
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
      message.info('Offline - exception queued for sync');
      setSku('');
      setLocation('');
      setDescription('');
    }
  };

  const displayRole = userProfile?.role
    ? userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)
    : 'Worker';

  return (
    <div
      style={{
        minHeight: '100vh',
        background: theme.colors.background,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <HeaderStatusBar
        warehouseName={warehouseName}
        userName={userProfile?.fullName ?? 'Worker'}
        userRole={displayRole}
        userEmail={userProfile?.email}
        isOnline={isOnline}
        pendingSyncCount={pendingSync}
        lastSyncedAt={lastSyncedAt}
      />

      <div style={{ flex: 1, padding: theme.spacing.lg }}>
        <div style={{ marginBottom: theme.spacing.lg }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'transparent',
              border: 'none',
              color: theme.colors.accent,
              fontSize: theme.typography.sizes.base,
              cursor: 'pointer',
              padding: theme.spacing.sm,
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.xs,
            }}
          >
            <ArrowLeftOutlined /> Back
          </button>
        </div>

        <h1 style={{ color: theme.colors.text, fontSize: theme.typography.sizes['2xl'], margin: 0 }}>
          <WarningOutlined style={{ marginRight: theme.spacing.sm, color: theme.colors.warning }} />
          {t('home.exceptions')}
        </h1>

        <Card
          style={{
            marginTop: theme.spacing.xl,
            background: theme.colors.cardBackground,
            border: `1px solid ${theme.colors.border}`,
          }}
          bodyStyle={{ padding: theme.spacing.lg }}
        >
          <div style={{ marginBottom: theme.spacing.lg }}>
            <label
              style={{
                color: theme.colors.text,
                fontSize: theme.typography.sizes.base,
                fontWeight: theme.typography.weights.semibold,
                display: 'block',
                marginBottom: theme.spacing.sm,
              }}
            >
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

          <div style={{ marginBottom: theme.spacing.lg }}>
            <label
              style={{
                color: theme.colors.text,
                fontSize: theme.typography.sizes.base,
                fontWeight: theme.typography.weights.semibold,
                display: 'block',
                marginBottom: theme.spacing.sm,
              }}
            >
              SKU *
            </label>
            <Input
              size="large"
              placeholder="Enter SKU"
              value={sku}
              onChange={(e) => setSku(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: theme.spacing.lg }}>
            <label
              style={{
                color: theme.colors.text,
                fontSize: theme.typography.sizes.base,
                fontWeight: theme.typography.weights.semibold,
                display: 'block',
                marginBottom: theme.spacing.sm,
              }}
            >
              Location (Optional)
            </label>
            <Input
              size="large"
              placeholder="e.g. A-01-01"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>

          <div style={{ marginBottom: theme.spacing.lg }}>
            <label
              style={{
                color: theme.colors.text,
                fontSize: theme.typography.sizes.base,
                fontWeight: theme.typography.weights.semibold,
                display: 'block',
                marginBottom: theme.spacing.sm,
              }}
            >
              Description *
            </label>
            <Input.TextArea
              placeholder="Describe the issue..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
            />
          </div>

          <Button
            type="primary"
            size="large"
            block
            onClick={handleSubmit}
            loading={submitCountMutation.isPending}
          >
            Submit Exception
          </Button>
        </Card>
      </div>
    </div>
  );
};

export default ExceptionsPage;

