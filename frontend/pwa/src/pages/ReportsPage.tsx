import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Button } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import HeaderStatusBar from '../components/HeaderStatusBar';
import BottomNav from '../components/BottomNav';
import { theme } from '../theme';
import { logout, getStoredUserProfile, StoredUserProfile } from '../api';
import { offlineQueue } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(getStoredUserProfile()?.location ?? 'Tranzitno skladište');
  const [isOnline, setIsOnline] = useState<boolean>(navigator.onLine);
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);
    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const handleQueue = (state: OfflineQueueState) => {
      setPendingSync(state.pending);
      setLastSyncedAt(state.lastSyncedAt);
    };

    offlineQueue.addListener(handleQueue);
    setUserProfile(getStoredUserProfile());

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      offlineQueue.removeListener(handleQueue);
    };
  }, []);

  useEffect(() => {
    if (userProfile?.location) {
      setWarehouseName(userProfile.location);
    }
  }, [userProfile?.location]);

  const displayRole = userProfile?.role
    ? userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)
    : 'Magacioner';

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
        warehouseName={warehouseName}
        userName={userProfile?.fullName ?? 'Radnik'}
        userRole={displayRole}
        userEmail={userProfile?.email}
        isOnline={isOnline}
        pendingSyncCount={pendingSync}
        lastSyncedAt={lastSyncedAt}
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
          IZVJEŠTAJI
        </h2>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: theme.spacing['2xl'],
            flex: 1,
          }}
        >
          <Empty
            image={<FileTextOutlined style={{ fontSize: '64px', color: theme.colors.textSecondary }} />}
            description={
              <span style={{ color: theme.colors.textSecondary }}>
                Nema dostupnih izvještaja
              </span>
            }
          >
            <Button type="primary" onClick={() => navigate('/')}>
              Povratak na zadatke
            </Button>
          </Empty>
        </div>
      </div>

      <BottomNav />
    </div>
  );
};

export default ReportsPage;
