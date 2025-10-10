import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Empty, Button } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';
import HeaderStatusBar from '../components/HeaderStatusBar';
import BottomNav from '../components/BottomNav';
import { theme } from '../theme';
import { logout } from '../api';

const ReportsPage: React.FC = () => {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
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
        isSyncing={false}
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

