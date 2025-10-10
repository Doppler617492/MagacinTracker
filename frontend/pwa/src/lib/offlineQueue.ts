interface OfflineAction {
  id: string;
  type: 'scan' | 'manual';
  taskItemId: string;
  payload: any;
  timestamp: number;
  retries: number;
}

class OfflineQueue {
  private queue: OfflineAction[] = [];
  private readonly STORAGE_KEY = 'magacin_offline_queue';
  private readonly MAX_RETRIES = 3;

  constructor() {
    this.loadFromStorage();
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

  private saveToStorage() {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(this.queue));
    } catch (error) {
      console.error('Failed to save offline queue to storage:', error);
    }
  }

  addAction(type: 'scan' | 'manual' | 'pick-by-code' | 'short-pick' | 'not-found' | 'complete-document', taskItemId: string, payload: any): string {
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
    return id;
  }

  getActions(): OfflineAction[] {
    return [...this.queue];
  }

  removeAction(id: string) {
    this.queue = this.queue.filter(action => action.id !== id);
    this.saveToStorage();
  }

  incrementRetries(id: string) {
    const action = this.queue.find(a => a.id === id);
    if (action) {
      action.retries++;
      this.saveToStorage();
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
  }

  getQueueSize(): number {
    return this.queue.length;
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
