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
  isOnline?: boolean;
  isSyncing?: boolean;
  onLogout?: () => void;
}

const HeaderStatusBar: React.FC<HeaderStatusBarProps> = ({
  warehouseName = 'Transit Warehouse',
  userName = 'Worker',
  userRole = 'Magacioner',
  isOnline = true,
  isSyncing = false,
  onLogout,
}) => {
  const [batteryLevel, setBatteryLevel] = useState<number>(100);
  const [lastSync, setLastSync] = useState<string>('Just now');

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

  const userMenuItems: MenuProps['items'] = [
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
      key: 'sync',
      label: (
        <div style={{ padding: '4px 0' }}>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
            Posljednja sinhronizacija
          </div>
          <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm }}>
            {lastSync}
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
        <SyncOutlined
          spin={isSyncing}
          style={{
            fontSize: '16px',
            color: isSyncing ? theme.colors.primary : theme.colors.textSecondary,
          }}
        />

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

