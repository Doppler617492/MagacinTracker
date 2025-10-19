/**
 * StockCountPage - Stock Count / Cycle Count Module
 * 
 * Features:
 * - Ad-hoc count (single SKU/Location)
 * - Guided count (system-proposed route)
 * - Offline support with sync
 * - Variance tracking
 * - Large numeric keypad
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, message, Input, Select, Tag, Card } from 'antd';
import {
  ScanOutlined,
  CalculatorOutlined,
  HistoryOutlined,
  ArrowLeftOutlined,
  PlusOutlined,
} from '@ant-design/icons';
import { theme } from '../theme';
import { t } from '../i18n/translations';
import HeaderStatusBar from '../components/HeaderStatusBar';
import NumPad from '../components/NumPad';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';

interface CountRecord {
  id: string;
  sku: string;
  sku_name: string;
  location: string;
  counted_qty: number;
  system_qty: number;
  variance: number;
  reason?: string;
  note?: string;
  status: 'pending' | 'synced';
  created_at: string;
}

interface CatalogItem {
  artikl_sifra: string;
  naziv: string;
  jedinica_mjere: string;
  barkodovi?: string[];
}

const fetchCatalogItem = async (skuOrBarcode: string): Promise<CatalogItem | null> => {
  try {
    const { data } = await client.get(`/catalog/lookup`, {
      params: { search: skuOrBarcode },
    });
    return data;
  } catch (error) {
    return null;
  }
};

const fetchCountHistory = async (): Promise<CountRecord[]> => {
  try {
    const { data } = await client.get('/counts', {
      params: {
        limit: 50,
      },
    });
    return data;
  } catch (error) {
    console.error('Failed to fetch count history:', error);
    return [];
  }
};

const StockCountPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? 'Warehouse'
  );

  // Flow state
  const [mode, setMode] = useState<'select' | 'ad-hoc' | 'history'>('select');
  const [step, setStep] = useState<'location' | 'sku' | 'quantity' | 'reason'>('location');

  // Count data
  const [location, setLocation] = useState<string>('');
  const [skuInput, setSkuInput] = useState<string>('');
  const [catalogItem, setCatalogItem] = useState<CatalogItem | null>(null);
  const [quantity, setQuantity] = useState<number>(0);
  const [systemQty, setSystemQty] = useState<number>(0);
  const [reason, setReason] = useState<string | undefined>(undefined);
  const [note, setNote] = useState<string>('');
  const [numPadVisible, setNumPadVisible] = useState(false);

  // Network monitoring
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

  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

  // Fetch count history
  const { data: countHistory, refetch: refetchHistory } = useQuery<CountRecord[]>({
    queryKey: ['count-history'],
    queryFn: fetchCountHistory,
    enabled: mode === 'history' && isOnline,
    retry: false,
  });

  // Submit count mutation
  const submitCountMutation = useMutation({
    mutationFn: async (payload: {
      sku: string;
      location: string;
      counted_qty: number;
      system_qty: number;
      variance: number;
      reason?: string;
      note?: string;
      operation_id: string;
    }) => {
      return client.post('/counts', payload);
    },
    onSuccess: () => {
      message.success(t('stockCount.submit') + ' - ' + t('common.success'));
      queryClient.invalidateQueries({ queryKey: ['count-history'] });
      resetFlow();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || t('common.error'));
    },
  });

  const resetFlow = () => {
    setMode('select');
    setStep('location');
    setLocation('');
    setSkuInput('');
    setCatalogItem(null);
    setQuantity(0);
    setSystemQty(0);
    setReason(undefined);
    setNote('');
  };

  const handleSKULookup = async (input: string) => {
    if (!input.trim()) {
      message.error('Please enter SKU or barcode');
      return;
    }

    const item = await fetchCatalogItem(input.trim());
    if (item) {
      setCatalogItem(item);
      setStep('quantity');
      setNumPadVisible(true);
    } else {
      message.error('SKU/Barcode not found in catalog');
    }
  };

  const handleQuantityConfirm = (confirmedQty: number) => {
    setQuantity(confirmedQty);
    setNumPadVisible(false);
    
    // Calculate variance (mock system qty for now)
    const variance = confirmedQty - systemQty;

    if (Math.abs(variance) > 0) {
      setStep('reason');
    } else {
      handleSubmitCount(confirmedQty, variance);
    }
  };

  const handleSubmitCount = (finalQty?: number, variance?: number) => {
    if (!catalogItem) {
      message.error('No SKU selected');
      return;
    }

    const countedQty = finalQty ?? quantity;
    const countVariance = variance ?? (countedQty - systemQty);

    const operationId = `count-${catalogItem.artikl_sifra}-${Date.now()}`;

    const payload = {
      sku: catalogItem.artikl_sifra,
      location: location || 'UNKNOWN',
      counted_qty: countedQty,
      system_qty: systemQty,
      variance: countVariance,
      reason,
      note: note?.trim() ? note : undefined,
      operation_id: operationId,
    };

    if (networkManager.isConnected()) {
      submitCountMutation.mutate(payload);
    } else {
      // Queue for offline sync
      offlineQueue.addAction('stock-count' as any, catalogItem.artikl_sifra, payload);
      message.info('Offline - count queued for sync');
      resetFlow();
    }
  };

  const displayRole = userProfile?.role
    ? userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)
    : 'Worker';

  // Mode Selection Screen
  if (mode === 'select') {
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

        <div
          style={{
            flex: 1,
            padding: theme.spacing.xl,
            display: 'flex',
            flexDirection: 'column',
            gap: theme.spacing.lg,
          }}
        >
          <div>
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
            {t('stockCount.title')}
          </h1>

          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: theme.spacing.lg,
              marginTop: theme.spacing.xl,
            }}
          >
            <button
              onClick={() => setMode('ad-hoc')}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: theme.spacing.md,
                padding: theme.spacing.xl,
                background: theme.colors.cardBackground,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.lg,
                cursor: 'pointer',
                minHeight: '160px',
              }}
            >
              <CalculatorOutlined style={{ fontSize: '64px', color: '#A78BFA' }} />
              <div>
                <div
                  style={{
                    color: theme.colors.text,
                    fontSize: theme.typography.sizes.lg,
                    fontWeight: theme.typography.weights.semibold,
                  }}
                >
                  {t('stockCount.adHoc')}
                </div>
                <div
                  style={{
                    color: theme.colors.textSecondary,
                    fontSize: theme.typography.sizes.sm,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  Count single SKU or location
                </div>
              </div>
            </button>

            <button
              onClick={() => setMode('history')}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: theme.spacing.md,
                padding: theme.spacing.xl,
                background: theme.colors.cardBackground,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.lg,
                cursor: 'pointer',
                minHeight: '160px',
              }}
            >
              <HistoryOutlined style={{ fontSize: '64px', color: theme.colors.warning }} />
              <div>
                <div
                  style={{
                    color: theme.colors.text,
                    fontSize: theme.typography.sizes.lg,
                    fontWeight: theme.typography.weights.semibold,
                  }}
                >
                  {t('stockCount.history')}
                </div>
                <div
                  style={{
                    color: theme.colors.textSecondary,
                    fontSize: theme.typography.sizes.sm,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  View past counts
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // History Screen
  if (mode === 'history') {
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
              onClick={() => setMode('select')}
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
            {t('stockCount.history')}
          </h1>

          <div style={{ marginTop: theme.spacing.lg }}>
            {!countHistory || countHistory.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: theme.spacing.xl,
                  color: theme.colors.textSecondary,
                  border: `1px dashed ${theme.colors.border}`,
                  borderRadius: theme.borderRadius.lg,
                }}
              >
                {t('common.noData')}
              </div>
            ) : (
              countHistory.map((count) => (
                <Card
                  key={count.id}
                  style={{
                    marginBottom: theme.spacing.md,
                    background: theme.colors.cardBackground,
                    border: `1px solid ${theme.colors.border}`,
                  }}
                  bodyStyle={{ padding: theme.spacing.md }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                    }}
                  >
                    <div>
                      <div
                        style={{
                          color: theme.colors.text,
                          fontSize: theme.typography.sizes.md,
                          fontWeight: theme.typography.weights.semibold,
                        }}
                      >
                        {count.sku} - {count.sku_name}
                      </div>
                      <div
                        style={{
                          color: theme.colors.textSecondary,
                          fontSize: theme.typography.sizes.sm,
                          marginTop: theme.spacing.xs,
                        }}
                      >
                        Location: {count.location}
                      </div>
                    </div>
                    <Tag color={count.status === 'synced' ? 'green' : 'orange'}>
                      {count.status}
                    </Tag>
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr 1fr',
                      gap: theme.spacing.sm,
                      marginTop: theme.spacing.md,
                    }}
                  >
                    <div>
                      <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
                        {t('stockCount.counted')}
                      </div>
                      <div style={{ color: theme.colors.accent, fontWeight: 600 }}>
                        {count.counted_qty}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
                        {t('stockCount.systemQty')}
                      </div>
                      <div style={{ color: theme.colors.text, fontWeight: 600 }}>
                        {count.system_qty}
                      </div>
                    </div>
                    <div>
                      <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
                        {t('stockCount.variance')}
                      </div>
                      <div
                        style={{
                          color:
                            count.variance > 0
                              ? theme.colors.success
                              : count.variance < 0
                                ? theme.colors.error
                                : theme.colors.text,
                          fontWeight: 600,
                        }}
                      >
                        {count.variance > 0 && '+'}
                        {count.variance}
                      </div>
                    </div>
                  </div>
                  {count.reason && (
                    <div
                      style={{
                        marginTop: theme.spacing.sm,
                        color: theme.colors.warning,
                        fontSize: theme.typography.sizes.xs,
                      }}
                    >
                      Reason: {count.reason}
                    </div>
                  )}
                </Card>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  // Ad-hoc Count Flow
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
            onClick={resetFlow}
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
          {t('stockCount.adHoc')}
        </h1>

        {/* Step 1: Location (Optional) */}
        {step === 'location' && (
          <div style={{ marginTop: theme.spacing.xl }}>
            <div style={{ marginBottom: theme.spacing.md }}>
              <label
                style={{
                  color: theme.colors.text,
                  fontSize: theme.typography.sizes.md,
                  fontWeight: theme.typography.weights.semibold,
                  display: 'block',
                  marginBottom: theme.spacing.sm,
                }}
              >
                {t('stockCount.enterLocation')} ({t('common.optional')})
              </label>
              <Input
                size="large"
                placeholder="e.g. A-01-01"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                style={{ marginBottom: theme.spacing.md }}
              />
            </div>
            <Button
              type="primary"
              size="large"
              block
              onClick={() => setStep('sku')}
            >
              Next: {t('stockCount.enterSKU')}
            </Button>
          </div>
        )}

        {/* Step 2: SKU/Barcode */}
        {step === 'sku' && (
          <div style={{ marginTop: theme.spacing.xl }}>
            <div style={{ marginBottom: theme.spacing.md }}>
              <label
                style={{
                  color: theme.colors.text,
                  fontSize: theme.typography.sizes.md,
                  fontWeight: theme.typography.weights.semibold,
                  display: 'block',
                  marginBottom: theme.spacing.sm,
                }}
              >
                {t('stockCount.scanSKU')} / {t('stockCount.enterSKU')}
              </label>
              <Input
                size="large"
                placeholder="Scan or type SKU/Barcode"
                value={skuInput}
                onChange={(e) => setSkuInput(e.target.value)}
                onPressEnter={() => handleSKULookup(skuInput)}
                prefix={<ScanOutlined />}
              />
            </div>
            <Button
              type="primary"
              size="large"
              block
              onClick={() => handleSKULookup(skuInput)}
              loading={false}
            >
              Lookup
            </Button>
          </div>
        )}

        {/* Step 3: Reason (if variance) */}
        {step === 'reason' && catalogItem && (
          <div style={{ marginTop: theme.spacing.xl }}>
            <div
              style={{
                background: theme.colors.cardBackground,
                padding: theme.spacing.lg,
                borderRadius: theme.borderRadius.lg,
                border: `1px solid ${theme.colors.border}`,
                marginBottom: theme.spacing.lg,
              }}
            >
              <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.lg, fontWeight: 600 }}>
                {catalogItem.naziv}
              </div>
              <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
                {catalogItem.artikl_sifra}
              </div>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: theme.spacing.sm,
                  marginTop: theme.spacing.md,
                }}
              >
                <div>
                  <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
                    {t('stockCount.counted')}
                  </div>
                  <div style={{ color: theme.colors.accent, fontWeight: 600 }}>{quantity}</div>
                </div>
                <div>
                  <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
                    {t('stockCount.systemQty')}
                  </div>
                  <div style={{ color: theme.colors.text, fontWeight: 600 }}>{systemQty}</div>
                </div>
                <div>
                  <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
                    {t('stockCount.variance')}
                  </div>
                  <div
                    style={{
                      color:
                        quantity - systemQty > 0
                          ? theme.colors.success
                          : quantity - systemQty < 0
                            ? theme.colors.error
                            : theme.colors.text,
                      fontWeight: 600,
                    }}
                  >
                    {quantity - systemQty > 0 && '+'}
                    {quantity - systemQty}
                  </div>
                </div>
              </div>
            </div>

            <div style={{ marginBottom: theme.spacing.lg }}>
              <label
                style={{
                  color: theme.colors.text,
                  fontSize: theme.typography.sizes.md,
                  fontWeight: theme.typography.weights.semibold,
                  display: 'block',
                  marginBottom: theme.spacing.sm,
                }}
              >
                {t('tasks.reason')} ({t('tasks.required')})
              </label>
              <Select
                size="large"
                placeholder="Select reason"
                value={reason}
                onChange={setReason}
                style={{ width: '100%', marginBottom: theme.spacing.md }}
                options={[
                  { value: t('reasons.missing'), label: t('reasons.missing') },
                  { value: t('reasons.damaged'), label: t('reasons.damaged') },
                  { value: t('reasons.misplaced'), label: t('reasons.misplaced') },
                  { value: t('reasons.other'), label: t('reasons.other') },
                ]}
              />
              <Input.TextArea
                placeholder={`${t('tasks.note')} (${t('tasks.optional')})`}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
              />
            </div>

            <Button
              type="primary"
              size="large"
              block
              onClick={() => handleSubmitCount()}
              loading={submitCountMutation.isPending}
              disabled={!reason}
            >
              {t('stockCount.submit')}
            </Button>
          </div>
        )}

        {/* NumPad for Quantity */}
        <NumPad
          visible={numPadVisible}
          title={catalogItem ? `${catalogItem.naziv} - ${catalogItem.artikl_sifra}` : 'Enter Quantity'}
          defaultValue={quantity}
          allowDecimal={true}
          confirmLabel={t('common.confirm')}
          cancelLabel={t('common.cancel')}
          onCancel={() => {
            setNumPadVisible(false);
            setStep('sku');
          }}
          onValueChange={(val) => setQuantity(val)}
          onConfirm={handleQuantityConfirm}
        />
      </div>
    </div>
  );
};

export default StockCountPage;

