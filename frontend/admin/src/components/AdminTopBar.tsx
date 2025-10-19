/**
 * Manhattan-style Admin Top Bar
 * Design: Active WMS clarity-first pattern
 * Language: Serbian (Srpski)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Input, Avatar, Dropdown, Space, Typography } from 'antd';
import type { MenuProps } from 'antd';
import {
  SearchOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  InboxOutlined,
} from '@ant-design/icons';
import './AdminTopBar.css';

const { Header } = Layout;
const { Text } = Typography;

interface AdminTopBarProps {
  user: {
    firstName: string;
    lastName: string;
    role: string;
  };
  onLogout: () => void;
}

export const AdminTopBar: React.FC<AdminTopBarProps> = ({ user, onLogout }) => {
  const navigate = useNavigate();

  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profil',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Podešavanja',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Odjava',
      onClick: onLogout,
      danger: true,
    },
  ];

  const handleSearch = (value: string) => {
    if (value.trim()) {
      navigate(`/search?q=${encodeURIComponent(value.trim())}`);
    }
  };

  const initials = `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();

  return (
    <Header className="manhattan-topbar">
      {/* Left: Logo */}
      <div className="manhattan-topbar__left">
        <div className="manhattan-topbar__logo" onClick={() => navigate('/')}>
          <InboxOutlined className="manhattan-topbar__logo-icon" />
          <span className="manhattan-topbar__logo-text">Magacin Track</span>
        </div>
      </div>

      {/* Center: Global Search */}
      <div className="manhattan-topbar__center">
        <Input
          placeholder="Pretraži dokumente, artikle, zadatke..."
          prefix={<SearchOutlined />}
          onPressEnter={(e) => handleSearch(e.currentTarget.value)}
          className="manhattan-topbar__search"
          size="large"
          allowClear
        />
      </div>

      {/* Right: User Profile */}
      <div className="manhattan-topbar__right">
        <Dropdown menu={{ items: userMenuItems }} trigger={['click']} placement="bottomRight">
          <div className="manhattan-topbar__user">
            <Avatar size={40} className="manhattan-topbar__avatar">
              {initials}
            </Avatar>
            <Space direction="vertical" size={0} className="manhattan-topbar__user-info">
              <Text strong className="manhattan-topbar__user-name">
                {user.firstName} {user.lastName}
              </Text>
              <Text className="manhattan-topbar__user-role" type="secondary">
                {user.role}
              </Text>
            </Space>
          </div>
        </Dropdown>
      </div>
    </Header>
  );
};

export default AdminTopBar;

