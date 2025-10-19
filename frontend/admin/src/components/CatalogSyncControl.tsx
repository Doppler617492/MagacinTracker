/**
 * Catalog Sync Control Panel
 * Manhattan Active WMS - Hardened sync with monitoring
 * Language: Serbian (Srpski)
 */

import React, { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import {
  Card,
  Button,
  Space,
  Badge,
  Typography,
  Modal,
  Table,
  Statistic,
  Alert,
  message
} from 'antd';
import {
  SyncOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  ClockCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import api from '../api';
import './CatalogSyncControl.css';

const { Title, Text } = Typography;

interface SyncStatus {
  status: 'OK' | 'Degraded' | 'Error';
  last_sync_at: string;
  records_synced: number;
  duration_ms: number;
  error_message?: string;
}

interface SyncLog {
  id: string;
  started_at: string;
  completed_at: string;
  records_synced: number;
  records_skipped: number;
  errors: number;
  status: string;
}

export const CatalogSyncControl: React.FC = () => {
  const [logModalOpen, setLogModalOpen] = useState(false);

  // Fetch sync status
  const { data: syncStatus, refetch: refetchStatus } = useQuery<SyncStatus>({
    queryKey: ['catalog-sync-status'],
    queryFn: async () => {
      const response = await api.get('/pantheon/sync/status');
      return response.data;
    },
    refetchInterval: 30000  // Refresh every 30s
  });

  // Fetch sync logs
  const { data: logs = [] } = useQuery<SyncLog[]>({
    queryKey: ['catalog-sync-logs'],
    queryFn: async () => {
      const response = await api.get('/pantheon/sync/logs');
      return response.data;
    },
    enabled: logModalOpen
  });

  // Trigger sync mutation
  const syncMutation = useMutation({
    mutationFn: async (mode: 'full' | 'delta') => {
      const response = await api.post('/pantheon/sync/catalog', { mode });
      return response.data;
    },
    onSuccess: (data) => {
      message.success(`Sync završen: ${data.records_synced} artikala sinhronizovano`);
      refetchStatus();
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Greška pri sinhronizaciji');
    }
  });

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'OK':
        return <Badge status="success" text="OK" />;
      case 'Degraded':
        return <Badge status="warning" text="Degraded" />;
      case 'Error':
        return <Badge status="error" text="Error" />;
      default:
        return <Badge status="default" text="Unknown" />;
    }
  };

  const formatDuration = (ms: number) => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  return (
    <Card
      title={
        <Space>
          <SyncOutlined />
          <span>Sinhronizacija kataloga</span>
        </Space>
      }
      extra={getStatusBadge(syncStatus?.status)}
      className="catalog-sync-control"
    >
      {syncStatus?.error_message && (
        <Alert
          message="Greška pri sinhronizaciji"
          description={syncStatus.error_message}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* Status Overview */}
        <div className="catalog-sync-control__stats">
          <Space size="large">
            <Statistic
              title="Zadnja sinhronizacija"
              value={syncStatus?.last_sync_at 
                ? new Date(syncStatus.last_sync_at).toLocaleString('sr-RS')
                : 'Nikad'}
              prefix={<ClockCircleOutlined />}
            />
            <Statistic
              title="Artikala sinhronizovano"
              value={syncStatus?.records_synced || 0}
              prefix={<CheckCircleOutlined />}
            />
            <Statistic
              title="Trajanje"
              value={syncStatus?.duration_ms ? formatDuration(syncStatus.duration_ms) : '-'}
            />
          </Space>
        </div>

        {/* Actions */}
        <Space>
          <Button
            type="primary"
            icon={<SyncOutlined />}
            onClick={() => syncMutation.mutate('delta')}
            loading={syncMutation.isPending}
            size="large"
          >
            Pokreni sync (Delta)
          </Button>

          <Button
            icon={<SyncOutlined />}
            onClick={() => syncMutation.mutate('full')}
            loading={syncMutation.isPending}
            size="large"
          >
            Pokreni sync (Full)
          </Button>

          <Button
            icon={<FileTextOutlined />}
            onClick={() => setLogModalOpen(true)}
            size="large"
          >
            Prikaži log
          </Button>
        </Space>

        {/* Info */}
        <Alert
          message="Sinhronizacija info"
          description={
            <ul style={{ margin: 0, paddingLeft: 20 }}>
              <li>Delta sync: Samo promijenjeni artikli (brži)</li>
              <li>Full sync: Svi artikli (sporiji, za oporavak)</li>
              <li>Rate limit: Maksimalno 5 zahtjeva/sekundi</li>
              <li>ETag caching: Automatski (304 Not Modified)</li>
            </ul>
          }
          type="info"
          showIcon
        />
      </Space>

      {/* Sync Logs Modal */}
      <Modal
        title="Istorija sinhronizacije"
        open={logModalOpen}
        onCancel={() => setLogModalOpen(false)}
        footer={null}
        width={800}
      >
        <Table
          dataSource={logs}
          rowKey="id"
          columns={[
            {
              title: 'Datum',
              dataIndex: 'started_at',
              render: (date) => new Date(date).toLocaleString('sr-RS')
            },
            {
              title: 'Trajanje',
              render: (_, record) => {
                const start = new Date(record.started_at).getTime();
                const end = new Date(record.completed_at).getTime();
                return formatDuration(end - start);
              }
            },
            {
              title: 'Sinhronizovano',
              dataIndex: 'records_synced'
            },
            {
              title: 'Preskočeno',
              dataIndex: 'records_skipped'
            },
            {
              title: 'Greške',
              dataIndex: 'errors',
              render: (errors) => errors > 0 ? <Text type="danger">{errors}</Text> : 0
            },
            {
              title: 'Status',
              dataIndex: 'status',
              render: (status) => (
                <Tag color={status === 'success' ? 'success' : 'error'}>
                  {status}
                </Tag>
              )
            }
          ]}
          pagination={{ pageSize: 10 }}
        />
      </Modal>
    </Card>
  );
};

export default CatalogSyncControl;

