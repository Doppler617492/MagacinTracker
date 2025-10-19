/**
 * Manhattan-style Header Component
 * Design: Active WMS clarity-first pattern
 * Language: Serbian (Srpski)
 */

import React from 'react';
import { Avatar, Badge, Button, Space, Typography } from 'antd';
import { 
  LogoutOutlined,
  WifiOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import { sr } from '../i18n/sr-comprehensive';
import { getShiftLabel, getShiftTime, getShiftPause } from '../i18n/sr-comprehensive';
import './ManhattanHeader.css';

const { Text } = Typography;

interface ManhattanHeaderProps {
  user: {
    firstName: string;
    lastName: string;
    role: string;
  };
  team?: {
    name: string;
    shift: 'A' | 'B';
  };
  isOnline: boolean;
  onLogout: () => void;
}

export const ManhattanHeader: React.FC<ManhattanHeaderProps> = ({
  user,
  team,
  isOnline,
  onLogout,
}) => {
  // Get user initials
  const initials = `${user.firstName[0]}${user.lastName[0]}`.toUpperCase();
  
  // Get role display in Serbian
  const roleMap: Record<string, string> = {
    admin: sr.user.admin,
    menadzer: sr.user.menadzer,
    sef: sr.user.sef,
    komercijalista: sr.user.komercijalista,
    magacioner: sr.user.magacioner,
  };
  const roleDisplay = roleMap[user.role.toLowerCase()] || user.role;

  return (
    <header className="manhattan-header">
      <div className="manhattan-header__left">
        {/* User Avatar with Initials */}
        <Avatar 
          size={44} 
          className="manhattan-header__avatar"
          style={{ backgroundColor: '#0D6EFD' }}
        >
          {initials}
        </Avatar>
        
        {/* User Info */}
        <div className="manhattan-header__user-info">
          <Text strong className="manhattan-header__name">
            {user.firstName} {user.lastName}
          </Text>
          <Text className="manhattan-header__role" type="secondary">
            {roleDisplay}
          </Text>
        </div>
      </div>

      <div className="manhattan-header__center">
        {team && (
          <div className="manhattan-header__shift-badge">
            <div className="shift-badge">
              <div className="shift-badge__main">
                <ClockCircleOutlined className="shift-badge__icon" />
                <Text strong>{getShiftLabel(team.shift)}</Text>
              </div>
              <div className="shift-badge__details">
                <Text className="shift-badge__time">
                  {getShiftTime(team.shift)}
                </Text>
                <Text className="shift-badge__pause" type="secondary">
                  {sr.shift.pauza}: {getShiftPause(team.shift)}
                </Text>
              </div>
              {team.name && (
                <Text className="shift-badge__team" type="secondary">
                  {team.name}
                </Text>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="manhattan-header__right">
        {/* Online/Offline Indicator */}
        <Badge 
          status={isOnline ? 'success' : 'error'} 
          text={
            <Text className="manhattan-header__status">
              {isOnline ? sr.header.online : sr.header.offline}
            </Text>
          }
        />
        
        {/* Logout Button */}
        <Button
          type="text"
          icon={<LogoutOutlined />}
          onClick={onLogout}
          className="manhattan-header__logout"
        >
          {sr.navigation.odjava}
        </Button>
      </div>
    </header>
  );
};

export default ManhattanHeader;

