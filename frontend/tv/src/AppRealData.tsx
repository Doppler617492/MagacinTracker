/**
 * TV Dashboard - Real Data Only (No Mocks)
 * Manhattan Active WMS Style
 * Language: Serbian (Srpski)
 */

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { io, Socket } from 'socket.io-client';
import { useQuery } from '@tanstack/react-query';
import { Typography, Card, Row, Col, Progress, Table, Tag, Space, Statistic } from 'antd';
import { 
  TrophyOutlined, 
  ClockCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined 
} from '@ant-design/icons';
import client, { ensureAuth } from './api';
import './styles.css';

const { Title, Text } = Typography;

interface PartialStats {
  total_items: number;
  fully_completed: number;
  partially_completed: number;
  partial_ratio: number;
  top_reasons: Array<{
    razlog: string;
    razlog_display: string;
    count: number;
    percentage: number;
  }>;
}

interface TeamPerformance {
  team_id: string;
  team_name: string;
  shift: 'A' | 'B';
  tasks_completed_today: number;
  items_completed: number;
  avg_time_minutes: number;
  procenat_ispunjenja_avg: number;
}

interface LiveMetrics {
  today_completed: number;
  shift_a_completed: number;
  shift_b_completed: number;
  partial_stats: PartialStats;
  top_team: TeamPerformance;
  active_workers: number;
  current_shift: 'A' | 'B';
}

const socketEndpoint = import.meta.env.VITE_SOCKET_URL ?? window.location.origin;

const fetchLiveMetrics = async (): Promise<LiveMetrics> => {
  const { data } = await client.get('/stream/live');
  return data;
};

export const AppRealData: React.FC = () => {
  const [ready, setReady] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);

  // Fetch live metrics every 15 seconds
  const { data: metrics, refetch } = useQuery({
    queryKey: ['tv', 'live-metrics'],
    queryFn: fetchLiveMetrics,
    enabled: ready,
    refetchInterval: 15000,  // 15 seconds
  });

  // Initialize auth
  useEffect(() => {
    ensureAuth()
      .then(() => setReady(true))
      .catch((error) => console.error('TV auth failed', error));
  }, []);

  // WebSocket for real-time updates (< 2s latency)
  useEffect(() => {
    if (!ready) return;

    const newSocket = io(socketEndpoint, { path: '/ws' });
    
    newSocket.on('connect', () => {
      console.info('[TV] Socket connected:', newSocket.id);
    });

    newSocket.on('task_completed', () => {
      console.info('[TV] Task completed event received');
      refetch();  // Immediate refresh on task completion
    });

    newSocket.on('document_completed', () => {
      console.info('[TV] Document completed event received');
      refetch();
    });

    newSocket.on('team_status_changed', () => {
      console.info('[TV] Team status changed');
      refetch();
    });

    newSocket.on('tv_delta', () => {
      console.info('[TV] TV delta event received');
      refetch();
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [ready, refetch]);

  if (!ready || !metrics) {
    return (
      <div className="tv-loading">
        <Title level={2}>Učitavanje...</Title>
      </div>
    );
  }

  const { 
    today_completed, 
    shift_a_completed, 
    shift_b_completed,
    partial_stats,
    top_team,
    active_workers,
    current_shift
  } = metrics;

  return (
    <div className="tv-dashboard">
      {/* Header */}
      <div className="tv-header">
        <Title level={1} style={{ margin: 0, color: '#fff' }}>
          Magacin Track - Uživo Dashboard
        </Title>
        <Space>
          <Tag color={current_shift === 'A' ? 'blue' : 'green'} style={{ fontSize: 16, padding: '4px 12px' }}>
            Trenutna smjena: {current_shift}
          </Tag>
          <Tag color="success" style={{ fontSize: 16, padding: '4px 12px' }}>
            Aktivno radnika: {active_workers}
          </Tag>
        </Space>
      </div>

      {/* KPI Metrics */}
      <Row gutter={24} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card className="tv-kpi-card">
            <Statistic
              title="Danas završeno"
              value={today_completed}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a', fontSize: 48 }}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card className="tv-kpi-card">
            <Statistic
              title="Smjena A"
              value={shift_a_completed}
              suffix="zadataka"
              valueStyle={{ color: '#1890ff', fontSize: 48 }}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card className="tv-kpi-card">
            <Statistic
              title="Smjena B"
              value={shift_b_completed}
              suffix="zadataka"
              valueStyle={{ color: '#52c41a', fontSize: 48 }}
            />
          </Card>
        </Col>

        <Col span={6}>
          <Card className="tv-kpi-card">
            <Statistic
              title="Djelimično %"
              value={partial_stats.partial_ratio.toFixed(1)}
              suffix="%"
              prefix={<WarningOutlined />}
              valueStyle={{ color: partial_stats.partial_ratio > 20 ? '#ff4d4f' : '#faad14', fontSize: 48 }}
            />
          </Card>
        </Col>
      </Row>

      {/* Top Team & Top Reasons */}
      <Row gutter={24} style={{ marginBottom: 24 }}>
        {/* Top Team */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <TrophyOutlined style={{ color: '#faad14', fontSize: 24 }} />
                <Title level={3} style={{ margin: 0 }}>Top Tim Dana</Title>
              </Space>
            }
            className="tv-card"
          >
            {top_team ? (
              <div className="tv-top-team">
                <Title level={2} style={{ color: '#1890ff' }}>{top_team.team_name}</Title>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <div>
                    <Text style={{ fontSize: 18 }}>Smjena:</Text>
                    <Tag color={top_team.shift === 'A' ? 'blue' : 'green'} style={{ fontSize: 16, marginLeft: 8 }}>
                      {top_team.shift}
                    </Tag>
                  </div>
                  <Statistic 
                    title="Zadaci završeni" 
                    value={top_team.tasks_completed_today}
                    valueStyle={{ fontSize: 36 }}
                  />
                  <Statistic 
                    title="Stavke ukupno" 
                    value={top_team.items_completed}
                    valueStyle={{ fontSize: 36 }}
                  />
                  <div>
                    <Text style={{ fontSize: 16 }}>% ispunjenja prosječno:</Text>
                    <Progress 
                      percent={top_team.procenat_ispunjenja_avg} 
                      strokeColor="#52c41a"
                      strokeWidth={16}
                      style={{ fontSize: 18 }}
                    />
                  </div>
                </Space>
              </div>
            ) : (
              <Text type="secondary">Nema podataka</Text>
            )}
          </Card>
        </Col>

        {/* Top 3 Reasons for Partial Completion */}
        <Col span={12}>
          <Card 
            title={
              <Space>
                <WarningOutlined style={{ color: '#faad14', fontSize: 24 }} />
                <Title level={3} style={{ margin: 0 }}>Top 3 Razloga (Djelimično)</Title>
              </Space>
            }
            className="tv-card"
          >
            {partial_stats.top_reasons && partial_stats.top_reasons.length > 0 ? (
              <div className="tv-top-reasons">
                {partial_stats.top_reasons.slice(0, 3).map((reason, index) => (
                  <motion.div
                    key={reason.razlog}
                    className="reason-item"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    <div className="reason-rank">#{index + 1}</div>
                    <div className="reason-content">
                      <Text strong style={{ fontSize: 20 }}>
                        {reason.razlog_display}
                      </Text>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginTop: 8 }}>
                        <Statistic 
                          value={reason.count} 
                          suffix="puta"
                          valueStyle={{ fontSize: 24 }}
                        />
                        <Progress 
                          percent={reason.percentage} 
                          strokeColor="#ff4d4f"
                          style={{ flex: 1 }}
                        />
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <Text type="secondary">Nema djelimičnih završetaka danas</Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Partial Completion Details */}
      <Row gutter={24}>
        <Col span={24}>
          <Card 
            title={
              <Title level={3} style={{ margin: 0 }}>
                Statistika Djelimičnih Završetaka
              </Title>
            }
            className="tv-card"
          >
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="Ukupno stavki"
                  value={partial_stats.total_items}
                  valueStyle={{ fontSize: 32 }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Potpuno završeno"
                  value={partial_stats.fully_completed}
                  valueStyle={{ color: '#52c41a', fontSize: 32 }}
                  prefix={<CheckCircleOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="Djelimično završeno"
                  value={partial_stats.partially_completed}
                  valueStyle={{ color: '#faad14', fontSize: 32 }}
                  prefix={<WarningOutlined />}
                />
              </Col>
              <Col span={6}>
                <div>
                  <Text type="secondary" style={{ fontSize: 14 }}>Postotak djelimičnih</Text>
                  <Progress 
                    percent={partial_stats.partial_ratio}
                    strokeColor={partial_stats.partial_ratio > 20 ? '#ff4d4f' : '#faad14'}
                    strokeWidth={20}
                    format={(percent) => `${percent?.toFixed(1)}%`}
                  />
                </div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Footer */}
      <div className="tv-footer">
        <Text type="secondary">
          Zadnje ažuriranje: {new Date().toLocaleTimeString('sr-RS')}
        </Text>
        {socket?.connected ? (
          <Tag color="success">● Live Sync Aktivan</Tag>
        ) : (
          <Tag color="error">● Offline</Tag>
        )}
      </div>
    </div>
  );
};

export default AppRealData;

