import React, { useState, useEffect } from 'react';
import { 
  WifiOutlined, 
  DisconnectOutlined, 
  SyncOutlined, 
  ThunderboltOutlined,
  UserOutlined,
  HomeOutlined,
  LogoutOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { Dropdown, Badge } from 'antd';
import type { MenuProps } from 'antd';
import { theme } from '../theme';

interface HeaderStatusBarProps {
  warehouseName?: string;
  userName?: string;
  userRole?: string;
  userEmail?: string;
  isOnline?: boolean;
  isSyncing?: boolean;
  pendingSyncCount?: number;
  lastSyncedAt?: number | null;
  activeShiftLabel?: string;
  onLogout?: () => void;
}

const HeaderStatusBar: React.FC<HeaderStatusBarProps> = ({
  warehouseName = 'Transit Warehouse',
  userName = 'Worker',
  userRole = 'Magacioner',
  userEmail,
  isOnline = true,
  isSyncing,
  pendingSyncCount = 0,
  lastSyncedAt = null,
  activeShiftLabel = 'Dnevna smjena',
  onLogout,
}) => {
  const [batteryLevel, setBatteryLevel] = useState<number>(100);

  useEffect(() => {
    // Battery API (if available on device)
    if ('getBattery' in navigator) {
      (navigator as any).getBattery().then((battery: any) => {
        setBatteryLevel(Math.round(battery.level * 100));
        battery.addEventListener('levelchange', () => {
          setBatteryLevel(Math.round(battery.level * 100));
        });
      });
    }
  }, []);

  const formattedLastSync = lastSyncedAt
    ? new Date(lastSyncedAt).toLocaleString('sr-Latn-ME', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      })
    : 'Nema podataka';

  const syncing = typeof isSyncing === 'boolean' ? isSyncing : pendingSyncCount > 0;

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 600 }}>
            {userName}
          </div>
          {userEmail && (
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
              {userEmail}
            </div>
          )}
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'role',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
            Uloga
          </div>
          <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 500 }}>
            {userRole}
          </div>
        </div>
      ),
      disabled: true,
    },
    {
      key: 'shift',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
            Aktivna smjena
          </div>
          <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm }}>
            {activeShiftLabel}
          </div>
        </div>
      ),
      disabled: true,
    },
    {
      key: 'sync',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
            Posljednja sinhronizacija
          </div>
          <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm }}>
            {formattedLastSync}
          </div>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Odjavi se',
      danger: true,
      onClick: onLogout,
    },
  ];

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: theme.zIndex.header,
        background: theme.colors.cardBackground,
        borderBottom: `1px solid ${theme.colors.border}`,
        padding: `${theme.spacing.md} ${theme.spacing.lg}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: theme.spacing.md,
        boxShadow: theme.shadows.sm,
      }}
    >
      {/* Left: Warehouse */}
      <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm, flex: '0 0 auto' }}>
        <HomeOutlined style={{ fontSize: '18px', color: theme.colors.accent }} />
        <span
          style={{
            color: theme.colors.text,
            fontSize: theme.typography.sizes.sm,
            fontWeight: theme.typography.weights.medium,
            whiteSpace: 'nowrap',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            maxWidth: '140px',
          }}
        >
          {warehouseName}
        </span>
      </div>

      {/* Center: User Info (Clickable) */}
      <Dropdown menu={{ items: userMenuItems }} trigger={['click']} placement="bottomRight">
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.sm,
            cursor: 'pointer',
            padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
            borderRadius: theme.borderRadius.md,
            background: theme.colors.neutral,
            transition: 'background 0.2s',
            flex: '1 1 auto',
            justifyContent: 'center',
            minWidth: 0,
          }}
          onMouseEnter={(e) => (e.currentTarget.style.background = '#3a3a3a')}
          onMouseLeave={(e) => (e.currentTarget.style.background = theme.colors.neutral)}
        >
          <UserOutlined style={{ fontSize: '16px', color: theme.colors.accent }} />
          <span
            style={{
              color: theme.colors.text,
              fontSize: theme.typography.sizes.sm,
              fontWeight: theme.typography.weights.medium,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {userName}
          </span>
          {userRole && (
            <span
              style={{
                marginLeft: 6,
                padding: '2px 6px',
                borderRadius: 8,
                background: '#2f2f2f',
                color: theme.colors.textSecondary,
                fontSize: theme.typography.sizes.xs,
                textTransform: 'uppercase',
              }}
            >
              {userRole}
            </span>
          )}
        </div>
      </Dropdown>

      {/* Right: Status Indicators */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: theme.spacing.md,
          flex: '0 0 auto',
        }}
      >
        {/* Online/Offline */}
        <Badge
          dot
          color={isOnline ? theme.colors.success : theme.colors.neutral}
          offset={[-2, 2]}
        >
          {isOnline ? (
            <WifiOutlined style={{ fontSize: '16px', color: theme.colors.success }} />
          ) : (
            <DisconnectOutlined style={{ fontSize: '16px', color: theme.colors.textSecondary }} />
          )}
        </Badge>

        {/* Sync Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <Badge
            count={pendingSyncCount}
            showZero={false}
            color={syncing ? theme.colors.warning : theme.colors.success}
          >
            <SyncOutlined
              spin={syncing}
              style={{
                fontSize: '16px',
                color: syncing ? theme.colors.primary : theme.colors.textSecondary,
              }}
            />
          </Badge>
          <span
            style={{
              color: syncing ? theme.colors.warning : theme.colors.textSecondary,
              fontSize: theme.typography.sizes.xs,
              fontWeight: theme.typography.weights.medium,
            }}
          >
            {syncing ? 'Pending' : 'Synced'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <ClockCircleOutlined
            style={{
              fontSize: '16px',
              color: theme.colors.textSecondary,
            }}
          />
          <span
            style={{
              color: theme.colors.textSecondary,
              fontSize: theme.typography.sizes.xs,
              fontWeight: theme.typography.weights.medium,
              whiteSpace: 'nowrap',
            }}
          >
            {formattedLastSync}
          </span>
        </div>

        {/* Battery */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <ThunderboltOutlined
            style={{
              fontSize: '16px',
              color: batteryLevel > 20 ? theme.colors.success : theme.colors.error,
            }}
          />
          <span
            style={{
              color: theme.colors.textSecondary,
              fontSize: theme.typography.sizes.xs,
              fontWeight: theme.typography.weights.medium,
            }}
          >
            {batteryLevel}%
          </span>
        </div>
      </div>
    </header>
  );
};

export default HeaderStatusBar;
