/**
 * StockCountPage - White Enterprise Theme
 * Full Warehouse Inventory Management
 * Supports both ad-hoc counts and systematic warehouse-wide inventory
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, message, Input, Select, Card, Tag, Progress, Divider } from 'antd';
import { ArrowLeft, Calculator, History as HistoryIcon, ScanBarcode, MapPin, Package, BarChart3, Target } from 'lucide-react';
import { whiteTheme } from '../theme-white';
import { useTranslation } from '../hooks/useTranslation';
import NumPad from '../components/NumPad';
import BarcodeScanner from '../components/BarcodeScanner';
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

interface LocationInfo {
  location: string;
  total_items: number;
  counted_items: number;
  progress: number;
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
      params: { limit: 50 },
    });
    return data;
  } catch (error) {
    return [];
  }
};

const fetchLocationProgress = async (): Promise<LocationInfo[]> => {
  try {
    const { data } = await client.get('/counts/location-progress');
    return data;
  } catch (error) {
    return [];
  }
};

const StockCountPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);

  const [mode, setMode] = useState<'select' | 'ad-hoc' | 'by-location' | 'full-inventory' | 'history'>('select');
  const [step, setStep] = useState<'location' | 'sku' | 'quantity' | 'reason'>('location');

  const [location, setLocation] = useState<string>('');
  const [skuInput, setSkuInput] = useState<string>(searchParams.get('sku') || '');
  const [catalogItem, setCatalogItem] = useState<CatalogItem | null>(null);
  const [quantity, setQuantity] = useState<number>(0);
  const [systemQty] = useState<number>(0);
  const [reason, setReason] = useState<string | undefined>(undefined);
  const [note, setNote] = useState<string>('');
  const [numPadVisible, setNumPadVisible] = useState(false);
  const [scannerVisible, setScannerVisible] = useState(false);

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    const handleQueue = (state: OfflineQueueState) => setPendingSync(state.pending);
    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueue);
    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueue);
    };
  }, []);

  const { data: countHistory } = useQuery<CountRecord[]>({
    queryKey: ['count-history'],
    queryFn: fetchCountHistory,
    enabled: mode === 'history' && isOnline,
    retry: false,
  });

  const { data: locationProgress } = useQuery<LocationInfo[]>({
    queryKey: ['location-progress'],
    queryFn: fetchLocationProgress,
    enabled: mode === 'by-location' && isOnline,
    retry: false,
  });

  const submitCountMutation = useMutation({
    mutationFn: async (payload: any) => client.post('/counts', payload),
    onSuccess: () => {
      message.success('Count submitted successfully');
      queryClient.invalidateQueries({ queryKey: ['count-history'] });
      queryClient.invalidateQueries({ queryKey: ['location-progress'] });
      resetFlow();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Error submitting count');
    },
  });

  const resetFlow = () => {
    setMode('select');
    setStep('location');
    setLocation('');
    setSkuInput('');
    setCatalogItem(null);
    setQuantity(0);
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
      message.error('SKU/Barcode not found');
    }
  };

  const handleQuantityConfirm = (confirmedQty: number) => {
    setQuantity(confirmedQty);
    setNumPadVisible(false);
    
    const variance = confirmedQty - systemQty;
    if (Math.abs(variance) > 0) {
      setStep('reason');
    } else {
      handleSubmitCount(confirmedQty, variance);
    }
  };

  const handleSubmitCount = (finalQty?: number, variance?: number) => {
    if (!catalogItem) return;

    const countedQty = finalQty ?? quantity;
    const countVariance = variance ?? (countedQty - systemQty);

    const payload = {
      sku: catalogItem.artikl_sifra,
      location: location || 'UNKNOWN',
      counted_qty: countedQty,
      system_qty: systemQty,
      variance: countVariance,
      reason,
      note: note?.trim() ? note : undefined,
      operation_id: `count-${catalogItem.artikl_sifra}-${Date.now()}`,
    };

    if (networkManager.isConnected()) {
      submitCountMutation.mutate(payload);
    } else {
      offlineQueue.addAction('stock-count' as any, catalogItem.artikl_sifra, payload);
      message.info('Offline - count queued');
      resetFlow();
    }
  };

  // Mode Selection
  if (mode === 'select') {
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
          <button
            onClick={() => navigate('/')}
            className="wms-btn wms-btn-secondary"
            style={{ marginBottom: whiteTheme.spacing.md }}
          >
            <ArrowLeft size={16} /> Home
          </button>
          <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
            Stock Count
          </h1>
        </div>

        <div style={{ padding: whiteTheme.spacing.xl }}>
          <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
              <Calculator size={24} color="#8B5CF6" />
              <div>
                <h2 style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                  Inventory Management
                </h2>
                <p style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, margin: 0 }}>
                  Choose your counting method
                </p>
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: whiteTheme.spacing.lg }}>
            <button
              onClick={() => setMode('ad-hoc')}
              className="wms-icon-card"
              style={{ minHeight: '180px' }}
            >
              <Package size={56} color="#8B5CF6" strokeWidth={1.5} />
              <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                Ad-hoc Count
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                Count single SKU or location
              </div>
            </button>

            <button
              onClick={() => setMode('by-location')}
              className="wms-icon-card"
              style={{ minHeight: '180px' }}
            >
              <MapPin size={56} color={whiteTheme.colors.accent} strokeWidth={1.5} />
              <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                Count by Location
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                Systematic location-based counting
              </div>
            </button>

            <button
              onClick={() => setMode('full-inventory')}
              className="wms-icon-card"
              style={{ minHeight: '180px' }}
            >
              <BarChart3 size={56} color={whiteTheme.colors.warning} strokeWidth={1.5} />
              <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                Full Inventory
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                Complete warehouse count
              </div>
            </button>

            <button
              onClick={() => setMode('history')}
              className="wms-icon-card"
              style={{ minHeight: '180px' }}
            >
              <HistoryIcon size={56} color={whiteTheme.colors.textSecondary} strokeWidth={1.5} />
              <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                Count History
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                View past counts
              </div>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // By Location Mode
  if (mode === 'by-location') {
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
          <button onClick={() => setMode('select')} className="wms-btn wms-btn-secondary" style={{ marginBottom: whiteTheme.spacing.md }}>
            <ArrowLeft size={16} /> Back
          </button>
          <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
            Count by Location
          </h1>
        </div>

        <div style={{ padding: whiteTheme.spacing.lg }}>
          <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
              <MapPin size={24} color={whiteTheme.colors.accent} />
              <div>
                <h2 style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                  Location Progress
                </h2>
                <p style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, margin: 0 }}>
                  Track counting progress by location
                </p>
              </div>
            </div>
          </div>

          {!locationProgress || locationProgress.length === 0 ? (
            <div className="wms-empty">
              <div className="wms-empty-icon"><MapPin size={48} /></div>
              <div className="wms-empty-text">No location data available</div>
              <div className="wms-empty-description">Location-based counting requires system setup</div>
            </div>
          ) : (
            locationProgress.map((loc) => (
              <div key={loc.location} className="wms-card" style={{ marginBottom: whiteTheme.spacing.md }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: whiteTheme.spacing.md }}>
                  <div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                      {loc.location}
                    </div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                      {loc.counted_items}/{loc.total_items} items counted
                    </div>
                  </div>
                  <Tag color={loc.progress === 100 ? 'success' : loc.progress > 0 ? 'processing' : 'default'}>
                    {loc.progress}%
                  </Tag>
                </div>
                <Progress
                  percent={loc.progress}
                  strokeColor={whiteTheme.colors.accent}
                  trailColor={whiteTheme.colors.divider}
                  strokeWidth={8}
                />
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // Full Inventory Mode
  if (mode === 'full-inventory') {
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
          <button onClick={() => setMode('select')} className="wms-btn wms-btn-secondary" style={{ marginBottom: whiteTheme.spacing.md }}>
            <ArrowLeft size={16} /> Back
          </button>
          <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
            Full Inventory Count
          </h1>
        </div>

        <div style={{ padding: whiteTheme.spacing.lg }}>
          <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
              <BarChart3 size={24} color={whiteTheme.colors.warning} />
              <div>
                <h2 style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                  Complete Warehouse Count
                </h2>
                <p style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, margin: 0 }}>
                  Systematic counting of entire warehouse
                </p>
              </div>
            </div>
          </div>

          <div className="wms-card">
            <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
              <Target size={20} color={whiteTheme.colors.info} />
              <h3 style={{ fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                Full Inventory Process
              </h3>
            </div>
            <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, lineHeight: 1.6 }}>
              <p>1. <strong>Plan the count</strong> - Schedule with management</p>
              <p>2. <strong>Freeze operations</strong> - Stop all movements</p>
              <p>3. <strong>Count systematically</strong> - Location by location</p>
              <p>4. <strong>Verify variances</strong> - Investigate discrepancies</p>
              <p>5. <strong>Update system</strong> - Adjust inventory records</p>
              <p>6. <strong>Resume operations</strong> - Restart warehouse activities</p>
            </div>
            <Divider />
            <div style={{ textAlign: 'center' }}>
              <Button
                type="primary"
                size="large"
                icon={<BarChart3 size={20} />}
                onClick={() => message.info('Full inventory count requires management approval')}
                style={{ marginRight: whiteTheme.spacing.md }}
              >
                Start Full Count
              </Button>
              <Button
                size="large"
                onClick={() => setMode('ad-hoc')}
              >
                Use Ad-hoc Instead
              </Button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // History Screen
  if (mode === 'history') {
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
          <button onClick={() => setMode('select')} className="wms-btn wms-btn-secondary" style={{ marginBottom: whiteTheme.spacing.md }}>
            <ArrowLeft size={16} /> Back
          </button>
          <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
            Count History
          </h1>
        </div>

        <div style={{ padding: whiteTheme.spacing.lg }}>
          {!countHistory || countHistory.length === 0 ? (
            <div className="wms-empty">
              <div className="wms-empty-icon"><Calculator size={48} /></div>
              <div className="wms-empty-text">No counts recorded</div>
              <div className="wms-empty-description">Start counting to see history here</div>
            </div>
          ) : (
            countHistory.map((count) => (
              <div key={count.id} className="wms-card" style={{ marginBottom: whiteTheme.spacing.md }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: whiteTheme.spacing.md }}>
                  <div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                      {count.sku} - {count.sku_name}
                    </div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                      {count.location}
                    </div>
                  </div>
                  <Tag color={count.status === 'synced' ? 'success' : 'warning'}>{count.status}</Tag>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: whiteTheme.spacing.md, padding: whiteTheme.spacing.md, background: whiteTheme.colors.panelBackground, borderRadius: whiteTheme.borderRadius.sm }}>
                  <div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Counted</div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.accent }}>{count.counted_qty}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>System</div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>{count.system_qty}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Variance</div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.bold, color: count.variance > 0 ? whiteTheme.colors.success : count.variance < 0 ? whiteTheme.colors.error : whiteTheme.colors.text }}>
                      {count.variance > 0 && '+'}{count.variance}
                    </div>
                  </div>
                </div>
                {count.reason && (
                  <div style={{ marginTop: whiteTheme.spacing.sm, fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.warning }}>
                    Reason: {count.reason}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    );
  }

  // Ad-hoc Count Flow
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
        <button onClick={resetFlow} className="wms-btn wms-btn-secondary" style={{ marginBottom: whiteTheme.spacing.md }}>
          <ArrowLeft size={16} /> Back
        </button>
        <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
          Ad-hoc Count
        </h1>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        {/* Step 1: Location */}
        {step === 'location' && (
          <div>
            <div className="wms-card">
              <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
                Location (Optional)
              </label>
              <Input
                size="large"
                placeholder="e.g. A-01-01"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                style={{ marginBottom: whiteTheme.spacing.md }}
              />
              <Button type="primary" size="large" block onClick={() => setStep('sku')}>
                Next: Enter SKU
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: SKU */}
        {step === 'sku' && (
          <div>
            <div className="wms-card">
              <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
                SKU / Barcode
              </label>
              <div style={{ display: 'flex', gap: whiteTheme.spacing.sm, marginBottom: whiteTheme.spacing.md }}>
                <Input
                  size="large"
                  placeholder="Scan or enter SKU"
                  value={skuInput}
                  onChange={(e) => setSkuInput(e.target.value)}
                  onPressEnter={() => handleSKULookup(skuInput)}
                  style={{ flex: 1 }}
                />
                <Button
                  size="large"
                  icon={<ScanBarcode size={20} />}
                  onClick={() => setScannerVisible(true)}
                />
              </div>
              <Button type="primary" size="large" block onClick={() => handleSKULookup(skuInput)}>
                Lookup
              </Button>
            </div>
          </div>
        )}

        {/* Step 3: Reason */}
        {step === 'reason' && catalogItem && (
          <div>
            <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
              <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.xs }}>
                {catalogItem.naziv}
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, marginBottom: whiteTheme.spacing.md }}>
                {catalogItem.artikl_sifra}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: whiteTheme.spacing.md, padding: whiteTheme.spacing.md, background: whiteTheme.colors.panelBackground, borderRadius: whiteTheme.borderRadius.sm }}>
                <div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Counted</div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xl, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.accent }}>{quantity}</div>
                </div>
                <div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>System</div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xl, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>{systemQty}</div>
                </div>
                <div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Variance</div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xl, fontWeight: whiteTheme.typography.weights.bold, color: quantity - systemQty > 0 ? whiteTheme.colors.success : quantity - systemQty < 0 ? whiteTheme.colors.error : whiteTheme.colors.text }}>
                    {quantity - systemQty > 0 && '+'}{quantity - systemQty}
                  </div>
                </div>
              </div>
            </div>

            <div className="wms-card">
              <label style={{ display: 'block', fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.sm }}>
                Reason (Required)
              </label>
              <Select
                size="large"
                placeholder="Select reason"
                value={reason}
                onChange={setReason}
                style={{ width: '100%', marginBottom: whiteTheme.spacing.md }}
                options={[
                  { value: 'Missing', label: 'Missing' },
                  { value: 'Damaged', label: 'Damaged' },
                  { value: 'Misplaced', label: 'Misplaced' },
                  { value: 'Other', label: 'Other' },
                ]}
              />
              <Input.TextArea
                placeholder="Note (optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
                rows={3}
                style={{ marginBottom: whiteTheme.spacing.md }}
              />
              <Button
                type="primary"
                size="large"
                block
                onClick={() => handleSubmitCount()}
                loading={submitCountMutation.isPending}
                disabled={!reason}
              >
                Submit Count
              </Button>
            </div>
          </div>
        )}

        <BarcodeScanner
          visible={scannerVisible}
          onScan={(barcode) => {
            setScannerVisible(false);
            setSkuInput(barcode);
            handleSKULookup(barcode);
          }}
          onCancel={() => setScannerVisible(false)}
          title="Scan SKU Barcode"
        />

        <NumPad
          visible={numPadVisible}
          title={catalogItem ? `${catalogItem.naziv} - ${catalogItem.artikl_sifra}` : 'Enter Quantity'}
          defaultValue={quantity}
          allowDecimal={true}
          confirmLabel="Confirm"
          cancelLabel="Cancel"
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

export default StockCountPageWhite;