/**
 * Manhattan-style Home Page
 * Design: Active WMS clarity-first grid layout
 * Language: Serbian (Srpski)
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Badge, Space, Typography } from 'antd';
import {
  CheckSquareOutlined,
  SearchOutlined,
  ContainerOutlined,
  SettingOutlined,
  UserOutlined,
  FilterOutlined,
} from '@ant-design/icons';
import { sr } from '../i18n/sr-comprehensive';
import { ManhattanHeader } from '../components/ManhattanHeader';
import './HomePageManhattan.css';

const { Text, Title } = Typography;

interface HomePageManhattanProps {
  user: {
    firstName: string;
    lastName: string;
    role: string;
  };
  team?: {
    name: string;
    shift: 'A' | 'B';
  };
  onLogout: () => void;
}

interface GridCardProps {
  icon: React.ReactNode;
  label: string;
  badge?: number;
  onClick: () => void;
  disabled?: boolean;
}

const GridCard: React.FC<GridCardProps> = ({ icon, label, badge, onClick, disabled }) => {
  return (
    <Card
      hoverable={!disabled}
      onClick={disabled ? undefined : onClick}
      className={`manhattan-grid-card ${disabled ? 'manhattan-grid-card--disabled' : ''}`}
      bodyStyle={{ padding: 0 }}
    >
      <div className="manhattan-grid-card__content">
        <div className="manhattan-grid-card__icon-wrapper">
          {badge !== undefined && badge > 0 ? (
            <Badge count={badge} offset={[0, 0]}>
              <div className="manhattan-grid-card__icon">{icon}</div>
            </Badge>
          ) : (
            <div className="manhattan-grid-card__icon">{icon}</div>
          )}
        </div>
        <Text className="manhattan-grid-card__label" strong>
          {label}
        </Text>
      </div>
    </Card>
  );
};

export const HomePageManhattan: React.FC<HomePageManhattanProps> = ({
  user,
  team,
  onLogout,
}) => {
  const navigate = useNavigate();
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [taskCount, setTaskCount] = useState(0);

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Fetch task count (mock for now - replace with real API call)
  useEffect(() => {
    // TODO: Replace with real API call
    // const fetchTaskCount = async () => {
    //   const response = await api.get('/worker/tasks');
    //   setTaskCount(response.data.length);
    // };
    // fetchTaskCount();
    setTaskCount(5); // Mock data
  }, []);

  const gridItems = [
    {
      icon: <CheckSquareOutlined />,
      label: sr.navigation.zadaci,
      badge: taskCount,
      onClick: () => navigate('/tasks'),
    },
    {
      icon: <SearchOutlined />,
      label: sr.navigation.pretragaArtikla,
      onClick: () => navigate('/lookup'),
    },
    {
      icon: <ContainerOutlined />,
      label: sr.navigation.popisMagacina,
      onClick: () => navigate('/stock-count'),
    },
    {
      icon: <SettingOutlined />,
      label: sr.navigation.podesavanja,
      onClick: () => navigate('/settings'),
    },
    {
      icon: <UserOutlined />,
      label: sr.navigation.profil,
      onClick: () => navigate('/profile'),
    },
  ];

  return (
    <div className="manhattan-home">
      <ManhattanHeader
        user={user}
        team={team}
        isOnline={isOnline}
        onLogout={onLogout}
      />

      <main className="manhattan-home__main">
        <div className="manhattan-home__container">
          {/* Welcome Section */}
          <div className="manhattan-home__welcome">
            <Title level={2} className="manhattan-home__title">
              {sr.navigation.pocetna}
            </Title>
            {team && (
              <Text className="manhattan-home__subtitle" type="secondary">
                {team.name} • {sr.shift[`smjena${team.shift}` as keyof typeof sr.shift]}
              </Text>
            )}
          </div>

          {/* Grid Cards */}
          <div className="manhattan-home__grid">
            {gridItems.map((item, index) => (
              <GridCard
                key={index}
                icon={item.icon}
                label={item.label}
                badge={item.badge}
                onClick={item.onClick}
              />
            ))}
          </div>

          {/* Offline Indicator */}
          {!isOnline && (
            <div className="manhattan-home__offline-banner">
              <Space>
                <Text strong style={{ color: '#DC3545' }}>
                  {sr.messages.nemaInternet}
                </Text>
                <Text type="secondary">
                  {sr.settings.offlineRezim}
                </Text>
              </Space>
            </div>
          )}
        </div>
      </main>
    </div>
  );
};

export default HomePageManhattan;

