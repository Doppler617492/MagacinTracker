import React, { useState, useEffect } from 'react';
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
  Input,
  Descriptions,
  List,
  Avatar
} from 'antd';
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
  RocketOutlined,
  RadarChartOutlined,
  CloudServerOutlined,
  MobileOutlined,
  WifiOutlined,
  DisconnectOutlined,
  DesktopOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Line, Column, Area, Scatter } from '@ant-design/charts';
import {
  getKafkaMetrics,
  getKafkaAnalytics,
  getKafkaPerformance,
  publishKafkaEvent,
  getEdgeStatus,
  getEdgeHealth,
  getEdgePerformance,
  getEdgeModels,
  syncEdgeModels,
  forceEdgeSync,
  getEdgeHubStatus,
  performEdgeInference,
  KafkaMetrics,
  AnalyticsData,
  EdgeDeviceStatus,
  EdgePerformanceMetrics,
  EdgeInferenceRequest
} from '../api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const GlobalOpsDashboardPage: React.FC = () => {
  const [globalMode, setGlobalMode] = useState(true);
  const [edgeInferenceModalVisible, setEdgeInferenceModalVisible] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch global data
  const { data: kafkaMetrics, isLoading: kafkaLoading, refetch: refetchKafka } = useQuery({
    queryKey: ['kafka-metrics'],
    queryFn: getKafkaMetrics,
    refetchInterval: globalMode ? 3000 : false, // Refresh every 3 seconds in global mode
  });

  const { data: kafkaAnalytics, isLoading: analyticsLoading } = useQuery({
    queryKey: ['kafka-analytics'],
    queryFn: getKafkaAnalytics,
    refetchInterval: globalMode ? 5000 : false, // Refresh every 5 seconds in global mode
  });

  const { data: kafkaPerformance, isLoading: performanceLoading } = useQuery({
    queryKey: ['kafka-performance'],
    queryFn: getKafkaPerformance,
    refetchInterval: globalMode ? 10000 : false, // Refresh every 10 seconds in global mode
  });

  const { data: edgeStatus, isLoading: edgeLoading } = useQuery({
    queryKey: ['edge-status'],
    queryFn: getEdgeStatus,
    refetchInterval: globalMode ? 8000 : false, // Refresh every 8 seconds in global mode
  });

  const { data: edgeHealth, isLoading: healthLoading } = useQuery({
    queryKey: ['edge-health'],
    queryFn: getEdgeHealth,
    refetchInterval: globalMode ? 15000 : false, // Refresh every 15 seconds in global mode
  });

  const { data: edgeModels, isLoading: modelsLoading } = useQuery({
    queryKey: ['edge-models'],
    queryFn: getEdgeModels,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Mutations
  const syncMutation = useMutation({
    mutationFn: syncEdgeModels,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['edge-status'] });
      queryClient.invalidateQueries({ queryKey: ['edge-models'] });
      message.success(`Edge sync completed! Model version: ${data.model_version}`);
    },
    onError: (error: any) => {
      message.error('Edge sync failed');
      console.error('Sync error:', error);
    }
  });

  const inferenceMutation = useMutation({
    mutationFn: performEdgeInference,
    onSuccess: (data) => {
      message.success(`Edge inference completed! Prediction: ${Math.round(data.prediction * 100)}% (${data.inference_time_ms}ms)`);
      setEdgeInferenceModalVisible(false);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error('Edge inference failed');
      console.error('Inference error:', error);
    }
  });

  const handleEdgeSync = () => {
    syncMutation.mutate();
  };

  const handleEdgeInference = (values: any) => {
    const inferenceRequest: EdgeInferenceRequest = {
      inference_type: values.inference_type,
      device_id: values.device_id,
      warehouse_id: values.warehouse_id,
      input_data: JSON.parse(values.input_data || '{}'),
      request_id: `edge_inf_${Date.now()}`
    };
    
    inferenceMutation.mutate(inferenceRequest);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'degraded': return 'orange';
      case 'error': return 'red';
      case 'offline': return 'gray';
      default: return 'blue';
    }
  };

  const getHealthStatus = (health: any) => {
    if (!health) return 'unknown';
    return health.status || 'unknown';
  };

  const getDeviceStatusIcon = (status: string) => {
    switch (status) {
      case 'online': return <WifiOutlined style={{ color: '#52c41a' }} />;
      case 'offline': return <DisconnectOutlined style={{ color: '#ff4d4f' }} />;
      case 'degraded': return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      default: return <QuestionCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  // Prepare data for visualizations
  const prepareGlobalMapData = () => {
    if (!kafkaAnalytics?.analytics_data?.warehouse_metrics) return [];
    
    return Object.entries(kafkaAnalytics.analytics_data.warehouse_metrics).map(([warehouseId, metrics]: [string, any]) => ({
      warehouse: warehouseId,
      events_count: metrics.events_count,
      active_workers: metrics.active_workers.length,
      ai_decisions: metrics.ai_decisions,
      last_event: new Date(metrics.last_event).getTime(),
      status: metrics.events_count > 100 ? 'high_activity' : 'normal'
    }));
  };

  const prepareEdgeHealthData = () => {
    if (!edgeHealth?.health_metrics) return [];
    
    return [{
      device: edgeHealth.health_metrics.device_id,
      cpu_usage: edgeHealth.health_metrics.system_metrics.cpu_usage,
      memory_usage: edgeHealth.health_metrics.system_metrics.memory_usage,
      temperature: edgeHealth.health_metrics.system_metrics.temperature,
      battery_level: edgeHealth.health_metrics.system_metrics.battery_level,
      status: edgeHealth.health_metrics.status
    }];
  };

  const prepareKafkaThroughputData = (): Array<{time: number; events_per_second: number; latency_ms: number; consumer_lag: number}> => {
    const data: Array<{time: number; events_per_second: number; latency_ms: number; consumer_lag: number}> = [];
    const now = Date.now();
    
    for (let i = 0; i < 30; i++) {
      data.push({
        time: now - (29 - i) * 10000, // 10 seconds intervals
        events_per_second: Math.random() * 500 + 100,
        latency_ms: Math.random() * 50 + 10,
        consumer_lag: Math.random() * 10
      });
    }
    
    return data;
  };

  const globalMapData = prepareGlobalMapData();
  const edgeHealthData = prepareEdgeHealthData();
  const kafkaThroughputData = prepareKafkaThroughputData();

  // Chart configurations
  const globalMapChartConfig = {
    data: globalMapData,
    xField: 'warehouse',
    yField: 'events_count',
    color: (item: any) => item.status === 'high_activity' ? '#ff4d4f' : '#52c41a',
    point: {
      size: (item: any) => item.active_workers * 2,
      shape: 'circle',
    },
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Warehouses' },
    },
    yAxis: {
      title: { text: 'Events Count' },
    },
  };

  const edgeHealthChartConfig = {
    data: edgeHealthData,
    xField: 'device',
    yField: 'cpu_usage',
    color: '#1890ff',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Edge Devices' },
    },
    yAxis: {
      title: { text: 'CPU Usage %' },
    },
  };

  const kafkaThroughputChartConfig = {
    data: kafkaThroughputData,
    xField: 'time',
    yField: 'events_per_second',
    smooth: true,
    color: '#52c41a',
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

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>🌍 Global Operations Dashboard</Title>
        <Text type="secondary">Distributed intelligent system monitoring and control</Text>
      </div>

      {/* Global Mode Toggle */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <Switch
                checked={globalMode}
                onChange={setGlobalMode}
                checkedChildren="GLOBAL"
                unCheckedChildren="LOCAL"
              />
              <Text strong>Global Mode</Text>
            </Space>
          </Col>
          <Col>
            <Badge 
              status={globalMode ? "processing" : "default"} 
              text={globalMode ? "Distributed system active" : "Local monitoring only"}
            />
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => {
                  refetchKafka();
                  message.success('Global data refreshed');
                }}
              >
                Refresh Global
              </Button>
              <Button
                type="primary"
                icon={<ThunderboltOutlined />}
                onClick={handleEdgeSync}
                loading={syncMutation.isPending}
              >
                Sync Edge Devices
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Global System Metrics */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Kafka Throughput"
              value={kafkaMetrics?.metrics?.throughput_events_per_second || 0}
              precision={1}
              suffix="events/s"
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {kafkaMetrics?.metrics?.events_published || 0} total published
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Kafka Latency"
              value={kafkaMetrics?.metrics?.kafka_latency_ms || 0}
              precision={1}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: kafkaMetrics?.metrics?.kafka_latency_ms && kafkaMetrics.metrics.kafka_latency_ms > 250 ? '#ff4d4f' : '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {kafkaMetrics?.metrics?.consumer_lag || 0} consumer lag
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Edge Devices"
              value={edgeHealth?.health_metrics?.device_id ? 1 : 0}
              prefix={<MobileOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {edgeHealth?.health_metrics?.status === 'healthy' ? 'All healthy' : 'Issues detected'}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Global Uptime"
              value={99.95}
              precision={2}
              suffix="%"
              prefix={<CloudServerOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {kafkaMetrics?.metrics?.error_count || 0} errors
            </div>
          </Card>
        </Col>
      </Row>

      {/* System Health Alert */}
      {edgeHealth?.health_metrics?.status === 'degraded' && (
        <Alert
          message="⚠️ Edge Device Health Degraded"
          description={edgeHealth.health_metrics.issues?.join(', ') || 'Edge device performance issues detected'}
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" type="primary" onClick={handleEdgeSync}>
              Sync & Repair
            </Button>
          }
        />
      )}

      {/* Main Dashboard Tabs */}
      <Tabs defaultActiveKey="global-map" size="large">
        <TabPane tab="🗺️ Live AI Map" key="global-map">
          <Row gutter={16}>
            <Col xs={24} lg={16}>
              <Card title="Global Warehouse Network" loading={analyticsLoading}>
                <div style={{ height: '400px' }}>
                  {globalMapData.length > 0 ? (
                    <Scatter {...globalMapChartConfig} />
                  ) : (
                    <div style={{ 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      No warehouse data available
                    </div>
                  )}
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="Warehouse Status" loading={analyticsLoading}>
                <List
                  dataSource={globalMapData}
                  renderItem={(item: any) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={<Avatar icon={<NodeIndexOutlined />} />}
                        title={item.warehouse}
                        description={
                          <Space direction="vertical" size="small">
                            <div>Events: {item.events_count}</div>
                            <div>Workers: {item.active_workers}</div>
                            <div>AI Decisions: {item.ai_decisions}</div>
                            <Tag color={item.status === 'high_activity' ? 'red' : 'green'}>
                              {item.status === 'high_activity' ? 'High Activity' : 'Normal'}
                            </Tag>
                          </Space>
                        }
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="📱 Edge Device Health" key="edge-health">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Edge Device Performance" loading={healthLoading}>
                <div style={{ height: '300px' }}>
                  {edgeHealthData.length > 0 ? (
                    <Column {...edgeHealthChartConfig} />
                  ) : (
                    <div style={{ 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      No edge device data available
                    </div>
                  )}
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Device Status Details" loading={healthLoading}>
                {edgeStatus?.device_status && (
                  <Descriptions column={1} size="small">
                    <Descriptions.Item label="Device ID">
                      {edgeStatus.device_status.device_id}
                    </Descriptions.Item>
                    <Descriptions.Item label="Status">
                      <Space>
                        {getDeviceStatusIcon(edgeStatus.device_status.status)}
                        <Tag color={getStatusColor(edgeStatus.device_status.status)}>
                          {edgeStatus.device_status.status}
                        </Tag>
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="CPU Usage">
                      <Progress 
                        percent={edgeStatus.device_status.cpu_usage} 
                        size="small"
                        status={edgeStatus.device_status.cpu_usage > 80 ? "exception" : "active"}
                      />
                    </Descriptions.Item>
                    <Descriptions.Item label="Memory Usage">
                      <Progress 
                        percent={edgeStatus.device_status.memory_usage} 
                        size="small"
                        status={edgeStatus.device_status.memory_usage > 85 ? "exception" : "active"}
                      />
                    </Descriptions.Item>
                    <Descriptions.Item label="Temperature">
                      <Space>
                        <FireOutlined />
                        <Text>{edgeStatus.device_status.temperature}°C</Text>
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="Battery Level">
                      <Space>
                        <ThunderboltOutlined />
                        <Progress 
                          percent={edgeStatus.device_status.battery_level} 
                          size="small"
                          status={edgeStatus.device_status.battery_level < 20 ? "exception" : "active"}
                        />
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="Network Status">
                      <Space>
                        <WifiOutlined />
                        <Tag color={edgeStatus.device_status.network_status === 'connected' ? 'green' : 'red'}>
                          {edgeStatus.device_status.network_status}
                        </Tag>
                      </Space>
                    </Descriptions.Item>
                  </Descriptions>
                )}
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="📊 Kafka Stream Monitor" key="kafka-monitor">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Kafka Throughput" loading={kafkaLoading}>
                <div style={{ height: '300px' }}>
                  <Area {...kafkaThroughputChartConfig} />
                </div>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Kafka Performance Metrics" loading={performanceLoading}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Throughput Target:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, ((kafkaMetrics?.metrics?.throughput_events_per_second || 0) / 1000) * 100)} 
                        status={(kafkaMetrics?.metrics?.throughput_events_per_second || 0) > 1000 ? "success" : "active"}
                      />
                      {kafkaMetrics?.metrics?.throughput_events_per_second || 0} / 1000 events/s
                    </div>
                  </div>
                  <div>
                    <Text strong>Latency Target:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, 100 - ((kafkaMetrics?.metrics?.kafka_latency_ms || 0) / 250) * 100)} 
                        status={(kafkaMetrics?.metrics?.kafka_latency_ms || 0) < 250 ? "success" : "exception"}
                      />
                      {kafkaMetrics?.metrics?.kafka_latency_ms || 0}ms / 250ms target
                    </div>
                  </div>
                  <div>
                    <Text strong>Error Rate:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, ((kafkaMetrics?.metrics?.error_count || 0) / 10) * 100)} 
                        status={(kafkaMetrics?.metrics?.error_count || 0) < 5 ? "success" : "exception"}
                      />
                      {kafkaMetrics?.metrics?.error_count || 0} errors
                    </div>
                  </div>
                  <div>
                    <Text strong>Consumer Lag:</Text>
                    <div>
                      <Progress 
                        percent={Math.min(100, ((kafkaMetrics?.metrics?.consumer_lag || 0) / 10) * 100)} 
                        status={(kafkaMetrics?.metrics?.consumer_lag || 0) < 1 ? "success" : "exception"}
                      />
                      {kafkaMetrics?.metrics?.consumer_lag || 0} lag
                    </div>
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="🤖 Edge AI Models" key="edge-models">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Model Performance" loading={modelsLoading}>
                <Table
                  dataSource={edgeModels?.models ? Object.entries(edgeModels.models).map(([modelName, modelData]: [string, any]) => ({
                    key: modelName,
                    model: modelName,
                    version: modelData.model_version,
                    trained: modelData.trained,
                    inference_count: modelData.performance?.inference_count || 0,
                    avg_latency: modelData.performance?.average_latency_ms || 0,
                    success_rate: modelData.performance?.success_rate || 0,
                    model_size: modelData.performance?.model_size_kb || 0
                  })) : []}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: 'Model',
                      dataIndex: 'model',
                      key: 'model',
                      render: (model: string) => (
                        <Space>
                          <DatabaseOutlined />
                          <span>{model}</span>
                        </Space>
                      )
                    },
                    {
                      title: 'Version',
                      dataIndex: 'version',
                      key: 'version',
                      render: (version: string) => (
                        <Tag color="blue">{version}</Tag>
                      )
                    },
                    {
                      title: 'Trained',
                      dataIndex: 'trained',
                      key: 'trained',
                      render: (trained: boolean) => (
                        <Tag color={trained ? 'green' : 'red'}>
                          {trained ? 'Yes' : 'No'}
                        </Tag>
                      )
                    },
                    {
                      title: 'Latency (ms)',
                      dataIndex: 'avg_latency',
                      key: 'avg_latency',
                      render: (latency: number) => (
                        <Tag color={latency < 100 ? 'green' : 'red'}>
                          {latency.toFixed(1)}ms
                        </Tag>
                      )
                    },
                    {
                      title: 'Success Rate',
                      dataIndex: 'success_rate',
                      key: 'success_rate',
                      render: (rate: number) => (
                        <Progress 
                          percent={rate * 100} 
                          size="small"
                          status={rate > 0.95 ? "success" : "exception"}
                        />
                      )
                    }
                  ]}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Model Sync Status" loading={modelsLoading}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Last Sync:</Text>
                    <div>{edgeStatus?.device_status?.last_heartbeat ? new Date(edgeStatus.device_status.last_heartbeat).toLocaleString() : 'Never'}</div>
                  </div>
                  <div>
                    <Text strong>Sync Status:</Text>
                    <div>
                      <Tag color="green">Up to date</Tag>
                    </div>
                  </div>
                  <div>
                    <Text strong>Model Version:</Text>
                    <div>{edgeModels?.models?.transformer?.model_version || 'Unknown'}</div>
                  </div>
                  <div>
                    <Text strong>Sync Frequency:</Text>
                    <div>Every 30 minutes</div>
                  </div>
                  <Button
                    type="primary"
                    icon={<SyncOutlined />}
                    onClick={handleEdgeSync}
                    loading={syncMutation.isPending}
                    style={{ width: '100%' }}
                  >
                    Force Sync Now
                  </Button>
                </Space>
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
              onClick={() => setEdgeInferenceModalVisible(true)}
            >
              Test Edge Inference
            </Button>
          </Col>
          <Col>
            <Button
              icon={<RadarChartOutlined />}
              onClick={() => {
                refetchKafka();
                message.success('Global system refreshed');
              }}
            >
              Refresh Global System
            </Button>
          </Col>
          <Col>
            <Button
              icon={<SyncOutlined />}
              onClick={handleEdgeSync}
              loading={syncMutation.isPending}
            >
              Sync All Edge Devices
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Edge Inference Modal */}
      <Modal
        title="🤖 Test Edge AI Inference"
        open={edgeInferenceModalVisible}
        onCancel={() => {
          setEdgeInferenceModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEdgeInference}
          initialValues={{
            inference_type: 'worker_performance',
            device_id: 'edge_device_12345',
            warehouse_id: 'warehouse_1',
            input_data: '{"current_tasks": 5, "completed_tasks": 25, "efficiency_score": 0.75, "idle_time": 0.2, "experience_level": 0.8}'
          }}
        >
          <Form.Item
            name="inference_type"
            label="Inference Type"
            rules={[{ required: true, message: 'Please select inference type' }]}
          >
            <Select placeholder="Select inference type">
              <Option value="worker_performance">Worker Performance</Option>
              <Option value="task_optimization">Task Optimization</Option>
              <Option value="load_balancing">Load Balancing</Option>
              <Option value="anomaly_detection">Anomaly Detection</Option>
              <Option value="resource_allocation">Resource Allocation</Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="device_id"
                label="Device ID"
                rules={[{ required: true, message: 'Please enter device ID' }]}
              >
                <Input placeholder="edge_device_12345" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="warehouse_id"
                label="Warehouse ID"
                rules={[{ required: true, message: 'Please enter warehouse ID' }]}
              >
                <Input placeholder="warehouse_1" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="input_data"
            label="Input Data (JSON)"
            rules={[{ required: true, message: 'Please enter input data' }]}
          >
            <Input.TextArea 
              rows={6} 
              placeholder='{"current_tasks": 5, "completed_tasks": 25, "efficiency_score": 0.75, "idle_time": 0.2, "experience_level": 0.8, "workload": 0.6, "time_of_day": 14, "day_of_week": 2}'
            />
          </Form.Item>

          <Alert
            message="Edge AI Inference"
            description="This will perform ultra-fast AI inference on the edge device with <100ms latency. The device will make autonomous decisions based on the input data."
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={inferenceMutation.isPending}
                icon={<ThunderboltOutlined />}
              >
                Perform Edge Inference
              </Button>
              <Button onClick={() => setEdgeInferenceModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default GlobalOpsDashboardPage;
