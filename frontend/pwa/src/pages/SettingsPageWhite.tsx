/**
 * SettingsPage - White Enterprise Theme
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Switch, message } from 'antd';
import { ArrowLeft, User, Wifi, RefreshCw, LogOut, Info } from 'lucide-react';
import { whiteTheme } from '../theme-white';
import { logout, getStoredUserProfile, StoredUserProfile, getMyTeam, WorkerTeamInfo } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import { useQuery } from '@tanstack/react-query';
import type { OfflineQueueState } from '../lib/offlineQueue';
import { useTranslation } from '../hooks/useTranslation';

const SettingsPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [autoSync, setAutoSync] = useState(true);

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

  const { data: teamInfo } = useQuery<WorkerTeamInfo | null>({
    queryKey: ['my-team'],
    queryFn: getMyTeam,
    retry: false,
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleClearCache = () => {
    offlineQueue.clear();
    localStorage.clear();
    message.success('Cache cleared');
    setTimeout(() => window.location.reload(), 1000);
  };

  const formattedLastSync = lastSyncedAt
    ? new Date(lastSyncedAt).toLocaleString('sr-Latn-ME')
    : 'Never';

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
          <ArrowLeft size={16} /> Home
        </button>
        <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
          Settings
        </h1>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        {/* Worker Info */}
        <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
            <User size={24} color={whiteTheme.colors.primary} />
            <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
              Worker Profile
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: whiteTheme.spacing.sm }}>
            <div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Name</div>
              <div style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: whiteTheme.colors.text }}>
                {userProfile?.fullName || 'Worker'}
              </div>
            </div>
            <div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Role</div>
              <div style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: whiteTheme.colors.text }}>
                {userProfile?.role?.toUpperCase() || 'WORKER'}
              </div>
            </div>
            {teamInfo && (
              <>
                <div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Team</div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: whiteTheme.colors.text }}>
                    {teamInfo.team_name}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Partner</div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: whiteTheme.colors.text }}>
                    {teamInfo.partner_name}
                  </div>
                </div>
                <div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>Shift</div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: whiteTheme.colors.text }}>
                    Shift {teamInfo.shift}
                  </div>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Network Status */}
        <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
            <Wifi size={24} color={isOnline ? whiteTheme.colors.accent : whiteTheme.colors.textMuted} />
            <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
              Network Status
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: whiteTheme.spacing.sm }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Connection</span>
              <span style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: isOnline ? whiteTheme.colors.accent : whiteTheme.colors.error }}>
                {isOnline ? 'Online' : 'Offline'}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Pending Actions</span>
              <span style={{ fontSize: whiteTheme.typography.sizes.base, fontWeight: whiteTheme.typography.weights.medium, color: pendingSync > 0 ? whiteTheme.colors.warning : whiteTheme.colors.accent }}>
                {pendingSync}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Last Sync</span>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.text }}>
                {formattedLastSync}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: whiteTheme.spacing.sm }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Auto-sync (every 60s)</span>
              <Switch checked={autoSync} onChange={setAutoSync} />
            </div>
          </div>
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: whiteTheme.spacing.md }}>
          <Button
            size="large"
            icon={<RefreshCw size={18} />}
            onClick={() => window.location.reload()}
            disabled={pendingSync === 0}
          >
            Sync Now ({pendingSync} pending)
          </Button>
          <Button
            size="large"
            danger
            onClick={handleClearCache}
          >
            Clear Cache & Data
          </Button>
          <Button
            type="primary"
            danger
            size="large"
            icon={<LogOut size={18} />}
            onClick={handleLogout}
          >
            Logout
          </Button>
        </div>

        {/* App Info */}
        <div className="wms-card" style={{ marginTop: whiteTheme.spacing.lg }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
            <Info size={24} color={whiteTheme.colors.info} />
            <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
              App Information
            </div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: whiteTheme.spacing.xs }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Version</span>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: whiteTheme.typography.weights.medium }}>1.0.0</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Build</span>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: whiteTheme.typography.weights.medium }}>2025.10.18</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>Theme</span>
              <span style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: whiteTheme.typography.weights.medium }}>Enterprise White</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsPageWhite;

