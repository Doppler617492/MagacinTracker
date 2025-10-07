import { useEffect, useState } from 'react';
import { Badge, Button, Card, List, message, Space, Tag, Typography } from 'antd';
import { WifiOutlined, DisconnectOutlined, SyncOutlined, DeleteOutlined } from '@ant-design/icons';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import client from '../api';

const { Text } = Typography;

interface OfflineAction {
  id: string;
  type: 'scan' | 'manual';
  taskItemId: string;
  payload: any;
  timestamp: number;
  retries: number;
}

const OfflineQueueComponent = () => {
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
    updateQueue();

    return () => {
      networkManager.removeListener(handleNetworkChange);
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
        } else if (action.type === 'manual') {
          await client.post(`/worker/tasks/${action.taskItemId}/complete-manual`, action.payload);
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
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)'
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
                      {action.type === 'scan' ? 'Skeniranje' : 'Ručno'}
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
