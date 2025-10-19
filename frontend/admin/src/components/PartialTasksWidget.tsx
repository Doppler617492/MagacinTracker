/**
 * PartialTasksWidget - Shows tasks completed with partial quantities
 * For Admin Dashboard
 */

import React from 'react';
import { Card, Table, Tag, Tooltip, Progress } from 'antd';
import {
  WarningOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface TaskItem {
  id: string;
  dokument_broj: string;
  lokacija_naziv: string;
  stavke_total: number;
  stavke_completed: number;
  partial_items: number;
  shortage_qty: number;
  progress: number;
  status: string;
  assigned_by_name?: string;
  completed_at?: string;
  completed_by_name?: string;
}

const fetchPartialTasks = async (): Promise<TaskItem[]> => {
  const { data } = await axios.get('/api/trebovanja', {
    params: {
      status: 'partial',
      limit: 20,
    },
  });
  return data;
};

const PartialTasksWidget: React.FC = () => {
  const { data: partialTasks, isLoading } = useQuery({
    queryKey: ['partial-tasks'],
    queryFn: fetchPartialTasks,
    refetchInterval: 60000, // Refresh every minute
    retry: false,
  });

  const columns = [
    {
      title: 'Document',
      dataIndex: 'dokument_broj',
      key: 'dokument_broj',
      width: 150,
      render: (dokument: string, record: TaskItem) => (
        <div>
          <div style={{ fontWeight: 600 }}>{dokument}</div>
          <div style={{ fontSize: '12px', color: '#888' }}>{record.lokacija_naziv}</div>
        </div>
      ),
    },
    {
      title: 'Progress',
      dataIndex: 'progress',
      key: 'progress',
      width: 150,
      render: (progress: number, record: TaskItem) => (
        <div>
          <Progress
            percent={progress}
            size="small"
            status={progress === 100 ? 'success' : 'active'}
            strokeColor={progress === 100 ? '#52c41a' : '#faad14'}
          />
          <div style={{ fontSize: '12px', color: '#888', marginTop: '4px' }}>
            {record.stavke_completed} / {record.stavke_total} items
          </div>
        </div>
      ),
    },
    {
      title: 'Partial Items',
      dataIndex: 'partial_items',
      key: 'partial_items',
      width: 100,
      align: 'center' as const,
      render: (partial: number) => (
        <Tag color="orange" icon={<WarningOutlined />}>
          {partial}
        </Tag>
      ),
    },
    {
      title: 'Shortage Qty',
      dataIndex: 'shortage_qty',
      key: 'shortage_qty',
      width: 100,
      align: 'right' as const,
      render: (shortage: number) => (
        <span style={{ color: shortage > 0 ? '#ff4d4f' : '#888', fontWeight: 600 }}>
          {shortage > 0 && '-'}
          {shortage}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 120,
      render: (status: string) => {
        const statusMap: Record<string, { color: string; label: string; icon: React.ReactNode }> = {
          done: { color: 'green', label: 'Done', icon: <CheckCircleOutlined /> },
          partial: { color: 'orange', label: 'Partial (Djelimično)', icon: <WarningOutlined /> },
          in_progress: { color: 'blue', label: 'In Progress', icon: null },
        };

        const config = statusMap[status] || {
          color: 'default',
          label: status,
          icon: null,
        };

        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: 'Completed By',
      dataIndex: 'completed_by_name',
      key: 'completed_by_name',
      width: 120,
      render: (name: string) => name || '-',
    },
    {
      title: 'Date',
      dataIndex: 'completed_at',
      key: 'completed_at',
      width: 120,
      render: (date: string) =>
        date ? new Date(date).toLocaleDateString('sr-Latn-ME') : '-',
    },
  ];

  const totalPartialItems = partialTasks?.reduce(
    (sum, task) => sum + (task.partial_items || 0),
    0
  );
  const totalShortage = partialTasks?.reduce(
    (sum, task) => sum + (task.shortage_qty || 0),
    0
  );

  return (
    <div style={{ marginBottom: '24px' }}>
      <Card
        title={
          <span>
            <WarningOutlined style={{ marginRight: '8px', color: '#faad14' }} />
            Partial Task Completions
          </span>
        }
        extra={
          <div style={{ display: 'flex', gap: '16px', fontSize: '14px' }}>
            <Tooltip title="Total tasks with partial quantities">
              <span>
                <strong>{partialTasks?.length || 0}</strong> tasks
              </span>
            </Tooltip>
            <Tooltip title="Total partial line items">
              <span>
                <strong>{totalPartialItems || 0}</strong> partial items
              </span>
            </Tooltip>
            <Tooltip title="Total shortage quantity">
              <span style={{ color: '#ff4d4f' }}>
                <strong>-{totalShortage || 0}</strong> shortage
              </span>
            </Tooltip>
          </div>
        }
        bordered={false}
        loading={isLoading}
      >
        {partialTasks && partialTasks.length > 0 ? (
          <>
            <div
              style={{
                background: '#fff7e6',
                border: '1px solid #ffd666',
                borderRadius: '6px',
                padding: '12px 16px',
                marginBottom: '16px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <ExclamationCircleOutlined style={{ color: '#faad14', fontSize: '18px' }} />
              <div>
                <div style={{ fontWeight: 600 }}>
                  {partialTasks.length} task{partialTasks.length !== 1 && 's'} completed with
                  shortages
                </div>
                <div style={{ fontSize: '12px', color: '#666', marginTop: '4px' }}>
                  Review these tasks to understand stock discrepancies and update inventory
                  accordingly.
                </div>
              </div>
            </div>

            <Table
              columns={columns}
              dataSource={partialTasks}
              rowKey="id"
              pagination={{ pageSize: 10, showSizeChanger: false }}
              size="small"
              scroll={{ x: 'max-content' }}
            />
          </>
        ) : (
          <div
            style={{
              textAlign: 'center',
              padding: '32px',
              color: '#888',
            }}
          >
            <CheckCircleOutlined style={{ fontSize: '48px', color: '#52c41a', marginBottom: '16px' }} />
            <div style={{ fontSize: '16px', fontWeight: 600, marginBottom: '8px' }}>
              All tasks completed fully!
            </div>
            <div style={{ fontSize: '14px' }}>
              No tasks with partial quantities in the selected period.
            </div>
          </div>
        )}
      </Card>
    </div>
  );
};

export default PartialTasksWidget;

