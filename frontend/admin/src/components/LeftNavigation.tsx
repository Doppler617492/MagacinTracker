/**
 * Manhattan-style Left Navigation
 * Design: Active WMS Information Architecture (IA)
 * Language: Serbian (Srpski)
 */

import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Menu, Layout } from 'antd';
import type { MenuProps } from 'antd';
import {
  FileTextOutlined,
  CheckSquareOutlined,
  UploadOutlined,
  InboxOutlined,
  BarcodeOutlined,
  BarChartOutlined,
  FileSearchOutlined,
  RobotOutlined,
  MonitorOutlined,
  ThunderboltOutlined,
  UserOutlined,
  SettingOutlined,
  HomeOutlined,
} from '@ant-design/icons';
import './LeftNavigation.css';

const { Sider } = Layout;

type MenuItem = Required<MenuProps>['items'][number];

function getItem(
  label: React.ReactNode,
  key: string,
  icon?: React.ReactNode,
  children?: MenuItem[],
  type?: 'group',
): MenuItem {
  return {
    key,
    icon,
    children,
    label,
    type,
  } as MenuItem;
}

const menuItems: MenuItem[] = [
  getItem('Početna', '/', <HomeOutlined />),
  
  { type: 'divider' },
  
  getItem('OPERACIJE', 'operacije-group', null, [
    getItem('Trebovanja', '/trebovanja', <FileTextOutlined />),
    getItem('Zadužnice', '/zaduznice', <CheckSquareOutlined />),
    getItem('Import', '/import', <UploadOutlined />),
  ], 'group'),
  
  getItem('KATALOG', 'katalog-group', null, [
    getItem('Artikli', '/artikli', <InboxOutlined />),
    getItem('Barkodovi', '/barkodovi', <BarcodeOutlined />),
  ], 'group'),
  
  getItem('ANALITIKA', 'analitika-group', null, [
    getItem('KPI', '/kpi', <BarChartOutlined />),
    getItem('Izveštaji', '/reports', <FileSearchOutlined />),
    getItem('AI Asistent', '/ai-hub', <RobotOutlined />),
  ], 'group'),
  
  getItem('UŽIVO', 'uzivo-group', null, [
    getItem('TV Dashboard', '/tv-dashboard', <MonitorOutlined />),
    getItem('Live Ops', '/live-ops', <ThunderboltOutlined />),
  ], 'group'),
  
  getItem('ADMINISTRACIJA', 'admin-group', null, [
    getItem('Korisnici i uloge', '/users', <UserOutlined />),
    getItem('Podešavanja', '/settings', <SettingOutlined />),
  ], 'group'),
];

interface LeftNavigationProps {
  collapsed?: boolean;
  onCollapse?: (collapsed: boolean) => void;
}

export const LeftNavigation: React.FC<LeftNavigationProps> = ({
  collapsed = false,
  onCollapse,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [collapsedState, setCollapsedState] = useState(collapsed);

  const handleMenuClick: MenuProps['onClick'] = (e) => {
    navigate(e.key);
  };

  const handleCollapse = (value: boolean) => {
    setCollapsedState(value);
    onCollapse?.(value);
  };

  // Get current selected key from location
  const selectedKey = location.pathname;

  return (
    <Sider
      collapsible
      collapsed={collapsedState}
      onCollapse={handleCollapse}
      width={240}
      className="manhattan-left-nav"
      breakpoint="lg"
      collapsedWidth={80}
    >
      {/* Logo Section */}
      <div className="manhattan-left-nav__logo">
        {collapsedState ? (
          <div className="manhattan-left-nav__logo-collapsed">
            <InboxOutlined style={{ fontSize: 24 }} />
          </div>
        ) : (
          <div className="manhattan-left-nav__logo-full">
            <InboxOutlined style={{ fontSize: 28, marginRight: 12 }} />
            <span className="manhattan-left-nav__logo-text">Magacin Track</span>
          </div>
        )}
      </div>

      {/* Navigation Menu */}
      <Menu
        theme="light"
        mode="inline"
        selectedKeys={[selectedKey]}
        onClick={handleMenuClick}
        items={menuItems}
        className="manhattan-left-nav__menu"
      />
    </Sider>
  );
};

export default LeftNavigation;

