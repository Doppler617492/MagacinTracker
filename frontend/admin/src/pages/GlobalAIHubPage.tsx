import React, { useState } from 'react';
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
  Popconfirm,
  Tabs,
  Badge,
  Timeline
} from 'antd';
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  BulbOutlined,
  RobotOutlined,
  BarChartOutlined,
  LineOutlined,
  TrophyOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  SyncOutlined,
  GlobalOutlined,
  NodeIndexOutlined,
  ThunderboltOutlined,
  EyeOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Line, Column, Heatmap } from '@ant-design/charts';
import {
  getFederatedSystemStatus,
  aggregateFederatedModels,
  getEdgeSystemStatus,
  syncEdgeModels,
  getDNNStatus,
  trainDNNModel,
  predictDNN,
  FederatedSystemStatus,
  EdgeSystemStatus,
  DNNTrainingRequest,
  DNNPredictionRequest
} from '../api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;

const GlobalAIHubPage: React.FC = () => {
  const [predictionModalVisible, setPredictionModalVisible] = useState(false);
  const [explainModalVisible, setExplainModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [predictionForm] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch system statuses
  const { data: federatedStatus, isLoading: federatedLoading, refetch: refetchFederated } = useQuery({
    queryKey: ['federated-system-status'],
    queryFn: getFederatedSystemStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: edgeStatus, isLoading: edgeLoading, refetch: refetchEdge } = useQuery({
    queryKey: ['edge-system-status'],
    queryFn: getEdgeSystemStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: dnnStatus, isLoading: dnnLoading, refetch: refetchDNN } = useQuery({
    queryKey: ['dnn-status'],
    queryFn: getDNNStatus,
    refetchInterval: 60000, // Refresh every minute
  });

  // Mutations
  const aggregationMutation = useMutation({
    mutationFn: aggregateFederatedModels,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['federated-system-status'] });
      message.success(`Federated aggregation completed! ${data.nodes_participated} nodes participated`);
    },
    onError: (error: any) => {
      message.error('Federated aggregation failed');
      console.error('Aggregation error:', error);
    }
  });

  const syncMutation = useMutation({
    mutationFn: syncEdgeModels,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['edge-system-status'] });
      message.success(`Edge sync completed! ${data.models_updated} models updated`);
    },
    onError: (error: any) => {
      message.error('Edge sync failed');
      console.error('Sync error:', error);
    }
  });

  const dnnTrainingMutation = useMutation({
    mutationFn: trainDNNModel,
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['dnn-status'] });
      message.success(`DNN training completed! Accuracy: ${Math.round(data.final_accuracy * 100)}%`);
    },
    onError: (error: any) => {
      message.error('DNN training failed');
      console.error('DNN training error:', error);
    }
  });

  const predictionMutation = useMutation({
    mutationFn: predictDNN,
    onSuccess: (data) => {
      setExplainModalVisible(true);
      message.success(`Prediction completed! Performance: ${Math.round(data.prediction * 100)}%`);
    },
    onError: (error: any) => {
      message.error('Prediction failed');
      console.error('Prediction error:', error);
    }
  });

  const handleAggregateNow = () => {
    aggregationMutation.mutate();
  };

  const handleSyncNow = () => {
    syncMutation.mutate();
  };

  const handleDNNTraining = (values: any) => {
    const trainingRequest: DNNTrainingRequest = {
      epochs: values.epochs,
      learning_rate: values.learning_rate,
      batch_size: values.batch_size,
      validation_split: values.validation_split
    };
    
    dnnTrainingMutation.mutate(trainingRequest);
  };

  const handlePrediction = (values: any) => {
    const predictionRequest: DNNPredictionRequest = {
      features: [
        values.current_tasks / 15.0,
        values.completed_tasks / 60.0,
        values.avg_completion_time / 15.0,
        values.efficiency_score,
        values.idle_time_percentage,
        values.day_of_week / 7.0,
        values.hour_of_day / 24.0,
        values.store_load_index,
        values.seasonality_factor,
        values.product_complexity,
        values.worker_experience,
        values.team_size / 10.0
      ],
      include_feature_importance: true
    };
    
    predictionMutation.mutate(predictionRequest);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'green';
      case 'syncing': return 'blue';
      case 'error': return 'red';
      case 'offline': return 'gray';
      default: return 'blue';
    }
  };

  const getNodeStatusColor = (node: any) => {
    if (!node.is_initialized) return 'red';
    if (node.is_syncing) return 'blue';
    if (node.should_sync) return 'orange';
    return 'green';
  };

  // Prepare data for visualizations
  const prepareFederatedSyncData = () => {
    if (!federatedStatus?.nodes) return [];
    
    return Object.entries(federatedStatus.nodes).map(([nodeId, node]: [string, any]) => ({
      node: nodeId,
      last_sync: node.last_sync ? new Date(node.last_sync).getTime() : 0,
      training_samples: node.training_samples,
      status: node.is_initialized ? 'active' : 'inactive'
    }));
  };

  const prepareEdgePerformanceData = () => {
    if (!edgeStatus?.models) return [];
    
    return Object.entries(edgeStatus.models).map(([modelId, model]: [string, any]) => ({
      model: modelId,
      avg_inference_time: model.performance_stats?.avg_inference_time_ms || 0,
      total_inferences: model.performance_stats?.total_inferences || 0,
      performance_target_met: model.performance_stats?.performance_target_met || false
    }));
  };

  const prepareModelAccuracyData = () => {
    const data = [];
    const locations = ['Podgorica DC', 'Nikšić Store', 'Bar Store', 'Ulcinj Store', 'Pljevlja Store'];
    
    for (let i = 0; i < 30; i++) {
      const date = new Date();
      date.setDate(date.getDate() - (29 - i));
      
      locations.forEach(location => {
        data.push({
          date: date.toISOString().split('T')[0],
          location,
          accuracy: 0.75 + Math.random() * 0.2 + (Math.sin(i / 5) * 0.1)
        });
      });
    }
    
    return data;
  };

  const federatedSyncData = prepareFederatedSyncData();
  const edgePerformanceData = prepareEdgePerformanceData();
  const modelAccuracyData = prepareModelAccuracyData();

  // Chart configurations
  const federatedSyncChartConfig = {
    data: federatedSyncData,
    xField: 'node',
    yField: 'training_samples',
    color: (item: any) => item.status === 'active' ? '#52c41a' : '#ff4d4f',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Federated Nodes' },
    },
    yAxis: {
      title: { text: 'Training Samples' },
    },
  };

  const edgePerformanceChartConfig = {
    data: edgePerformanceData,
    xField: 'model',
    yField: 'avg_inference_time',
    color: (item: any) => item.performance_target_met ? '#52c41a' : '#ff4d4f',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Edge Models' },
    },
    yAxis: {
      title: { text: 'Inference Time (ms)' },
    },
  };

  const modelAccuracyHeatmapConfig = {
    data: modelAccuracyData,
    xField: 'date',
    yField: 'location',
    colorField: 'accuracy',
    color: ['#ff4d4f', '#faad14', '#52c41a'],
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>🌍 Global AI Hub</Title>
        <Text type="secondary">Centralized AI management across all warehouses and locations</Text>
      </div>

      {/* Global Status Overview */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Federated Nodes"
              value={federatedStatus?.aggregation_status?.total_nodes || 0}
              prefix={<NodeIndexOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {federatedStatus?.aggregation_status?.trained_nodes || 0} trained
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Edge Models"
              value={edgeStatus?.total_models || 0}
              prefix={<ThunderboltOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {edgeStatus?.initialized_models || 0} initialized
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Global Model Version"
              value={federatedStatus?.global_model?.version || 0}
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {federatedStatus?.global_model?.total_samples || 0} samples
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Edge Predictions"
              value={edgeStatus?.total_predictions || 0}
              prefix={<BulbOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {edgeStatus?.sync_errors || 0} sync errors
            </div>
          </Card>
        </Col>
      </Row>

      {/* Action Buttons */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16}>
          <Col>
            <Button
              type="primary"
              size="large"
              icon={<SyncOutlined />}
              onClick={handleAggregateNow}
              loading={aggregationMutation.isPending}
            >
              Aggregate Now
            </Button>
          </Col>
          <Col>
            <Button
              size="large"
              icon={<ReloadOutlined />}
              onClick={handleSyncNow}
              loading={syncMutation.isPending}
            >
              Sync Edge Models
            </Button>
          </Col>
          <Col>
            <Button
              size="large"
              icon={<EyeOutlined />}
              onClick={() => setPredictionModalVisible(true)}
            >
              Test Prediction
            </Button>
          </Col>
          <Col>
            <Button
              size="large"
              icon={<ReloadOutlined />}
              onClick={() => {
                refetchFederated();
                refetchEdge();
                refetchDNN();
                message.success('All systems refreshed');
              }}
            >
              Refresh All
            </Button>
          </Col>
        </Row>
      </Card>

      {/* Main Dashboard Tabs */}
      <Tabs defaultActiveKey="federated" size="large">
        <TabPane tab="🔄 Federated Learning" key="federated">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Federated Nodes Status" loading={federatedLoading}>
                <Table
                  dataSource={federatedSyncData}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: 'Node',
                      dataIndex: 'node',
                      key: 'node',
                      render: (node: string) => (
                        <Space>
                          <NodeIndexOutlined />
                          <span>{node}</span>
                        </Space>
                      )
                    },
                    {
                      title: 'Status',
                      dataIndex: 'status',
                      key: 'status',
                      render: (status: string) => (
                        <Tag color={status === 'active' ? 'green' : 'red'}>
                          {status === 'active' ? 'Active' : 'Inactive'}
                        </Tag>
                      )
                    },
                    {
                      title: 'Samples',
                      dataIndex: 'training_samples',
                      key: 'training_samples',
                      render: (samples: number | undefined) =>
                        typeof samples === 'number' ? samples.toLocaleString() : '0'
                    }
                  ]}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Training Samples Distribution" loading={federatedLoading}>
                <div style={{ height: '300px' }}>
                  {federatedSyncData.length > 0 ? (
                    <Column {...federatedSyncChartConfig} />
                  ) : (
                    <div style={{ 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      No federated data available
                    </div>
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="⚡ Edge Inference" key="edge">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="Edge Models Performance" loading={edgeLoading}>
                <Table
                  dataSource={edgePerformanceData}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: 'Model',
                      dataIndex: 'model',
                      key: 'model',
                      render: (model: string) => (
                        <Space>
                          <ThunderboltOutlined />
                          <span>{model}</span>
                        </Space>
                      )
                    },
                    {
                      title: 'Avg Time (ms)',
                      dataIndex: 'avg_inference_time',
                      key: 'avg_inference_time',
                      render: (time: number) => (
                        <Tag color={time < 200 ? 'green' : 'red'}>
                          {time.toFixed(1)}ms
                        </Tag>
                      )
                    },
                    {
                      title: 'Predictions',
                      dataIndex: 'total_inferences',
                      key: 'total_inferences',
                      render: (count: number | undefined) =>
                        typeof count === 'number' ? count.toLocaleString() : '0'
                    }
                  ]}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Inference Performance" loading={edgeLoading}>
                <div style={{ height: '300px' }}>
                  {edgePerformanceData.length > 0 ? (
                    <Column {...edgePerformanceChartConfig} />
                  ) : (
                    <div style={{ 
                      height: '100%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      color: '#999'
                    }}>
                      No edge performance data available
                    </div>
                  )}
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="🧠 Deep Neural Network" key="dnn">
          <Row gutter={16}>
            <Col xs={24} lg={12}>
              <Card title="DNN Model Status" loading={dnnLoading}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Model Version:</Text>
                    <div>{dnnStatus?.model_version || 0}</div>
                  </div>
                  <div>
                    <Text strong>Accuracy:</Text>
                    <div>{dnnStatus?.accuracy ? Math.round(dnnStatus.accuracy * 100) : 0}%</div>
                  </div>
                  <div>
                    <Text strong>Parameters:</Text>
                    <div>{
                      typeof dnnStatus?.total_parameters === 'number'
                        ? dnnStatus.total_parameters.toLocaleString()
                        : 0
                    }</div>
                  </div>
                  <div>
                    <Text strong>Last Trained:</Text>
                    <div>{dnnStatus?.last_trained ? new Date(dnnStatus.last_trained).toLocaleString() : 'Never'}</div>
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Model Accuracy Heatmap" loading={dnnLoading}>
                <div style={{ height: '300px' }}>
                  <Heatmap {...modelAccuracyHeatmapConfig} />
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="📊 Global Analytics" key="analytics">
          <Row gutter={16}>
            <Col xs={24}>
              <Card title="Model Performance Across Locations">
                <div style={{ height: '400px' }}>
                  <Heatmap {...modelAccuracyHeatmapConfig} />
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* Prediction Modal */}
      <Modal
        title="🧠 Test Deep Neural Network Prediction"
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
          onFinish={handlePrediction}
          initialValues={{
            current_tasks: 5,
            completed_tasks: 25,
            avg_completion_time: 4.5,
            efficiency_score: 0.75,
            idle_time_percentage: 0.2,
            day_of_week: 1,
            hour_of_day: 12,
            store_load_index: 0.6,
            seasonality_factor: 0.5,
            product_complexity: 0.5,
            worker_experience: 0.7,
            team_size: 3
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="current_tasks" label="Current Tasks">
                <InputNumber min={0} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="completed_tasks" label="Completed Tasks Today">
                <InputNumber min={0} max={100} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="avg_completion_time" label="Avg Completion Time (min)">
                <InputNumber min={1} max={15} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="efficiency_score" label="Efficiency Score">
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="idle_time_percentage" label="Idle Time %">
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="store_load_index" label="Store Load Index">
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="day_of_week" label="Day of Week">
                <InputNumber min={0} max={6} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="hour_of_day" label="Hour of Day">
                <InputNumber min={0} max={23} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="seasonality_factor" label="Seasonality Factor">
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="product_complexity" label="Product Complexity">
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="worker_experience" label="Worker Experience">
                <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="team_size" label="Team Size">
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={predictionMutation.isPending}
                icon={<BulbOutlined />}
              >
                Predict Performance
              </Button>
              <Button onClick={() => setPredictionModalVisible(false)}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Explain Prediction Modal */}
      <Modal
        title="🔍 Prediction Explanation"
        open={explainModalVisible}
        onCancel={() => setExplainModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setExplainModalVisible(false)}>
            Close
          </Button>
        ]}
        width={600}
      >
        {predictionMutation.data && (
          <div>
            <Alert
              message={`Predicted Performance: ${Math.round(predictionMutation.data.prediction * 100)}%`}
              description={`Confidence: ${Math.round(predictionMutation.data.confidence * 100)}% | Processing Time: ${predictionMutation.data.processing_time_ms.toFixed(1)}ms`}
              type="info"
              showIcon
              style={{ marginBottom: '16px' }}
            />
            
            {predictionMutation.data.feature_importance && (
              <div>
                <Title level={4}>Feature Importance</Title>
                <Table
                  dataSource={Object.entries(predictionMutation.data.feature_importance).map(([feature, importance]) => ({
                    key: feature,
                    feature,
                    importance: Number(importance)
                  }))}
                  pagination={false}
                  size="small"
                  columns={[
                    {
                      title: 'Feature',
                      dataIndex: 'feature',
                      key: 'feature',
                    },
                    {
                      title: 'Importance',
                      dataIndex: 'importance',
                      key: 'importance',
                      render: (importance: number) => (
                        <Progress 
                          percent={Math.abs(importance) * 100} 
                          size="small" 
                          status={importance > 0 ? 'active' : 'exception'}
                        />
                      )
                    }
                  ]}
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default GlobalAIHubPage;
