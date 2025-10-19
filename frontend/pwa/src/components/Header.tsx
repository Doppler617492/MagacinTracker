import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Badge, Dropdown, Menu, Modal } from 'antd';
import { 
  User, 
  LogOut, 
  Settings, 
  Bell, 
  Search, 
  ScanBarcode, 
  Wifi, 
  WifiOff, 
  CheckCircle, 
  Clock, 
  AlertCircle,
  Battery,
  BatteryCharging,
  Menu as MenuIcon
} from 'lucide-react';
import { useHeader } from '../contexts/HeaderContext';
import { logout } from '../api';
import { useTranslation } from '../hooks/useTranslation';
import '../styles/header.css';

const Header: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');
  const {
    user,
    teamName,
    teamMembers,
    currentShift,
    shiftTimeRemaining,
    timeUntilBreak,
    isOnline,
    syncStatus,
    pendingActionsCount,
    batteryLevel,
    batteryCharging,
    alerts,
    unreadAlertsCount,
    markAlertAsRead,
    clearAllAlerts,
  } = useHeader();

  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const [notificationsVisible, setNotificationsVisible] = useState(false);
  const [logoutModalVisible, setLogoutModalVisible] = useState(false);

  const handleLogout = () => {
    setLogoutModalVisible(true);
  };

  const confirmLogout = () => {
    logout();
    navigate('/login');
  };

  const handleLogoClick = () => {
    navigate('/');
  };

  const handleSearchClick = () => {
    navigate('/lookup');
  };

  const handleScanClick = () => {
    // Open scan modal or navigate to scan page
    console.log('Opening barcode scanner...');
  };

  const formatTime = (num: number) => String(num).padStart(2, '0');

  const getInitials = () => {
    if (!user) return 'U';
    const firstInitial = user.first_name?.charAt(0) || '';
    const lastInitial = user.last_name?.charAt(0) || '';
    return (firstInitial + lastInitial).toUpperCase() || 'U';
  };

  const profileMenu = (
    <Menu>
      <Menu.Item key="profile" icon={<User size={16} />} onClick={() => navigate('/settings')}>
        Profile
      </Menu.Item>
      <Menu.Item key="settings" icon={<Settings size={16} />} onClick={() => navigate('/settings')}>
        Settings
      </Menu.Item>
      <Menu.Divider />
      <Menu.Item key="logout" icon={<LogOut size={16} />} onClick={handleLogout} danger>
        Logout
      </Menu.Item>
    </Menu>
  );

  return (
    <>
      <header className="wms-header">
        <div className="wms-header-container">
          {/* Left Section: Logo & Team Info */}
          <div className="wms-header-left">
            <div className="wms-header-logo" onClick={handleLogoClick} role="button" tabIndex={0} aria-label="Navigate to home">
              <div className="wms-logo-icon">MT</div>
              <div className="wms-logo-text">
                <div className="wms-logo-title">Magacin Track</div>
                <div className="wms-logo-subtitle">WMS</div>
              </div>
            </div>

            <div className="wms-header-team">
              <div className="wms-team-name">Team: {teamName}</div>
              <div className="wms-team-members">
                {teamMembers.map((member, idx) => (
                  <span key={member.id}>
                    {member.firstName} {member.lastName}
                    {idx < teamMembers.length - 1 && ' & '}
                  </span>
                ))}
              </div>
            </div>
          </div>

          {/* Center Section: Shift Timer */}
          {currentShift && (
            <div className="wms-header-center">
              <div className="wms-shift-timer">
                {shiftTimeRemaining && (
                  <div className="wms-timer-display">
                    <Clock size={20} className="wms-timer-icon" />
                    <span className="wms-timer-value">
                      {formatTime(shiftTimeRemaining.hours)}:
                      {formatTime(shiftTimeRemaining.minutes)}:
                      {formatTime(shiftTimeRemaining.seconds)}
                    </span>
                  </div>
                )}
                <div className="wms-shift-info">
                  <span className="wms-shift-badge">{currentShift.name} {currentShift.startTime}-{currentShift.endTime}</span>
                  {timeUntilBreak !== null && timeUntilBreak > 0 && timeUntilBreak <= 15 && (
                    <span className="wms-break-notice">Break in {timeUntilBreak} min</span>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Right Section: Status & Actions */}
          <div className="wms-header-right">
            {/* Status Indicators */}
            <div className="wms-status-indicators">
              {/* Network Status */}
              <div className={`wms-status-badge ${isOnline ? 'status-online' : 'status-offline'}`} aria-label={isOnline ? 'Online' : 'Offline'}>
                {isOnline ? <Wifi size={18} /> : <WifiOff size={18} />}
                <span className="wms-status-text">{isOnline ? 'Online' : 'Offline'}</span>
              </div>

              {/* Sync Status */}
              <div className={`wms-status-badge status-${syncStatus}`} aria-label={`Sync status: ${syncStatus}`}>
                {syncStatus === 'synced' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                <span className="wms-status-text">
                  {syncStatus === 'synced' ? 'Synced' : `${pendingActionsCount} pending`}
                </span>
              </div>

              {/* Battery Status */}
              {batteryLevel !== null && (
                <div className={`wms-status-badge status-battery ${batteryLevel <= 20 ? 'status-low' : ''}`} aria-label={`Battery: ${batteryLevel}%`}>
                  {batteryCharging ? <BatteryCharging size={18} /> : <Battery size={18} />}
                  <span className="wms-status-text">{batteryLevel}%</span>
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="wms-header-actions">
              <button 
                className="wms-action-btn" 
                onClick={handleSearchClick}
                aria-label="Search or lookup"
                title="Search"
              >
                <Search size={22} />
              </button>

              <button 
                className="wms-action-btn" 
                onClick={handleScanClick}
                aria-label="Scan barcode"
                title="Scan"
              >
                <ScanBarcode size={22} />
              </button>

              {/* Notifications */}
              <Badge count={unreadAlertsCount} offset={[-5, 5]}>
                <button 
                  className="wms-action-btn" 
                  onClick={() => setNotificationsVisible(!notificationsVisible)}
                  aria-label={`Notifications: ${unreadAlertsCount} unread`}
                  title="Notifications"
                >
                  <Bell size={22} />
                </button>
              </Badge>

              {/* Profile */}
              <Dropdown overlay={profileMenu} trigger={['click']} placement="bottomRight">
                <div className="wms-profile-avatar" role="button" tabIndex={0} aria-label="User profile menu">
                  {getInitials()}
                </div>
              </Dropdown>
            </div>

            {/* Mobile Menu Toggle */}
            <button 
              className="wms-mobile-menu-btn"
              onClick={() => setMobileMenuVisible(!mobileMenuVisible)}
              aria-label="Toggle mobile menu"
            >
              <MenuIcon size={24} />
            </button>
          </div>
        </div>

        {/* Mobile Menu Drawer */}
        {mobileMenuVisible && (
          <div className="wms-mobile-menu">
            <div className="wms-mobile-menu-section">
              <h4>Status</h4>
              <div className="wms-mobile-status">
                <div className={`wms-mobile-status-item ${isOnline ? 'online' : 'offline'}`}>
                  {isOnline ? <Wifi size={18} /> : <WifiOff size={18} />}
                  <span>{isOnline ? 'Online' : 'Offline'}</span>
                </div>
                <div className={`wms-mobile-status-item ${syncStatus === 'synced' ? 'synced' : 'pending'}`}>
                  {syncStatus === 'synced' ? <CheckCircle size={18} /> : <AlertCircle size={18} />}
                  <span>{syncStatus === 'synced' ? 'Synced' : `${pendingActionsCount} pending`}</span>
                </div>
                {batteryLevel !== null && (
                  <div className="wms-mobile-status-item">
                    {batteryCharging ? <BatteryCharging size={18} /> : <Battery size={18} />}
                    <span>{batteryLevel}%</span>
                  </div>
                )}
              </div>
            </div>
            <div className="wms-mobile-menu-actions">
              <button onClick={handleSearchClick}>
                <Search size={20} /> Search
              </button>
              <button onClick={handleScanClick}>
                <ScanBarcode size={20} /> Scan
              </button>
              <button onClick={() => { setMobileMenuVisible(false); navigate('/settings'); }}>
                <Settings size={20} /> Settings
              </button>
              <button onClick={handleLogout} className="logout-btn">
                <LogOut size={20} /> Logout
              </button>
            </div>
          </div>
        )}
      </header>

      {/* Notifications Panel */}
      {notificationsVisible && (
        <div className="wms-notifications-panel">
          <div className="wms-notifications-header">
            <h3>Notifications</h3>
            <button onClick={clearAllAlerts} className="wms-clear-all-btn">Clear All</button>
          </div>
          <div className="wms-notifications-list">
            {alerts.length === 0 ? (
              <div className="wms-no-notifications">No notifications</div>
            ) : (
              alerts.map(alert => (
                <div 
                  key={alert.id} 
                  className={`wms-notification-item ${alert.read ? 'read' : 'unread'}`}
                  onClick={() => markAlertAsRead(alert.id)}
                >
                  <div className="wms-notification-icon">
                    {alert.type === 'task' && <CheckCircle size={20} />}
                    {alert.type === 'exception' && <AlertCircle size={20} />}
                    {alert.type === 'system' && <Bell size={20} />}
                  </div>
                  <div className="wms-notification-content">
                    <div className="wms-notification-message">{alert.message}</div>
                    <div className="wms-notification-time">
                      {new Date(alert.timestamp).toLocaleTimeString('sr-RS', { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                  {!alert.read && <div className="wms-notification-badge"></div>}
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* Logout Confirmation Modal */}
      <Modal
        title="Logout Confirmation"
        open={logoutModalVisible}
        onOk={confirmLogout}
        onCancel={() => setLogoutModalVisible(false)}
        okText="Logout"
        cancelText="Cancel"
        okButtonProps={{ danger: true }}
      >
        <p>Are you sure you want to logout? Any pending actions will remain in the queue and will be synced when you login again.</p>
      </Modal>

      {/* Offline Banner */}
      {!isOnline && (
        <div className="wms-offline-banner">
          <WifiOff size={18} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '8px' }} />
          You are offline. All actions will be queued and synced when you reconnect.
        </div>
      )}
    </>
  );
};

export default Header;

