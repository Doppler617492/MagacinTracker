type OfflineActionType =
  | 'scan'
  | 'manual-entry'
  | 'pick-by-code'
  | 'short-pick'
  | 'not-found'
  | 'complete-document'
  | 'stock-count'
  | 'exception';

interface OfflineAction {
  id: string;
  type: OfflineActionType;
  taskItemId: string;
  payload: any;
  timestamp: number;
  retries: number;
}

export interface OfflineQueueState {
  size: number;
  pending: number;
  lastSyncedAt: number | null;
}

class OfflineQueue {
  private queue: OfflineAction[] = [];
  private readonly STORAGE_KEY = 'magacin_offline_queue';
  private readonly LAST_SYNC_KEY = 'magacin_offline_last_sync';
  private readonly MAX_RETRIES = 3;
  private listeners: Set<(state: OfflineQueueState) => void> = new Set();
  private lastSyncedAt: number | null = null;

  constructor() {
    this.loadFromStorage();
    this.loadLastSync();
  }

  private loadFromStorage() {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (stored) {
        this.queue = JSON.parse(stored);
      }
    } catch (error) {
      console.error('Failed to load offline queue from storage:', error);
      this.queue = [];
    }
  }

  private loadLastSync() {
    try {
      const stored = localStorage.getItem(this.LAST_SYNC_KEY);
      if (stored) {
        const value = parseInt(stored, 10);
        if (!Number.isNaN(value)) {
          this.lastSyncedAt = value;
        }
      }
    } catch (error) {
      console.error('Failed to load last sync timestamp:', error);
    }
  }

  private saveToStorage() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.queue));
    } catch (error) {
      console.error('Failed to save offline queue to storage:', error);
    }
  }

  private saveLastSync() {
    if (this.lastSyncedAt) {
      try {
        localStorage.setItem(this.LAST_SYNC_KEY, this.lastSyncedAt.toString());
      } catch (error) {
        console.error('Failed to persist last sync timestamp', error);
      }
    }
  }

  private notifyListeners() {
    const state = this.getState();
    this.listeners.forEach((listener) => {
      try {
        listener(state);
      } catch (error) {
        console.error('OfflineQueue listener error', error);
      }
    });
  }

  addAction(type: OfflineActionType, taskItemId: string, payload: any): string {
    if (type === 'pick-by-code') {
      console.warn('OfflineQueue: pick-by-code actions are not supported in manual mode – skipping enqueue.');
      return '';
    }
    const id = `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    const action: OfflineAction = {
      id,
      type,
      taskItemId,
      payload,
      timestamp: Date.now(),
      retries: 0
    };

    this.queue.push(action);
    this.saveToStorage();
    this.notifyListeners();
    return id;
  }

  getActions(): OfflineAction[] {
    return [...this.queue];
  }

  removeAction(id: string) {
    this.queue = this.queue.filter(action => action.id !== id);
    this.saveToStorage();
    if (this.queue.length === 0) {
      this.lastSyncedAt = Date.now();
      this.saveLastSync();
    }
    this.notifyListeners();
  }

  incrementRetries(id: string) {
    const action = this.queue.find(a => a.id === id);
    if (action) {
      action.retries++;
      this.saveToStorage();
      this.notifyListeners();
    }
  }

  getFailedActions(): OfflineAction[] {
    return this.queue.filter(action => action.retries >= this.MAX_RETRIES);
  }

  getPendingActions(): OfflineAction[] {
    return this.queue.filter(action => action.retries < this.MAX_RETRIES);
  }

  clear() {
    this.queue = [];
    this.saveToStorage();
    this.lastSyncedAt = Date.now();
    this.saveLastSync();
    this.notifyListeners();
  }

  getQueueSize(): number {
    return this.queue.length;
  }

  getState(): OfflineQueueState {
    return {
      size: this.queue.length,
      pending: this.getPendingActions().length,
      lastSyncedAt: this.lastSyncedAt,
    };
  }

  getLastSyncedAt(): number | null {
    return this.lastSyncedAt;
  }

  addListener(listener: (state: OfflineQueueState) => void) {
    this.listeners.add(listener);
    listener(this.getState());
  }

  removeListener(listener: (state: OfflineQueueState) => void) {
    this.listeners.delete(listener);
  }
}

export const offlineQueue = new OfflineQueue();

// Network status detection
export class NetworkManager {
  private isOnline = navigator.onLine;
  private listeners: ((isOnline: boolean) => void)[] = [];

  constructor() {
    window.addEventListener('online', () => {
      this.isOnline = true;
      this.notifyListeners();
    });

    window.addEventListener('offline', () => {
      this.isOnline = false;
      this.notifyListeners();
    });
  }

  isConnected(): boolean {
    return this.isOnline;
  }

  addListener(callback: (isOnline: boolean) => void) {
    this.listeners.push(callback);
  }

  removeListener(callback: (isOnline: boolean) => void) {
    this.listeners = this.listeners.filter(l => l !== callback);
  }

  private notifyListeners() {
    this.listeners.forEach(callback => callback(this.isOnline));
  }
}

export const networkManager = new NetworkManager();
