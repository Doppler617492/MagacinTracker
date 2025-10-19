/**
 * LookupPage - White Enterprise Theme
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Input, Button, Tag, message } from 'antd';
import { ArrowLeft, Search, ScanBarcode, Calculator } from 'lucide-react';
import { whiteTheme } from '../theme-white';
import BarcodeScanner from '../components/BarcodeScanner';
import client from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';
import { useTranslation } from '../hooks/useTranslation';

interface CatalogItem {
  sifra: string;
  naziv: string;
  jedinica_mjere: string;
  aktivan: boolean;
  barkodovi: Array<{
    value: string;
    is_primary?: boolean;
  }>;
  last_location?: string;
}

const LookupPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [searchMode, setSearchMode] = useState<'sku' | 'barcode'>('sku');
  const [searchInput, setSearchInput] = useState<string>(searchParams.get('barcode') || '');
  const [scannerVisible, setScannerVisible] = useState(false);
  const [searchResult, setSearchResult] = useState<CatalogItem | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    networkManager.addListener(handleNetworkChange);
    return () => networkManager.removeListener(handleNetworkChange);
  }, []);

  useEffect(() => {
    if (searchParams.get('barcode')) {
      handleSearch(searchParams.get('barcode')!);
    }
  }, [searchParams]);

  const handleSearch = async (query: string) => {
    if (!query.trim()) {
      message.error('Molimo unesite SKU ili barkod');
      return;
    }

    setLoading(true);
    try {
      const { data } = await client.get('/catalog/lookup', {
        params: { search: query.trim() },
      });
      setSearchResult(data);
    } catch (error: any) {
      message.error(error?.response?.data?.detail || t.lookup.itemNotFound);
      setSearchResult(null);
    } finally {
      setLoading(false);
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
          <ArrowLeft size={16} /> {t.common.home}
        </button>
        <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
          {t.lookup.title}
        </h1>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        <div style={{ marginBottom: whiteTheme.spacing.lg }}>
          <div style={{ display: 'flex', gap: whiteTheme.spacing.sm, marginBottom: whiteTheme.spacing.md }}>
            <button
              onClick={() => setSearchMode('sku')}
              style={{
                flex: 1,
                padding: whiteTheme.spacing.md,
                background: searchMode === 'sku' ? whiteTheme.colors.primary : whiteTheme.colors.cardBackground,
                color: searchMode === 'sku' ? 'white' : whiteTheme.colors.text,
                border: `1px solid ${searchMode === 'sku' ? whiteTheme.colors.primary : whiteTheme.colors.border}`,
                borderRadius: whiteTheme.borderRadius.md,
                fontSize: whiteTheme.typography.sizes.base,
                fontWeight: whiteTheme.typography.weights.semibold,
                cursor: 'pointer',
              }}
            >
              SKU
            </button>
            <button
              onClick={() => setSearchMode('barcode')}
              style={{
                flex: 1,
                padding: whiteTheme.spacing.md,
                background: searchMode === 'barcode' ? whiteTheme.colors.primary : whiteTheme.colors.cardBackground,
                color: searchMode === 'barcode' ? 'white' : whiteTheme.colors.text,
                border: `1px solid ${searchMode === 'barcode' ? whiteTheme.colors.primary : whiteTheme.colors.border}`,
                borderRadius: whiteTheme.borderRadius.md,
                fontSize: whiteTheme.typography.sizes.base,
                fontWeight: whiteTheme.typography.weights.semibold,
                cursor: 'pointer',
              }}
            >
              Barcode
            </button>
          </div>

          <div style={{ display: 'flex', gap: whiteTheme.spacing.sm }}>
            <Input
              size="large"
              placeholder={searchMode === 'sku' ? t.lookup.enterSku : t.lookup.scanOrEnter}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onPressEnter={() => handleSearch(searchInput)}
              prefix={<Search size={16} />}
              style={{ flex: 1 }}
            />
            {searchMode === 'barcode' && (
              <Button
                size="large"
                icon={<ScanBarcode size={20} />}
                onClick={() => setScannerVisible(true)}
              />
            )}
            <Button
              type="primary"
              size="large"
              onClick={() => handleSearch(searchInput)}
              loading={loading}
            >
              {t.common.search}
            </Button>
          </div>
        </div>

        {searchResult && (
          <div 
            className="wms-card"
            style={{
              padding: whiteTheme.spacing.xl,
              background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
              border: `2px solid ${whiteTheme.colors.border}`,
              borderRadius: whiteTheme.borderRadius.lg,
              boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            }}
          >
            <div style={{ marginBottom: whiteTheme.spacing.lg }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.sm, marginBottom: whiteTheme.spacing.sm }}>
                <div style={{ 
                  background: searchResult.aktivan ? whiteTheme.colors.success : whiteTheme.colors.error,
                  borderRadius: '50%',
                  width: '12px',
                  height: '12px',
                }} />
                <div style={{ fontSize: whiteTheme.typography.sizes.xl, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>
                  {searchResult.naziv}
                </div>
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.base, color: whiteTheme.colors.textSecondary, marginTop: whiteTheme.spacing.xs }}>
                SKU: {searchResult.sifra}
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: searchResult.aktivan ? whiteTheme.colors.success : whiteTheme.colors.error, marginTop: whiteTheme.spacing.xs }}>
                {searchResult.aktivan ? '✅ Aktivan' : '❌ Neaktivan'}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: whiteTheme.spacing.lg, marginBottom: whiteTheme.spacing.lg, padding: whiteTheme.spacing.lg, background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)', borderRadius: whiteTheme.borderRadius.lg, border: `1px solid ${whiteTheme.colors.border}` }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', fontWeight: 600, marginBottom: whiteTheme.spacing.xs }}>
                  📦 Jedinica mjere
                </div>
                <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>
                  {searchResult.jedinica_mjere}
                </div>
              </div>
              {searchResult.last_location && (
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', fontWeight: 600, marginBottom: whiteTheme.spacing.xs }}>
                    📍 Poslednja lokacija
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>
                    {searchResult.last_location}
                  </div>
                </div>
              )}
            </div>

            {searchResult.barkodovi && searchResult.barkodovi.length > 0 && (
              <div style={{ marginBottom: whiteTheme.spacing.lg }}>
                <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', fontWeight: 600, marginBottom: whiteTheme.spacing.sm }}>
                  📷 Barkodovi ({searchResult.barkodovi.length})
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: whiteTheme.spacing.sm }}>
                  {searchResult.barkodovi.map((barcode, index) => (
                    <Tag 
                      key={index} 
                      color={barcode.is_primary ? "blue" : "default"}
                      style={{ 
                        fontSize: whiteTheme.typography.sizes.sm,
                        fontWeight: barcode.is_primary ? 600 : 400,
                        padding: `${whiteTheme.spacing.xs} ${whiteTheme.spacing.sm}`,
                      }}
                    >
                      {barcode.is_primary ? '⭐ ' : ''}{barcode.value}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: whiteTheme.spacing.sm }}>
              <Button
                type="primary"
                size="large"
                icon={<Calculator size={18} />}
                onClick={() => navigate(`/stock-count?sku=${searchResult.sifra}`)}
                style={{ flex: 1 }}
              >
                Broj ovaj SKU
              </Button>
              <Button
                size="large"
                icon={<Search size={18} />}
                onClick={() => {
                  setSearchInput('');
                  setSearchResult(null);
                }}
                style={{ flex: 1 }}
              >
                Nova pretraga
              </Button>
            </div>
          </div>
        )}

        <BarcodeScanner
          visible={scannerVisible}
          onScan={(barcode) => {
            setScannerVisible(false);
            setSearchInput(barcode);
            handleSearch(barcode);
          }}
          onCancel={() => setScannerVisible(false)}
          title="Skeniraj barkod"
        />
      </div>
    </div>
  );
};

export default LookupPageWhite;

