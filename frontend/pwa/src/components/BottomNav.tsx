import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  UnorderedListOutlined,
  BarChartOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { theme } from '../theme';

interface NavItem {
  key: string;
  icon: React.ReactNode;
  label: string;
  path: string;
}

const navItems: NavItem[] = [
  {
    key: 'home',
    icon: <HomeOutlined />,
    label: 'Početna',
    path: '/',
  },
  {
    key: 'tasks',
    icon: <UnorderedListOutlined />,
    label: 'Zadaci',
    path: '/',
  },
  {
    key: 'reports',
    icon: <BarChartOutlined />,
    label: 'Izvještaji',
    path: '/reports',
  },
  {
    key: 'settings',
    icon: <SettingOutlined />,
    label: 'Postavke',
    path: '/settings',
  },
];

const BottomNav: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  return (
    <nav
      style={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: theme.zIndex.bottomNav,
        background: theme.colors.cardBackground,
        borderTop: `1px solid ${theme.colors.border}`,
        boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        justifyContent: 'space-around',
        padding: `${theme.spacing.sm} 0`,
      }}
    >
      {navItems.map((item) => {
        const active = isActive(item.path);
        return (
          <button
            key={item.key}
            onClick={() => navigate(item.path)}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '4px',
              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
              transition: 'all 0.2s',
              color: active ? theme.colors.accent : theme.colors.textSecondary,
            }}
            onMouseEnter={(e) => {
              if (!active) {
                e.currentTarget.style.color = theme.colors.text;
              }
            }}
            onMouseLeave={(e) => {
              if (!active) {
                e.currentTarget.style.color = theme.colors.textSecondary;
              }
            }}
          >
            <div style={{ fontSize: '22px', lineHeight: 1 }}>
              {item.icon}
            </div>
            <span
              style={{
                fontSize: theme.typography.sizes.xs,
                fontWeight: active ? theme.typography.weights.semibold : theme.typography.weights.normal,
                letterSpacing: '0.3px',
              }}
            >
              {item.label}
            </span>
            {active && (
              <div
                style={{
                  position: 'absolute',
                  bottom: 0,
                  left: '50%',
                  transform: 'translateX(-50%)',
                  width: '40%',
                  height: '3px',
                  background: theme.colors.accent,
                  borderRadius: '2px 2px 0 0',
                }}
              />
            )}
          </button>
        );
      })}
    </nav>
  );
};

export default BottomNav;

