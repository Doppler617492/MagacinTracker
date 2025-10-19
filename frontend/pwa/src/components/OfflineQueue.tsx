import { useEffect, useState } from 'react';
import { Badge, Button, Card, List, message, Space, Tag, Typography } from 'antd';
import { WifiOutlined, DisconnectOutlined, SyncOutlined, DeleteOutlined } from '@ant-design/icons';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import { whiteTheme } from '../theme-white';
import { useTranslation } from '../hooks/useTranslation';
import client from '../api';

const { Text } = Typography;

interface OfflineAction {
  id: string;
  type: 'scan' | 'manual-entry' | 'pick-by-code' | 'short-pick' | 'not-found' | 'complete-document';
  taskItemId: string;
  payload: any;
  timestamp: number;
  retries: number;
}

const OfflineQueueComponent = () => {
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [queue, setQueue] = useState<OfflineAction[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => {
      setIsOnline(online);
      if (online) {
        processQueue();
      }
    };

    networkManager.addListener(handleNetworkChange);
    const handleQueueState = () => {
      setQueue(offlineQueue.getActions());
    };
    offlineQueue.addListener(handleQueueState);
    updateQueue();

    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueueState);
    };
  }, []);

  const updateQueue = () => {
    setQueue(offlineQueue.getActions());
  };

  const processQueue = async () => {
    if (isProcessing || !isOnline) return;

    setIsProcessing(true);
    const pendingActions = offlineQueue.getPendingActions();

    for (const action of pendingActions) {
      try {
        if (action.type === 'scan') {
          await client.post(`/worker/tasks/${action.taskItemId}/scan`, action.payload);
        } else if (action.type === 'manual-entry') {
          await client.post(`/worker/tasks/${action.taskItemId}/manual-entry`, action.payload);
        } else if (action.type === 'pick-by-code') {
          message.info('Rad samo sa ručnim unosom – pick-by-code akcija uklonjena.');
          offlineQueue.removeAction(action.id);
          continue;
        } else if (action.type === 'short-pick') {
          await client.post(`/worker/tasks/${action.taskItemId}/short-pick`, action.payload);
        } else if (action.type === 'not-found') {
          await client.post(`/worker/tasks/${action.taskItemId}/not-found`, action.payload);
        } else if (action.type === 'complete-document') {
          await client.post(`/worker/documents/${action.taskItemId}/complete`, action.payload);
        } else if (action.type === 'stock-count') {
          await client.post(`/counts`, action.payload);
        } else if (action.type === 'exception') {
          await client.post(`/exceptions`, action.payload);
        }
        
        offlineQueue.removeAction(action.id);
        message.success(`Akcija ${action.type} uspešno poslata`);
      } catch (error) {
        offlineQueue.incrementRetries(action.id);
        console.error(`Failed to process action ${action.id}:`, error);
      }
    }

    updateQueue();
    setIsProcessing(false);
  };

  const clearQueue = () => {
    offlineQueue.clear();
    updateQueue();
    message.success('Offline queue je obrisana');
  };

  const removeAction = (actionId: string) => {
    offlineQueue.removeAction(actionId);
    updateQueue();
    message.success('Akcija uklonjena iz queue-a');
  };

  if (queue.length === 0 && isOnline) {
    return null;
  }

  return (
    <Card 
      size="small" 
      style={{ 
        position: 'fixed', 
        bottom: 16, 
        right: 16, 
        zIndex: 1000,
        maxWidth: 400,
        background: whiteTheme.colors.cardBackground,
        border: `1px solid ${whiteTheme.colors.border}`,
        boxShadow: whiteTheme.shadows.xl,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <Space>
          {isOnline ? (
            <WifiOutlined style={{ color: '#52c41a' }} />
          ) : (
            <DisconnectOutlined style={{ color: '#ff4d4f' }} />
          )}
          <Text strong>
            {isOnline ? 'Online' : 'Offline'}
          </Text>
          {queue.length > 0 && (
            <Badge count={queue.length} showZero={false} />
          )}
        </Space>
        <Space>
          {isOnline && queue.length > 0 && (
            <Button 
              size="small" 
              icon={<SyncOutlined />} 
              onClick={processQueue}
              loading={isProcessing}
            >
              Pošalji
            </Button>
          )}
          {queue.length > 0 && (
            <Button 
              size="small" 
              danger 
              icon={<DeleteOutlined />} 
              onClick={clearQueue}
            >
              Obriši
            </Button>
          )}
        </Space>
      </div>

      {queue.length > 0 && (
        <List
          size="small"
          dataSource={queue}
          renderItem={(action) => (
            <List.Item
              actions={[
                <Button 
                  size="small" 
                  type="text" 
                  danger 
                  onClick={() => removeAction(action.id)}
                >
                  Ukloni
                </Button>
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text style={{ fontSize: '12px' }}>
                      {action.type === 'scan' && 'Skeniranje'}
                      {action.type === 'manual-entry' && 'Ručno unošenje'}
                      {action.type === 'pick-by-code' && 'Sken kodom'}
                      {action.type === 'short-pick' && 'Djelimično zatvaranje'}
                      {action.type === 'not-found' && 'Nije pronađeno'}
                      {action.type === 'complete-document' && 'Završetak dokumenta'}
                      {action.type === 'stock-count' && 'Popis zaliha'}
                      {action.type === 'exception' && 'Izuzetak'}
                    </Text>
                    {action.retries > 0 && (
                      <Tag color="orange" style={{ fontSize: '10px' }}>
                        {action.retries} pokušaja
                      </Tag>
                    )}
                  </Space>
                }
                description={
                  <Text style={{ fontSize: '11px', color: '#666' }}>
                    {new Date(action.timestamp).toLocaleTimeString()}
                  </Text>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  );
};

export default OfflineQueueComponent;
