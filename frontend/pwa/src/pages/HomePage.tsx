/**
 * HomePage - Icon-based Home Screen for Rugged Devices
 * 
 * Features:
 * - Large tap targets (64x64 minimum)
 * - Monochrome icons
 * - Icon grid layout
 * - Enhanced header with team/shift/battery
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  CheckSquareOutlined, 
  TeamOutlined, 
  ScanOutlined, 
  EditOutlined,
  WarningOutlined,
  CalculatorOutlined,
  SearchOutlined,
  HistoryOutlined,
  SettingOutlined,
  BarcodeOutlined,
} from '@ant-design/icons';
import { theme } from '../theme';
import { t } from '../i18n/translations';
import HeaderStatusBar from '../components/HeaderStatusBar';
import { getStoredUserProfile, StoredUserProfile, getMyTeam, WorkerTeamInfo } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import { useQuery } from '@tanstack/react-query';
import { Tag } from 'antd';
import type { OfflineQueueState } from '../lib/offlineQueue';

interface IconCardProps {
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  badge?: number;
  color?: string;
}

const IconCard: React.FC<IconCardProps> = ({ icon, label, onClick, badge, color = theme.colors.accent }) => {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: theme.spacing.md,
        padding: theme.spacing.xl,
        background: theme.colors.cardBackground,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.lg,
        cursor: 'pointer',
        position: 'relative',
        minHeight: '120px',
        minWidth: '120px',
        transition: 'all 0.2s ease',
      }}
      onMouseDown={(e) => {
        e.currentTarget.style.transform = 'scale(0.95)';
        e.currentTarget.style.background = theme.colors.background;
      }}
      onMouseUp={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.background = theme.colors.cardBackground;
      }}
      onTouchStart={(e) => {
        e.currentTarget.style.transform = 'scale(0.95)';
        e.currentTarget.style.background = theme.colors.background;
      }}
      onTouchEnd={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.background = theme.colors.cardBackground;
      }}
    >
      {badge !== undefined && badge > 0 && (
        <div
          style={{
            position: 'absolute',
            top: theme.spacing.sm,
            right: theme.spacing.sm,
            background: theme.colors.error,
            color: 'white',
            borderRadius: '999px',
            minWidth: '24px',
            height: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: theme.typography.sizes.xs,
            fontWeight: theme.typography.weights.bold,
            padding: `0 ${theme.spacing.xs}`,
          }}
        >
          {badge > 99 ? '99+' : badge}
        </div>
      )}
      <div style={{ fontSize: '48px', color, lineHeight: 1 }}>
        {icon}
      </div>
      <div
        style={{
          color: theme.colors.text,
          fontSize: theme.typography.sizes.sm,
          fontWeight: theme.typography.weights.semibold,
          textAlign: 'center',
          letterSpacing: '0.3px',
        }}
      >
        {label}
      </div>
    </button>
  );
};

const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? 'Warehouse'
  );
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

  // Battery API (if available)
  useEffect(() => {
    const getBattery = async () => {
      try {
        // @ts-ignore - Battery API might not be in TypeScript definitions
        if ('getBattery' in navigator) {
          // @ts-ignore
          const battery = await navigator.getBattery();
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

  // Refresh user profile
  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

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
      {/* Enhanced Header */}
      <HeaderStatusBar
        warehouseName={warehouseName}
        userName={userProfile?.fullName ?? 'Worker'}
        userRole={displayRole}
        userEmail={userProfile?.email}
        isOnline={isOnline}
        pendingSyncCount={pendingSync}
        lastSyncedAt={lastSyncedAt}
        battery={battery}
        isCharging={isCharging}
      />

      {/* Team & Shift Info */}
      {teamInfo && (
        <div
          style={{
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '16px',
            color: 'white',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            flexWrap: 'wrap',
            gap: theme.spacing.md,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div>
              <TeamOutlined style={{ marginRight: '8px', fontSize: '18px' }} />
              <strong style={{ fontSize: '16px' }}>{teamInfo.team_name}</strong>
              <Tag color="cyan" style={{ marginLeft: '8px', fontSize: '13px' }}>
                {t('header.shift')} {teamInfo.shift}
              </Tag>
            </div>
            <div style={{ fontSize: '14px', opacity: 0.95 }}>
              {teamInfo.partner_name}
              {teamInfo.partner_online ? (
                <Tag color="success" style={{ marginLeft: '8px' }}>
                  {t('header.online')}
                </Tag>
              ) : (
                <Tag color="default" style={{ marginLeft: '8px' }}>
                  {t('header.offline')}
                </Tag>
              )}
            </div>
          </div>
          {teamInfo.shift_status.countdown_formatted && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontFamily: 'monospace',
                  fontSize: '18px',
                  fontWeight: 'bold',
                }}
              >
                {teamInfo.shift_status.countdown_formatted}
              </span>
              <span style={{ fontSize: '12px', opacity: 0.9 }}>
                {teamInfo.shift_status.status === 'on_break'
                  ? t('header.toEnd')
                  : teamInfo.shift_status.status === 'working'
                    ? t('header.toBreak')
                    : ''}
              </span>
            </div>
          )}
        </div>
      )}

      {/* Icon Grid */}
      <div
        style={{
          flex: 1,
          padding: theme.spacing.xl,
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
          gap: theme.spacing.lg,
          alignContent: 'start',
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%',
        }}
      >
        <IconCard
          icon={<CheckSquareOutlined />}
          label={t('home.myTasks')}
          onClick={() => navigate('/tasks')}
          color={theme.colors.primary}
        />

        <IconCard
          icon={<TeamOutlined />}
          label={t('home.teamTasks')}
          onClick={() => navigate('/team-tasks')}
          color={theme.colors.accent}
        />

        <IconCard
          icon={<ScanOutlined />}
          label={t('home.scanPick')}
          onClick={() => navigate('/scan-pick')}
          color={theme.colors.success}
        />

        <IconCard
          icon={<EditOutlined />}
          label={t('home.manualEntry')}
          onClick={() => navigate('/manual-entry')}
          color="#3B82F6"
        />

        <IconCard
          icon={<WarningOutlined />}
          label={t('home.exceptions')}
          onClick={() => navigate('/exceptions')}
          color={theme.colors.warning}
          badge={pendingSync}
        />

        <IconCard
          icon={<CalculatorOutlined />}
          label={t('home.stockCount')}
          onClick={() => navigate('/stock-count')}
          color="#A78BFA"
        />

        <IconCard
          icon={<SearchOutlined />}
          label={t('home.lookup')}
          onClick={() => navigate('/lookup')}
          color="#10B981"
        />

        <IconCard
          icon={<HistoryOutlined />}
          label={t('home.history')}
          onClick={() => navigate('/history')}
          color="#F59E0B"
        />

        <IconCard
          icon={<SettingOutlined />}
          label={t('home.settings')}
          onClick={() => navigate('/settings')}
          color={theme.colors.textSecondary}
        />
      </div>

      {/* Footer Info */}
      <div
        style={{
          padding: theme.spacing.md,
          textAlign: 'center',
          color: theme.colors.textSecondary,
          fontSize: theme.typography.sizes.xs,
          borderTop: `1px solid ${theme.colors.border}`,
        }}
      >
        {userProfile?.fullName} • {displayRole}
        {battery !== null && (
          <span style={{ marginLeft: theme.spacing.md }}>
            {t('header.battery')}: {battery}%{isCharging && ' ⚡'}
          </span>
        )}
      </div>
    </div>
  );
};

export default HomePage;

