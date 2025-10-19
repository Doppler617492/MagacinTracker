/**
 * StockCountWidget - Shows stock count variances and statistics
 * For Admin Dashboard
 */

import React from 'react';
import { Card, Table, Tag, Statistic, Row, Col, Empty } from 'antd';
import {
  CalculatorOutlined,
  RiseOutlined,
  FallOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface CountRecord {
  id: string;
  sku: string;
  sku_name: string;
  location: string;
  counted_qty: number;
  system_qty: number;
  variance: number;
  variance_pct: number;
  reason?: string;
  status: string;
  counted_by_name: string;
  created_at: string;
}

interface CountSummary {
  total_counts: number;
  total_variance: number;
  positive_variance: number;
  negative_variance: number;
  counts_today: number;
  pending_review: number;
  top_variances: CountRecord[];
}

const fetchCountSummary = async (): Promise<CountSummary> => {
  const { data } = await axios.get('/api/counts/summary');
  return data;
};

const fetchTopVariances = async (): Promise<CountRecord[]> => {
  const { data } = await axios.get('/api/counts', {
    params: {
      limit: 10,
    },
  });
  return data;
};

const StockCountWidget: React.FC = () => {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['count-summary'],
    queryFn: fetchCountSummary,
    refetchInterval: 60000, // Refresh every minute
    retry: false,
  });

  const { data: topVariances, isLoading: variancesLoading } = useQuery({
    queryKey: ['top-variances'],
    queryFn: fetchTopVariances,
    refetchInterval: 60000,
    retry: false,
  });

  const columns = [
    {
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 120,
      render: (sku: string, record: CountRecord) => (
        <div>
          <div style={{ fontWeight: 600 }}>{sku}</div>
          <div style={{ fontSize: '12px', color: '#888' }}>{record.sku_name}</div>
        </div>
      ),
    },
    {
      title: 'Location',
      dataIndex: 'location',
      key: 'location',
      width: 100,
    },
    {
      title: 'System',
      dataIndex: 'system_qty',
      key: 'system_qty',
      width: 80,
      align: 'right' as const,
    },
    {
      title: 'Counted',
      dataIndex: 'counted_qty',
      key: 'counted_qty',
      width: 80,
      align: 'right' as const,
    },
    {
      title: 'Variance',
      dataIndex: 'variance',
      key: 'variance',
      width: 100,
      align: 'right' as const,
      render: (variance: number, record: CountRecord) => {
        const color = variance > 0 ? '#52c41a' : variance < 0 ? '#ff4d4f' : '#1890ff';
        const icon =
          variance > 0 ? (
            <RiseOutlined />
          ) : variance < 0 ? (
            <FallOutlined />
          ) : null;

        return (
          <div>
            <div style={{ color, fontWeight: 600 }}>
              {icon} {variance > 0 && '+'}
              {variance}
            </div>
            <div style={{ fontSize: '12px', color: '#888' }}>
              ({variance > 0 && '+'}
              {record.variance_pct.toFixed(1)}%)
            </div>
          </div>
        );
      },
    },
    {
      title: 'Reason',
      dataIndex: 'reason',
      key: 'reason',
      width: 120,
      render: (reason: string) => (reason ? <Tag color="orange">{reason}</Tag> : '-'),
    },
    {
      title: 'Counted By',
      dataIndex: 'counted_by_name',
      key: 'counted_by_name',
      width: 100,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => {
        const color = status === 'synced' ? 'green' : status === 'pending' ? 'orange' : 'blue';
        return <Tag color={color}>{status}</Tag>;
      },
    },
  ];

  return (
    <div style={{ marginBottom: '24px' }}>
      <Card
        title={
          <span>
            <CalculatorOutlined style={{ marginRight: '8px' }} />
            Stock Count Variances
          </span>
        }
        bordered={false}
        loading={summaryLoading}
      >
        {/* Summary Statistics */}
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Statistic
              title="Counts Today"
              value={summary?.counts_today || 0}
              prefix={<CalculatorOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Total Variance"
              value={summary?.total_variance || 0}
              precision={0}
              valueStyle={{
                color:
                  (summary?.total_variance || 0) > 0
                    ? '#3f8600'
                    : (summary?.total_variance || 0) < 0
                      ? '#cf1322'
                      : undefined,
              }}
              prefix={
                (summary?.total_variance || 0) > 0 ? (
                  <RiseOutlined />
                ) : (summary?.total_variance || 0) < 0 ? (
                  <FallOutlined />
                ) : null
              }
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Positive Variance"
              value={summary?.positive_variance || 0}
              precision={0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<RiseOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Negative Variance"
              value={Math.abs(summary?.negative_variance || 0)}
              precision={0}
              valueStyle={{ color: '#cf1322' }}
              prefix={<FallOutlined />}
            />
          </Col>
        </Row>

        {summary && summary.pending_review > 0 && (
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
            <WarningOutlined style={{ color: '#faad14', fontSize: '18px' }} />
            <div>
              <strong>{summary.pending_review}</strong> count
              {summary.pending_review !== 1 && 's'} pending review (variance &gt; 10%)
            </div>
          </div>
        )}

        {/* Top Variances Table */}
        <div style={{ marginTop: '16px' }}>
          <h4 style={{ marginBottom: '12px' }}>Recent Counts</h4>
          {topVariances && topVariances.length > 0 ? (
            <Table
              columns={columns}
              dataSource={topVariances}
              rowKey="id"
              pagination={false}
              size="small"
              loading={variancesLoading}
              scroll={{ x: 'max-content' }}
            />
          ) : (
            <Empty description="No counts recorded yet" />
          )}
        </div>
      </Card>
    </div>
  );
};

export default StockCountWidget;

