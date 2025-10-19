/**
 * HomePage - White Enterprise Theme
 * Professional WMS-style interface for rugged devices
 * Inspired by Manhattan WMS and SAP Fiori
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ClipboardList,
  AlertTriangle,
  Calculator,
  Search,
  History,
  Settings,
  RefreshCw,
} from 'lucide-react';
import { whiteTheme } from '../theme-white';
import { useTranslation } from '../hooks/useTranslation';
import { getStoredUserProfile, StoredUserProfile, getMyTeam, WorkerTeamInfo } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import { useQuery } from '@tanstack/react-query';
import type { OfflineQueueState } from '../lib/offlineQueue';

interface IconCardProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  badge?: number;
  color?: string;
}

const IconCard: React.FC<IconCardProps> = ({ icon, label, onClick, badge, color = whiteTheme.colors.primary }) => {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: whiteTheme.spacing.md,
        padding: whiteTheme.spacing.xl,
        background: whiteTheme.colors.cardBackground,
        border: `1px solid ${whiteTheme.colors.border}`,
        borderRadius: whiteTheme.borderRadius.lg,
        cursor: 'pointer',
        position: 'relative',
        minHeight: '120px',
        minWidth: '120px',
        transition: `all ${whiteTheme.transitions.normal}`,
        boxShadow: whiteTheme.shadows.card,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = color;
        e.currentTarget.style.background = `${color}08`;
        e.currentTarget.style.boxShadow = whiteTheme.shadows.md;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = whiteTheme.colors.border;
        e.currentTarget.style.background = whiteTheme.colors.cardBackground;
        e.currentTarget.style.boxShadow = whiteTheme.shadows.card;
      }}
      onMouseDown={(e) => {
        e.currentTarget.style.transform = 'scale(0.96)';
        e.currentTarget.style.boxShadow = whiteTheme.shadows.sm;
      }}
      onMouseUp={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
      }}
    >
      {badge !== undefined && badge > 0 && (
        <div
          style={{
            position: 'absolute',
            top: whiteTheme.spacing.sm,
            right: whiteTheme.spacing.sm,
            background: whiteTheme.colors.error,
            color: 'white',
            borderRadius: whiteTheme.borderRadius.full,
            minWidth: '22px',
            height: '22px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: whiteTheme.typography.sizes.xs,
            fontWeight: whiteTheme.typography.weights.bold,
            padding: `0 ${whiteTheme.spacing.xs}`,
            boxShadow: whiteTheme.shadows.sm,
          }}
        >
          {badge > 99 ? '99+' : badge}
        </div>
      )}
      <div style={{ fontSize: '40px', color, lineHeight: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {icon}
      </div>
      <div
        style={{
          color: whiteTheme.colors.text,
          fontSize: whiteTheme.typography.sizes.sm,
          fontWeight: whiteTheme.typography.weights.semibold,
          textAlign: 'center',
          letterSpacing: '0.3px',
        }}
      >
        {label}
      </div>
    </button>
  );
};

const HomePageWhite: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [battery, setBattery] = useState<number | null>(null);
  const [isCharging, setIsCharging] = useState<boolean>(false);

  // Monitor network status
  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    networkManager.addListener(handleNetworkChange);
    return () => networkManager.removeListener(handleNetworkChange);
  }, []);

  // Monitor offline queue
  useEffect(() => {
    const handleQueue = (state: OfflineQueueState) => {
      setPendingSync(state.pending);
      setLastSyncedAt(state.lastSyncedAt);
    };
    offlineQueue.addListener(handleQueue);
    return () => offlineQueue.removeListener(handleQueue);
  }, []);

  // Battery API
  useEffect(() => {
    const getBattery = async () => {
      try {
        if ('getBattery' in navigator) {
          const battery = await (navigator as any).getBattery();
          setBattery(Math.round(battery.level * 100));
          setIsCharging(battery.charging);

          battery.addEventListener('levelchange', () => {
            setBattery(Math.round(battery.level * 100));
          });

          battery.addEventListener('chargingchange', () => {
            setIsCharging(battery.charging);
          });
        }
      } catch (error) {
        console.info('Battery API not available');
      }
    };

    getBattery();
  }, []);

  // Fetch team info
  const { data: teamInfo } = useQuery<WorkerTeamInfo | null>({
    queryKey: ['my-team'],
    queryFn: getMyTeam,
    refetchInterval: isOnline ? 60000 : false,
    retry: false,
  });

  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

  const handleSyncNow = async () => {
    if (isOnline && pendingSync > 0) {
      // Trigger sync
      window.location.reload();
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: whiteTheme.colors.background,
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Main Content */}
      <div
        style={{
          flex: 1,
          padding: whiteTheme.spacing.xl,
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        {/* Page Title */}
        <div style={{ marginBottom: whiteTheme.spacing.xl }}>
          <h1
            style={{
              fontSize: whiteTheme.typography.sizes['2xl'],
              fontWeight: whiteTheme.typography.weights.bold,
              color: whiteTheme.colors.text,
              margin: 0,
              marginBottom: whiteTheme.spacing.xs,
            }}
          >
            Cungu WMS
          </h1>
          <p style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, margin: 0 }}>
            Select a module to continue
          </p>
        </div>

        {/* Icon Grid - 7 Professional Modules */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            gap: whiteTheme.spacing.lg,
            marginBottom: whiteTheme.spacing.xl,
          }}
        >
          <IconCard
            icon={<ClipboardList strokeWidth={1.5} />}
            label={t.navigation.tasks}
            onClick={() => navigate('/tasks')}
            color={whiteTheme.colors.primary}
          />

          <IconCard
            icon={<AlertTriangle strokeWidth={1.5} />}
            label={t.navigation.exceptions}
            onClick={() => navigate('/exceptions')}
            color={whiteTheme.colors.warning}
            badge={pendingSync}
          />

          <IconCard
            icon={<Calculator strokeWidth={1.5} />}
            label={t.navigation.stockCount}
            onClick={() => navigate('/stock-count')}
            color="#8B5CF6"
          />

          <IconCard
            icon={<Search strokeWidth={1.5} />}
            label={t.navigation.lookup}
            onClick={() => navigate('/lookup')}
            color="#10B981"
          />

          <IconCard
            icon={<History strokeWidth={1.5} />}
            label={t.navigation.history}
            onClick={() => navigate('/history')}
            color="#F59E0B"
          />

          <IconCard
            icon={<Settings strokeWidth={1.5} />}
            label={t.navigation.settings}
            onClick={() => navigate('/settings')}
            color={whiteTheme.colors.textSecondary}
          />

          <IconCard
            icon={<RefreshCw strokeWidth={1.5} />}
            label="Sync Now"
            onClick={handleSyncNow}
            color={whiteTheme.colors.info}
          />
        </div>
      </div>

      {/* Professional Footer */}
      <div
        style={{
          borderTop: `1px solid ${whiteTheme.colors.divider}`,
          padding: `${whiteTheme.spacing.md} ${whiteTheme.spacing.lg}`,
          background: whiteTheme.colors.panelBackground,
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textMuted }}>
          Cungu WMS PWA • Version 1.0.0 • © 2025 Doppler Systems
        </div>
        {userProfile && (
          <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, marginTop: '4px' }}>
            {userProfile.fullName} • {userProfile.role?.toUpperCase()}
          </div>
        )}
      </div>
    </div>
  );
};

export default HomePageWhite;

