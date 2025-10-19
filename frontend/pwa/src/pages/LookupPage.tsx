/**
 * LookupPage - SKU / Barcode Lookup
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Input, Button, Card, Tag, message } from 'antd';
import { ArrowLeftOutlined, SearchOutlined, ScanOutlined } from '@ant-design/icons';
import { theme } from '../theme';
import { t } from '../i18n/translations';
import HeaderStatusBar from '../components/HeaderStatusBar';
import BarcodeScanner from '../components/BarcodeScanner';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';

interface CatalogItem {
  artikl_sifra: string;
  naziv: string;
  jedinica_mjere: string;
  barkodovi?: string[];
  last_location?: string;
}

const LookupPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? 'Warehouse'
  );

  const [searchMode, setSearchMode] = useState<'sku' | 'barcode'>('sku');
  const [searchInput, setSearchInput] = useState<string>(searchParams.get('barcode') || '');
  const [scannerVisible, setScannerVisible] = useState(false);
  const [searchResult, setSearchResult] = useState<CatalogItem | null>(null);
  const [loading, setLoading] = useState(false);

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
    if (searchParams.get('barcode')) {
      handleSearch(searchParams.get('barcode')!);
    }
  }, [searchParams]);

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      message.error('Please enter SKU or barcode');
      return;
    }

    setLoading(true);
    try {
      const { data } = await client.get('/catalog/lookup', {
        params: { search: query.trim() },
      });
      setSearchResult(data);
    } catch (error: any) {
      message.error(error?.response?.data?.detail || 'Item not found');
      setSearchResult(null);
    } finally {
      setLoading(false);
    }
  };

  const handleScan = (barcode: string) => {
    setScannerVisible(false);
    setSearchInput(barcode);
    handleSearch(barcode);
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
          {t('home.lookup')}
        </h1>

        <div style={{ marginTop: theme.spacing.xl }}>
          <div style={{ display: 'flex', gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
            <button
              onClick={() => setSearchMode('sku')}
              style={{
                flex: 1,
                padding: theme.spacing.md,
                background: searchMode === 'sku' ? theme.colors.primary : theme.colors.cardBackground,
                color: searchMode === 'sku' ? 'white' : theme.colors.text,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.md,
                fontSize: theme.typography.sizes.base,
                fontWeight: theme.typography.weights.semibold,
                cursor: 'pointer',
              }}
            >
              SKU
            </button>
            <button
              onClick={() => setSearchMode('barcode')}
              style={{
                flex: 1,
                padding: theme.spacing.md,
                background: searchMode === 'barcode' ? theme.colors.primary : theme.colors.cardBackground,
                color: searchMode === 'barcode' ? 'white' : theme.colors.text,
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.md,
                fontSize: theme.typography.sizes.base,
                fontWeight: theme.typography.weights.semibold,
                cursor: 'pointer',
              }}
            >
              Barcode
            </button>
          </div>

          <div style={{ display: 'flex', gap: theme.spacing.sm, marginBottom: theme.spacing.lg }}>
            <Input
              size="large"
              placeholder={searchMode === 'sku' ? 'Enter SKU' : 'Enter or scan barcode'}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onPressEnter={() => handleSearch(searchInput)}
              prefix={<SearchOutlined />}
              style={{ flex: 1 }}
            />
            {searchMode === 'barcode' && (
              <Button
                size="large"
                icon={<ScanOutlined />}
                onClick={() => setScannerVisible(true)}
              />
            )}
            <Button
              type="primary"
              size="large"
              onClick={() => handleSearch(searchInput)}
              loading={loading}
            >
              Search
            </Button>
          </div>

          {searchResult && (
            <Card
              style={{
                background: theme.colors.cardBackground,
                border: `1px solid ${theme.colors.border}`,
              }}
              bodyStyle={{ padding: theme.spacing.lg }}
            >
              <div style={{ marginBottom: theme.spacing.md }}>
                <div
                  style={{
                    color: theme.colors.text,
                    fontSize: theme.typography.sizes.xl,
                    fontWeight: theme.typography.weights.bold,
                  }}
                >
                  {searchResult.naziv}
                </div>
                <div
                  style={{
                    color: theme.colors.textSecondary,
                    fontSize: theme.typography.sizes.base,
                    marginTop: theme.spacing.xs,
                  }}
                >
                  SKU: {searchResult.artikl_sifra}
                </div>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: theme.spacing.md,
                  marginTop: theme.spacing.lg,
                }}
              >
                <div>
                  <div
                    style={{
                      color: theme.colors.textSecondary,
                      fontSize: theme.typography.sizes.xs,
                      textTransform: 'uppercase',
                      marginBottom: theme.spacing.xs,
                    }}
                  >
                    Unit
                  </div>
                  <div style={{ color: theme.colors.text, fontWeight: 600 }}>
                    {searchResult.jedinica_mjere}
                  </div>
                </div>
                {searchResult.last_location && (
                  <div>
                    <div
                      style={{
                        color: theme.colors.textSecondary,
                        fontSize: theme.typography.sizes.xs,
                        textTransform: 'uppercase',
                        marginBottom: theme.spacing.xs,
                      }}
                    >
                      Last Location
                    </div>
                    <div style={{ color: theme.colors.text, fontWeight: 600 }}>
                      {searchResult.last_location}
                    </div>
                  </div>
                )}
              </div>

              {searchResult.barkodovi && searchResult.barkodovi.length > 0 && (
                <div style={{ marginTop: theme.spacing.lg }}>
                  <div
                    style={{
                      color: theme.colors.textSecondary,
                      fontSize: theme.typography.sizes.xs,
                      textTransform: 'uppercase',
                      marginBottom: theme.spacing.sm,
                    }}
                  >
                    Barcodes
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: theme.spacing.xs }}>
                    {searchResult.barkodovi.map((barcode, index) => (
                      <Tag key={index} color="blue">
                        {barcode}
                      </Tag>
                    ))}
                  </div>
                </div>
              )}

              <div style={{ marginTop: theme.spacing.xl, display: 'flex', gap: theme.spacing.sm }}>
                <Button
                  type="primary"
                  size="large"
                  block
                  onClick={() => navigate(`/stock-count?sku=${searchResult.artikl_sifra}`)}
                >
                  Count this SKU
                </Button>
              </div>
            </Card>
          )}
        </div>

        <BarcodeScanner
          visible={scannerVisible}
          onScan={handleScan}
          onCancel={() => setScannerVisible(false)}
          title="Scan Barcode"
        />
      </div>
    </div>
  );
};

export default LookupPage;

