import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { getStoredUserProfile, StoredUserProfile } from '../api';
import { networkManager } from '../lib/offlineQueue';

interface ShiftInfo {
  name: string;
  startTime: string;
  endTime: string;
  breakTime?: string;
  breakDuration?: number; // minutes
}

interface TeamMember {
  id: string;
  firstName: string;
  lastName: string;
}

interface Alert {
  id: string;
  type: 'task' | 'exception' | 'system';
  message: string;
  timestamp: string;
  read: boolean;
}

interface HeaderContextType {
  user: StoredUserProfile | null;
  teamName: string;
  teamMembers: TeamMember[];
  currentShift: ShiftInfo | null;
  shiftTimeRemaining: { hours: number; minutes: number; seconds: number } | null;
  timeUntilBreak: number | null; // minutes
  isOnline: boolean;
  syncStatus: 'synced' | 'pending' | 'syncing';
  pendingActionsCount: number;
  batteryLevel: number | null;
  batteryCharging: boolean;
  alerts: Alert[];
  unreadAlertsCount: number;
  refreshShiftInfo: () => void;
  markAlertAsRead: (alertId: string) => void;
  clearAllAlerts: () => void;
}

const HeaderContext = createContext<HeaderContextType | undefined>(undefined);

export const useHeader = () => {
  const context = useContext(HeaderContext);
  if (!context) {
    throw new Error('useHeader must be used within HeaderProvider');
  }
  return context;
};

interface HeaderProviderProps {
  children: ReactNode;
}

export const HeaderProvider: React.FC<HeaderProviderProps> = ({ children }) => {
  const [user, setUser] = useState<StoredUserProfile | null>(null);
  const [teamName, setTeamName] = useState('');
  const [teamMembers, setTeamMembers] = useState<TeamMember[]>([]);
  const [currentShift, setCurrentShift] = useState<ShiftInfo | null>(null);
  const [shiftTimeRemaining, setShiftTimeRemaining] = useState<{ hours: number; minutes: number; seconds: number } | null>(null);
  const [timeUntilBreak, setTimeUntilBreak] = useState<number | null>(null);
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [syncStatus, setSyncStatus] = useState<'synced' | 'pending' | 'syncing'>('synced');
  const [pendingActionsCount, setPendingActionsCount] = useState(0);
  const [batteryLevel, setBatteryLevel] = useState<number | null>(null);
  const [batteryCharging, setBatteryCharging] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // Load user profile and team info
  useEffect(() => {
    const profile = getStoredUserProfile();
    if (profile) {
      setUser(profile);
      setTeamName(profile.team_name || 'No Team');
      // Parse team members from profile or fetch from API
      // For now, using mock data - this should be fetched from API
      if (profile.team_name) {
        setTeamMembers([
          { id: '1', firstName: profile.first_name || '', lastName: profile.last_name || '' }
        ]);
      }
    }
  }, []);

  // Initialize shift info (this should be fetched from API or calculated based on team schedule)
  useEffect(() => {
    // Mock shift data - replace with actual API call
    const now = new Date();
    const currentHour = now.getHours();
    
    let shift: ShiftInfo | null = null;
    if (currentHour >= 8 && currentHour < 16) {
      shift = {
        name: 'Shift A',
        startTime: '08:00',
        endTime: '16:00',
        breakTime: '12:00',
        breakDuration: 30
      };
    } else if (currentHour >= 16 && currentHour < 24) {
      shift = {
        name: 'Shift B',
        startTime: '16:00',
        endTime: '24:00',
        breakTime: '20:00',
        breakDuration: 30
      };
    } else if (currentHour >= 0 && currentHour < 8) {
      shift = {
        name: 'Shift C',
        startTime: '00:00',
        endTime: '08:00',
        breakTime: '04:00',
        breakDuration: 30
      };
    }
    
    setCurrentShift(shift);
  }, []);

  // Shift timer - updates every second
  useEffect(() => {
    if (!currentShift) return;

    const updateTimer = () => {
      const now = new Date();
      const [endHour, endMinute] = currentShift.endTime.split(':').map(Number);
      const endTime = new Date();
      endTime.setHours(endHour, endMinute, 0, 0);
      
      // If end time is earlier than now, it's tomorrow
      if (endTime < now) {
        endTime.setDate(endTime.getDate() + 1);
      }
      
      const diff = endTime.getTime() - now.getTime();
      
      if (diff > 0) {
        const hours = Math.floor(diff / (1000 * 60 * 60));
        const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((diff % (1000 * 60)) / 1000);
        
        setShiftTimeRemaining({ hours, minutes, seconds });
      } else {
        setShiftTimeRemaining(null);
      }

      // Calculate time until break
      if (currentShift.breakTime) {
        const [breakHour, breakMinute] = currentShift.breakTime.split(':').map(Number);
        const breakTime = new Date();
        breakTime.setHours(breakHour, breakMinute, 0, 0);
        
        if (breakTime > now) {
          const diffToBreak = breakTime.getTime() - now.getTime();
          const minutesToBreak = Math.floor(diffToBreak / (1000 * 60));
          setTimeUntilBreak(minutesToBreak);
        } else {
          setTimeUntilBreak(null);
        }
      }
    };

    updateTimer();
    const interval = setInterval(updateTimer, 1000);

    return () => clearInterval(interval);
  }, [currentShift]);

  // Network status listener
  useEffect(() => {
    const handleNetworkChange = (online: boolean) => {
      setIsOnline(online);
    };
    
    networkManager.addListener(handleNetworkChange);
    
    return () => {
      networkManager.removeListener(handleNetworkChange);
    };
  }, []);

  // Sync queue status
  useEffect(() => {
    const updateSyncStatus = () => {
      const queue = localStorage.getItem('offline_queue');
      if (queue) {
        try {
          const actions = JSON.parse(queue);
          setPendingActionsCount(actions.length);
          setSyncStatus(actions.length > 0 ? 'pending' : 'synced');
        } catch (e) {
          setPendingActionsCount(0);
          setSyncStatus('synced');
        }
      } else {
        setPendingActionsCount(0);
        setSyncStatus('synced');
      }
    };

    updateSyncStatus();
    const interval = setInterval(updateSyncStatus, 2000);

    return () => clearInterval(interval);
  }, []);

  // Battery status (if supported)
  useEffect(() => {
    const updateBatteryStatus = async () => {
      if ('getBattery' in navigator) {
        try {
          const battery: any = await (navigator as any).getBattery();
          setBatteryLevel(Math.round(battery.level * 100));
          setBatteryCharging(battery.charging);

          battery.addEventListener('levelchange', () => {
            setBatteryLevel(Math.round(battery.level * 100));
          });
          battery.addEventListener('chargingchange', () => {
            setBatteryCharging(battery.charging);
          });
        } catch (e) {
          console.log('Battery API not supported');
        }
      }
    };

    updateBatteryStatus();
  }, []);

  // Mock alerts - replace with actual API call
  useEffect(() => {
    // This should fetch from /api/worker/alerts?limit=5
    const mockAlerts: Alert[] = [
      {
        id: '1',
        type: 'task',
        message: 'New task assigned: Document #12345',
        timestamp: new Date().toISOString(),
        read: false
      }
    ];
    setAlerts(mockAlerts);
  }, []);

  const refreshShiftInfo = () => {
    // Re-fetch shift info from API
    console.log('Refreshing shift info...');
  };

  const markAlertAsRead = (alertId: string) => {
    setAlerts(prev => prev.map(alert => 
      alert.id === alertId ? { ...alert, read: true } : alert
    ));
  };

  const clearAllAlerts = () => {
    setAlerts([]);
  };

  const unreadAlertsCount = alerts.filter(a => !a.read).length;

  const value: HeaderContextType = {
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
    refreshShiftInfo,
    markAlertAsRead,
    clearAllAlerts,
  };

  return <HeaderContext.Provider value={value}>{children}</HeaderContext.Provider>;
};

