import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  InputNumber,
  Select,
  message,
  Progress,
  Typography,
  Divider,
  Alert,
  Table,
  Tooltip,
  Badge,
  Timeline,
  Tabs,
  Switch,
  Input
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  ThunderboltOutlined,
  BarChartOutlined,
  LineOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  GlobalOutlined,
  NodeIndexOutlined,
  EyeOutlined,
  QuestionCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  FireOutlined,
  RocketOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Line, Column, Area } from '@ant-design/charts';
import {
  getStreamMetrics,
  getThroughputMetrics,
  getPerformanceMetrics,
  getHealthMetrics,
  getRecentEvents,
  getWorkerActivity,
  getWarehouseLoad,
  getTvSnapshot,
  simulateEvents,
  publishEvent,
  getTransformerStatus,
  predictTransformer,
  StreamEvent,
  EventPublishRequest,
  TransformerPredictionRequest
} from '../api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const LiveOpsDashboardPage: React.FC = () => {
  const [liveMode, setLiveMode] = useState(true);
  const [eventModalVisible, setEventModalVisible] = useState(false);
  const [predictionModalVisible, setPredictionModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [predictionForm] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch real-time data
  const { data: streamMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
    queryKey: ['stream-metrics'],
    queryFn: getStreamMetrics,
    refetchInterval: liveMode ? 2000 : false, // Refresh every 2 seconds in live mode
  });

  const { data: throughputMetrics, isLoading: throughputLoading } = useQuery({
    queryKey: ['throughput-metrics'],
    queryFn: getThroughputMetrics,
    refetchInterval: liveMode ? 5000 : false, // Refresh every 5 seconds in live mode
  });

  const { data: performanceMetrics, isLoading: performanceLoading } = useQuery({
    queryKey: ['performance-metrics'],
    queryFn: getPerformanceMetrics,
    refetchInterval: liveMode ? 10000 : false, // Refresh every 10 seconds in live mode
  });

  const { data: healthMetrics, isLoading: healthLoading } = useQuery({
    queryKey: ['health-metrics'],
    queryFn: getHealthMetrics,
    refetchInterval: liveMode ? 15000 : false, // Refresh every 15 seconds in live mode
  });

  const { data: recentEvents, isLoading: eventsLoading, refetch: refetchEvents } = useQuery({
    queryKey: ['recent-events'],
    queryFn: () => getRecentEvents(50),
    refetchInterval: liveMode ? 3000 : false, // Refresh every 3 seconds in live mode
  });

  const { data: workerActivity, isLoading: workerLoading } = useQuery({
    queryKey: ['worker-activity'],
    queryFn: getWorkerActivity,
    refetchInterval: liveMode ? 8000 : false, // Refresh every 8 seconds in live mode
  });

  const { data: warehouseLoad, isLoading: warehouseLoading } = useQuery({
    queryKey: ['warehouse-load'],
    queryFn: getWarehouseLoad,
    refetchInterval: liveMode ? 12000 : false, // Refresh every 12 seconds in live mode
  });

  const { data: transformerStatus, isLoading: transformerLoading } = useQuery({
    queryKey: ['transformer-status'],
    queryFn: getTransformerStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: tvSnapshot } = useQuery({
    queryKey: ['tv-snapshot', liveMode],
    queryFn: getTvSnapshot,
    refetchInterval: liveMode ? 15000 : false,
  });

  // Mutations
  const simulateMutation = useMutation({
    mutationFn: simulateEvents,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['recent-events'] });
      queryClient.invalidateQueries({ queryKey: ['stream-metrics'] });
      message.success(`Simulated ${data.event_count} events successfully!`);
    },
    onError: (error: any) => {
      message.error('Event simulation failed');
      console.error('Simulation error:', error);
    }
  });

  const publishMutation = useMutation({
    mutationFn: publishEvent,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['recent-events'] });
      message.success(`Event ${data.event_id} published successfully!`);
      setEventModalVisible(false);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error('Event publish failed');
      console.error('Publish error:', error);
    }
  });

  const predictionMutation = useMutation({
    mutationFn: predictTransformer,
    onSuccess: (data) => {
      message.success(`Pattern analysis completed! Processing time: ${data.processing_time_ms}ms`);
      setPredictionModalVisible(false);
      predictionForm.resetFields();
    },
    onError: (error: any) => {
      message.error('Pattern prediction failed');
      console.error('Prediction error:', error);
    }
  });

  const handleSimulateEvents = (warehouseId: string, eventCount: number) => {
    simulateMutation.mutate({ warehouseId, eventCount });
  };

  const handlePublishEvent = (values: any) => {
    const eventRequest: EventPublishRequest = {
      event_type: values.event_type,
      warehouse_id: values.warehouse_id,
      data: JSON.parse(values.event_data || '{}'),
      correlation_id: values.correlation_id
    };
    
    publishMutation.mutate(eventRequest);
  };

  const handlePredictPattern = (values: any) => {
    const sequences = values.sequences.split('\n').filter((seq: string) => seq.trim());
    const predictionRequest: TransformerPredictionRequest = {
      sequences: sequences.map((seq: string) => seq.split(',').map((s: string) => s.trim()))
    };
    
    predictionMutation.mutate(predictionRequest);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'degraded': return 'orange';
      case 'error': return 'red';
      default: return 'blue';
    }
  };

  const getEventTypeColor = (eventType: string) => {
    switch (eventType) {
      case 'task_created': return 'blue';
      case 'task_completed': return 'green';
      case 'task_assigned': return 'purple';
      case 'worker_login': return 'cyan';
      case 'worker_logout': return 'orange';
      case 'scan_event': return 'geekblue';
      case 'ai_prediction': return 'magenta';
      case 'ai_action': return 'red';
      case 'system_alert': return 'volcano';
      default: return 'default';
    }
  };

  // Prepare data for visualizations
  const prepareEventTimelineData = () => {
    if (!recentEvents?.events) return [];
    
    return recentEvents.events.slice(0, 20).map((event: StreamEvent, index: number) => ({
      time: new Date(event.timestamp).getTime(),
      event_type: event.event_type,
      warehouse_id: event.warehouse_id,
      processed: event.processed,
      index
    }));
  };

  const prepareThroughputData = () => {
    const data = [];
    const now = Date.now();
    
    for (let i = 0; i < 30; i++) {
      data.push({
        time: now - (29 - i) * 10000, // 10 seconds intervals
        events_per_second: Math.random() * 200 + 50,
        queue_size: Math.random() * 100,
        processing_time: Math.random() * 50 + 10
      });
    }
    
    return data;
  };

  const prepareWorkerActivityData = () => {
    if (!workerActivity?.worker_activity) return [];
    
    return Object.entries(workerActivity.worker_activity).map(([workerId, activity]: [string, any]) => ({
      worker: workerId,
      event_count: activity.event_count,
      last_activity: new Date(activity.last_activity).getTime(),
      warehouse: activity.warehouse_id
    }));
  };

  const eventTimelineData = prepareEventTimelineData();
  const throughputData = prepareThroughputData();
  const workerActivityData = prepareWorkerActivityData();
  const queueStatusLabels: Record<string, string> = {
    assigned: 'Dodijeljeno',
    in_progress: 'U toku',
    done: 'Završeno',
    blocked: 'Blokirano',
  };

  const partialQueueData = useMemo(() => {
    if (!tvSnapshot?.queue) return [] as Array<{
      key: string;
      dokument: string;
      radnja: string;
      partial_items: number;
      total_items: number;
      shortage_qty: number;
      status: string;
    }>;

    return tvSnapshot.queue
      .filter((item) => (item.partial_items ?? 0) > 0 || (item.shortage_qty ?? 0) > 0)
      .map((item) => ({
        key: item.dokument,
        dokument: item.dokument,
        radnja: item.radnja,
        partial_items: item.partial_items ?? 0,
        total_items: item.total_items ?? 0,
        shortage_qty: item.shortage_qty ?? 0,
        status: item.status,
      }));
  }, [tvSnapshot?.queue]);

  const partialQueueColumns: ColumnsType<(typeof partialQueueData)[number]> = [
    {
      title: 'Dokument',
      dataIndex: 'dokument',
      key: 'dokument',
      width: 160,
    },
    {
      title: 'Radnja',
      dataIndex: 'radnja',
      key: 'radnja',
      width: 180,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 140,
      render: (status: string) => queueStatusLabels[status] ?? status,
    },
    {
      title: 'Djelimično',
      dataIndex: 'partial_items',
      key: 'partial_items',
      width: 130,
      render: (value: number, record) => (
        <span style={{ fontWeight: 600 }}>
          {value} / {record.total_items}
        </span>
      ),
    },
    {
      title: 'Razlika (kom)',
      dataIndex: 'shortage_qty',
      key: 'shortage_qty',
      width: 140,
      render: (value: number) => (
        <span style={{ color: value > 0 ? '#ff4d4f' : '#52c41a', fontWeight: 600 }}>
          {value.toFixed(1)}
        </span>
      ),
    },
  ];

  // Chart configurations
  const eventTimelineChartConfig = {
    data: eventTimelineData,
    xField: 'time',
    yField: 'index',
    color: (item: any) => getEventTypeColor(item.event_type),
    point: {
      size: 5,
      shape: 'circle',
    },
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      type: 'time',
      title: { text: 'Time' },
    },
    yAxis: {
      title: { text: 'Event Index' },
    },
  };

  const throughputChartConfig = {
    data: throughputData,
    xField: 'time',
    yField: 'events_per_second',
    smooth: true,
    color: '#1890ff',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      type: 'time',
      title: { text: 'Time' },
    },
    yAxis: {
      title: { text: 'Events/Second' },
    },
  };

  const workerActivityChartConfig = {
    data: workerActivityData,
    xField: 'worker',
    yField: 'event_count',
    color: '#52c41a',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Workers' },
    },
    yAxis: {
      title: { text: 'Event Count' },
    },
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>⚡ Live Operations Dashboard</Title>
        <Text type="secondary">Real-time monitoring and control of warehouse operations</Text>
      </div>

      {/* Live Mode Toggle */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Switch
                checked={liveMode}
                onChange={setLiveMode}
                checkedChildren="LIVE"
                unCheckedChildren="PAUSED"
              />
              <Text strong>Live Mode</Text>
            </Space>
          </Col>
          <Col>
            <Badge 
              status={liveMode ? "processing" : "default"} 
              text={liveMode ? "Real-time updates active" : "Updates paused"}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  refetchMetrics();
                  refetchEvents();
                  message.success('All data refreshed');
                }}
              >
                Refresh All
              </Button>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={() => handleSimulateEvents("warehouse_1", 20)}
                loading={simulateMutation.isPending}
              >
                Simulate Events
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Real-time Metrics */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Events/Second"
              value={streamMetrics?.metrics?.events_per_second || 0}
              precision={1}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {streamMetrics?.metrics?.events_processed || 0} total processed
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Queue Size"
              value={streamMetrics?.metrics?.queue_size || 0}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: streamMetrics?.metrics?.queue_size > 100 ? '#ff4d4f' : '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {streamMetrics?.metrics?.average_processing_time ? (streamMetrics.metrics.average_processing_time * 1000).toFixed(1) : 0}ms avg
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Active Workers"
              value={streamMetrics?.metrics?.active_workers || 0}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {streamMetrics?.metrics?.active_warehouses || 0} warehouses
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Error Rate"
              value={streamMetrics?.metrics?.processing_errors || 0}
              prefix={<ExclamationCircleOutlined />}
              valueStyle={{ color: streamMetrics?.metrics?.processing_errors > 0 ? '#ff4d4f' : '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {streamMetrics?.metrics?.event_history_size || 0} in history
            </div>
          </Card>
        </Col>
      </Row>
      {tvSnapshot && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Djelimične stavke"
                value={tvSnapshot.kpi.partial_items}
                prefix={<WarningOutlined />}
                valueStyle={{ color: tvSnapshot.kpi.partial_items > 0 ? '#fa8c16' : '#52c41a' }}
              />
              <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                Aktivne zadužnice: {tvSnapshot.queue.length}
              </div>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Razlika ukupno (kom)"
                value={tvSnapshot.kpi.shortage_qty}
                precision={1}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: tvSnapshot.kpi.shortage_qty > 0 ? '#ff4d4f' : '#52c41a' }}
              />
              <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                Dokumenta sa razlikom: {partialQueueData.length}
              </div>
            </Card>
          </Col>
        </Row>
      )}
      {partialQueueData.length > 0 && (
        <Card title="Djelimične zadužnice" style={{ marginBottom: '24px' }}>
          <Table
            columns={partialQueueColumns}
            dataSource={partialQueueData}
            pagination={false}
            size="small"
          />
        </Card>
      )}

      {/* System Health Alert */}
      {healthMetrics?.health_metrics?.status === 'degraded' && (
        <Alert
          message="⚠️ System Health Degraded"
          description={healthMetrics.health_metrics.issues?.join(', ') || 'System performance issues detected'}
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" type="primary">
              View Details
            </Button>
          }
        />
      )}

      {/* Main Dashboard Tabs */}
      <Tabs defaultActiveKey="events" size="large">
        <TabPane tab="📊 Real-time Events" key="events">
          <Row gutter={16}>
            <Col xs={24} lg={16}>
              <Card title="Event Timeline" loading={eventsLoading}>
                <div style={{ height: '400px' }}>
                  {eventTimelineData.length > 0 ? (
                    <Line {...eventTimelineChartConfig} />
                  ) : (
                    <div style={{ 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      No events available
                    </div>
                  )}
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="Recent Events" loading={eventsLoading}>
                <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                  {recentEvents?.events?.slice(0, 10).map((event: StreamEvent, index: number) => (
                    <div key={event.event_id} style={{ 
                      padding: '8px 0', 
                      borderBottom: index < 9 ? '1px solid #f0f0f0' : 'none',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}>
                      <div>
                        <Tag color={getEventTypeColor(event.event_type)}>
                          {event.event_type}
                        </Tag>
                        <div style={{ fontSize: '12px', color: '#666' }}>
                          {event.warehouse_id}
                        </div>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '12px' }}>
                          {new Date(event.timestamp).toLocaleTimeString()}
                        </div>
                        <Badge 
                          status={event.processed ? "success" : "processing"} 
                          text={event.processed ? "Processed" : "Processing"}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="📈 Throughput Analytics" key="throughput">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Events Per Second" loading={throughputLoading}>
                <div style={{ height: '300px' }}>
                  <Area {...throughputChartConfig} />
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Performance Metrics" loading={performanceLoading}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Throughput Target:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, (throughputMetrics?.throughput_metrics?.events_per_second || 0) / 2)} 
                        status={throughputMetrics?.throughput_metrics?.events_per_second > 100 ? "success" : "active"}
                      />
                      {throughputMetrics?.throughput_metrics?.events_per_second || 0} / 100 events/s
                    </div>
                  </div>
                  <div>
                    <Text strong>Latency Target:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, 100 - (throughputMetrics?.throughput_metrics?.average_processing_time || 0) * 1000)} 
                        status={throughputMetrics?.throughput_metrics?.average_processing_time < 0.1 ? "success" : "exception"}
                      />
                      {(throughputMetrics?.throughput_metrics?.average_processing_time || 0) * 1000}ms / 100ms target
                    </div>
                  </div>
                  <div>
                    <Text strong>Error Rate:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, throughputMetrics?.throughput_metrics?.processing_errors || 0)} 
                        status={throughputMetrics?.throughput_metrics?.processing_errors < 5 ? "success" : "exception"}
                      />
                      {throughputMetrics?.throughput_metrics?.processing_errors || 0}% / 5% target
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="👥 Worker Activity" key="workers">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Worker Event Activity" loading={workerLoading}>
                <div style={{ height: '300px' }}>
                  {workerActivityData.length > 0 ? (
                    <Column {...workerActivityChartConfig} />
                  ) : (
                    <div style={{ 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      No worker activity data available
                    </div>
                  )}
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Worker Status" loading={workerLoading}>
                <Table
                  dataSource={workerActivityData}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: 'Worker',
                      dataIndex: 'worker',
                      key: 'worker',
                    },
                    {
                      title: 'Events',
                      dataIndex: 'event_count',
                      key: 'event_count',
                      render: (count: number) => (
                        <Tag color="blue">{count}</Tag>
                      )
                    },
                    {
                      title: 'Warehouse',
                      dataIndex: 'warehouse',
                      key: 'warehouse',
                    },
                    {
                      title: 'Last Activity',
                      dataIndex: 'last_activity',
                      key: 'last_activity',
                      render: (time: number) => (
                        <Text type="secondary">
                          {new Date(time).toLocaleTimeString()}
                        </Text>
                      )
                    }
                  ]}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="🏭 Warehouse Load" key="warehouses">
          <Row gutter={16}>
            <Col xs={24}>
              <Card title="Warehouse Load Distribution" loading={warehouseLoading}>
                <Table
                  dataSource={Object.entries(warehouseLoad?.warehouse_load || {}).map(([warehouseId, load]: [string, any]) => ({
                    key: warehouseId,
                    warehouse: warehouseId,
                    total_tasks: load.total_tasks || 0,
                    pending: load.pending || 0,
                    in_progress: load.in_progress || 0,
                    completed: load.completed || 0,
                    load_percentage: load.load_percentage || 0
                  }))}
                  pagination={false}
                  columns={[
                    {
                      title: 'Warehouse',
                      dataIndex: 'warehouse',
                      key: 'warehouse',
                      render: (name: string) => <Text strong>{name}</Text>
                    },
                    {
                      title: 'Total Tasks',
                      dataIndex: 'total_tasks',
                      key: 'total_tasks',
                      render: (count: number) => <Tag color="blue">{count}</Tag>
                    },
                    {
                      title: 'Pending',
                      dataIndex: 'pending',
                      key: 'pending',
                      render: (count: number) => <Tag color="orange">{count}</Tag>
                    },
                    {
                      title: 'In Progress',
                      dataIndex: 'in_progress',
                      key: 'in_progress',
                      render: (count: number) => <Tag color="processing">{count}</Tag>
                    },
                    {
                      title: 'Completed',
                      dataIndex: 'completed',
                      key: 'completed',
                      render: (count: number) => <Tag color="success">{count}</Tag>
                    },
                    {
                      title: 'Load',
                      dataIndex: 'load_percentage',
                      key: 'load_percentage',
                      render: (percent: number) => (
                        <Progress 
                          percent={percent} 
                          size="small"
                          status={percent > 80 ? "exception" : percent > 50 ? "normal" : "success"}
                        />
                      )
                    }
                  ]}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Action Buttons */}
      <Card style={{ marginTop: '24px' }}>
        <Row gutter={16}>
          <Col>
            <Button
              type="primary"
              icon={<RocketOutlined />}
              onClick={() => setEventModalVisible(true)}
            >
              Publish Event
            </Button>
          </Col>
          <Col>
            <Button
              icon={<EyeOutlined />}
              onClick={() => setPredictionModalVisible(true)}
            >
              Analyze Pattern
            </Button>
          </Col>
          <Col>
            <Button
              icon={<FireOutlined />}
              onClick={() => handleSimulateEvents("warehouse_1", 50)}
              loading={simulateMutation.isPending}
            >
              Stress Test
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Publish Event Modal */}
      <Modal
        title="🚀 Publish Event"
        open={eventModalVisible}
        onCancel={() => {
          setEventModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handlePublishEvent}
          initialValues={{
            event_type: 'task_created',
            warehouse_id: 'warehouse_1',
            event_data: '{"task_id": "task_123", "priority": "high"}',
            correlation_id: `corr_${Date.now()}`
          }}
        >
          <Form.Item
            name="event_type"
            label="Event Type"
            rules={[{ required: true, message: 'Please select event type' }]}
          >
            <Select placeholder="Select event type">
              <Option value="task_created">Task Created</Option>
              <Option value="task_completed">Task Completed</Option>
              <Option value="task_assigned">Task Assigned</Option>
              <Option value="worker_login">Worker Login</Option>
              <Option value="worker_logout">Worker Logout</Option>
              <Option value="scan_event">Scan Event</Option>
              <Option value="ai_prediction">AI Prediction</Option>
              <Option value="ai_action">AI Action</Option>
              <Option value="system_alert">System Alert</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="warehouse_id"
            label="Warehouse ID"
            rules={[{ required: true, message: 'Please enter warehouse ID' }]}
          >
            <Input placeholder="warehouse_1" />
          </Form.Item>

          <Form.Item
            name="event_data"
            label="Event Data (JSON)"
            rules={[{ required: true, message: 'Please enter event data' }]}
          >
            <Input.TextArea 
              rows={4} 
              placeholder='{"task_id": "task_123", "priority": "high", "worker_id": "worker_1"}'
            />
          </Form.Item>

          <Form.Item
            name="correlation_id"
            label="Correlation ID"
          >
            <Input placeholder="Optional correlation ID" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={publishMutation.isPending}
                icon={<RocketOutlined />}
              >
                Publish Event
              </Button>
              <Button onClick={() => setEventModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Pattern Analysis Modal */}
      <Modal
        title="🔍 Pattern Analysis"
        open={predictionModalVisible}
        onCancel={() => {
          setPredictionModalVisible(false);
          predictionForm.resetFields();
        }}
        footer={null}
        width={800}
      >
        <Form
          form={predictionForm}
          layout="vertical"
          onFinish={handlePredictPattern}
          initialValues={{
            sequences: `task_created,worker_login,scan_event,task_completed
task_created,task_assigned,scan_event,worker_logout
worker_login,task_created,scan_event,task_completed,worker_logout`
          }}
        >
          <Alert
            message="Pattern Analysis"
            description="Enter event sequences (one per line, comma-separated) to analyze patterns like 'warehouse overload' or 'worker performance decline'."
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />

          <Form.Item
            name="sequences"
            label="Event Sequences"
            rules={[{ required: true, message: 'Please enter event sequences' }]}
          >
            <Input.TextArea 
              rows={8} 
              placeholder="task_created,worker_login,scan_event,task_completed&#10;task_created,task_assigned,scan_event,worker_logout&#10;worker_login,task_created,scan_event,task_completed,worker_logout"
            />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={predictionMutation.isPending}
                icon={<EyeOutlined />}
              >
                Analyze Patterns
              </Button>
              <Button onClick={() => setPredictionModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default LiveOpsDashboardPage;
