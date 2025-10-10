import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Card, Switch, message } from 'antd';
import {
  SyncOutlined,
  LogoutOutlined,
  MobileOutlined,
  SettingOutlined,
  GlobalOutlined,
} from '@ant-design/icons';
import HeaderStatusBar from '../components/HeaderStatusBar';
import BottomNav from '../components/BottomNav';
import { theme } from '../theme';
import { logout } from '../api';

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const [autoSync, setAutoSync] = useState(true);
  const [notifications, setNotifications] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);

  const handleLogout = () => {
    logout();
    message.success('Uspješno ste se odjavili');
    navigate('/login');
  };

  const handleSync = async () => {
    setIsSyncing(true);
    message.info('Sinhronizacija u toku...');
    
    // Simulate sync
    setTimeout(() => {
      setIsSyncing(false);
      message.success('Sinhronizacija završena');
    }, 2000);
  };

  const handleClearCache = () => {
    localStorage.clear();
    message.success('Keš memorija očišćena');
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: theme.colors.background,
        display: 'flex',
        flexDirection: 'column',
        paddingBottom: '80px',
      }}
    >
      <HeaderStatusBar
        warehouseName="Transit Warehouse"
        userName="Radnik"
        userRole="Magacioner"
        isOnline={navigator.onLine}
        isSyncing={isSyncing}
        onLogout={handleLogout}
      />

      <div
        style={{
          flex: 1,
          padding: theme.spacing.lg,
          display: 'flex',
          flexDirection: 'column',
          gap: theme.spacing.lg,
        }}
      >
        <h2
          style={{
            color: theme.colors.text,
            fontSize: theme.typography.sizes.lg,
            fontWeight: theme.typography.weights.bold,
            margin: 0,
            letterSpacing: '0.5px',
          }}
        >
          POSTAVKE
        </h2>

        {/* Sync Section */}
        <div
          style={{
            background: theme.colors.cardBackground,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.lg,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.sm,
              marginBottom: theme.spacing.md,
            }}
          >
            <SyncOutlined style={{ fontSize: '18px', color: theme.colors.accent }} />
            <h3 style={{ color: theme.colors.text, margin: 0, fontSize: theme.typography.sizes.base }}>
              Sinhronizacija
            </h3>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: theme.spacing.md,
            }}
          >
            <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
              Automatska sinhronizacija
            </span>
            <Switch checked={autoSync} onChange={setAutoSync} />
          </div>

          <Button
            type="primary"
            icon={<SyncOutlined spin={isSyncing} />}
            onClick={handleSync}
            loading={isSyncing}
            block
            style={{
              background: theme.colors.primary,
              borderColor: theme.colors.primary,
              height: '44px',
              fontSize: theme.typography.sizes.base,
            }}
          >
            Sinhronizuj sada
          </Button>
        </div>

        {/* Notifications Section */}
        <div
          style={{
            background: theme.colors.cardBackground,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.lg,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.sm,
              marginBottom: theme.spacing.md,
            }}
          >
            <MobileOutlined style={{ fontSize: '18px', color: theme.colors.accent }} />
            <h3 style={{ color: theme.colors.text, margin: 0, fontSize: theme.typography.sizes.base }}>
              Obavještenja
            </h3>
          </div>

          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
              Push obavještenja
            </span>
            <Switch checked={notifications} onChange={setNotifications} />
          </div>
        </div>

        {/* App Info Section */}
        <div
          style={{
            background: theme.colors.cardBackground,
            border: `1px solid ${theme.colors.border}`,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.lg,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.sm,
              marginBottom: theme.spacing.md,
            }}
          >
            <SettingOutlined style={{ fontSize: '18px', color: theme.colors.accent }} />
            <h3 style={{ color: theme.colors.text, margin: 0, fontSize: theme.typography.sizes.base }}>
              Aplikacija
            </h3>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: `${theme.spacing.sm} 0`,
              }}
            >
              <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
                Verzija
              </span>
              <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm }}>1.0.0</span>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: `${theme.spacing.sm} 0`,
              }}
            >
              <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
                Uređaj
              </span>
              <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm }}>
                {navigator.userAgent.includes('Mobile') ? 'Mobilni' : 'Desktop'}
              </span>
            </div>

            <Button
              onClick={handleClearCache}
              style={{
                marginTop: theme.spacing.sm,
                height: '40px',
              }}
            >
              Očisti keš memoriju
            </Button>
          </div>
        </div>

        {/* Logout Button */}
        <Button
          danger
          type="primary"
          icon={<LogoutOutlined />}
          onClick={handleLogout}
          block
          style={{
            height: '48px',
            fontSize: theme.typography.sizes.base,
            fontWeight: theme.typography.weights.semibold,
            marginTop: theme.spacing.md,
          }}
        >
          Odjavi se
        </Button>
      </div>

      <BottomNav />
    </div>
  );
};

export default SettingsPage;

