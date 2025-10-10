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
  Popconfirm
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
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Line, Column } from '@ant-design/charts';
import {
  getAIModelStatus,
  getAIModelPerformance,
  trainAIModel,
  getTrainingStatus,
  cancelTraining,
  resetAIModels,
  ModelStatus,
  TrainingRequest,
  TrainingResponse
} from '../api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const AIModelDashboardPage: React.FC = () => {
  const [trainingModalVisible, setTrainingModalVisible] = useState(false);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch AI model status and performance
  const { data: modelStatus, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
    queryKey: ['ai-model-status'],
    queryFn: getAIModelStatus,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: modelPerformance, isLoading: performanceLoading } = useQuery({
    queryKey: ['ai-model-performance'],
    queryFn: getAIModelPerformance,
    refetchInterval: 60000, // Refresh every minute
  });

  // Training mutation
  const trainingMutation = useMutation({
    mutationFn: trainAIModel,
    onSuccess: (data: TrainingResponse) => {
      queryClient.invalidateQueries({ queryKey: ['ai-model-status'] });
      queryClient.invalidateQueries({ queryKey: ['ai-model-performance'] });
      setTrainingModalVisible(false);
      form.resetFields();
      message.success(`Model ${data.model_type} je uspešno treniran! Tačnost: ${Math.round(data.final_accuracy * 100)}%`);
    },
    onError: (error: any) => {
      message.error('Greška pri treniranju modela');
      console.error('Training error:', error);
    }
  });

  const resetMutation = useMutation({
    mutationFn: resetAIModels,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-model-status'] });
      queryClient.invalidateQueries({ queryKey: ['ai-model-performance'] });
      message.success('Svi AI modeli su resetovani');
    },
    onError: (error: any) => {
      message.error('Greška pri resetovanju modela');
      console.error('Reset error:', error);
    }
  });

  const handleStartTraining = () => {
    setTrainingModalVisible(true);
  };

  const handleTrainingSubmit = async (values: any) => {
    const trainingRequest: TrainingRequest = {
      model_type: values.model_type,
      epochs: values.epochs,
      learning_rate: values.learning_rate,
      batch_size: values.batch_size
    };
    
    trainingMutation.mutate(trainingRequest);
  };

  const handleResetModels = () => {
    resetMutation.mutate();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'fully_trained': return 'green';
      case 'partially_trained': return 'orange';
      case 'not_trained': return 'red';
      default: return 'blue';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'fully_trained': return 'Potpuno treniran';
      case 'partially_trained': return 'Delimično treniran';
      case 'not_trained': return 'Nije treniran';
      default: return 'Nepoznat';
    }
  };

  const getModelIcon = (modelType: string) => {
    switch (modelType) {
      case 'neural_network': return <BulbOutlined style={{ color: '#1890ff' }} />;
      case 'reinforcement_learning': return <RobotOutlined style={{ color: '#52c41a' }} />;
      default: return <BulbOutlined />;
    }
  };

  // Prepare training history data for charts
  const prepareTrainingHistoryData = () => {
    if (!modelStatus?.neural_network?.training_status?.is_trained) {
      return [];
    }

    // Mock training history data (in production, this would come from the API)
    const epochs = Array.from({ length: 100 }, (_, i) => i + 1);
    return epochs.map(epoch => ({
      epoch,
      loss: Math.max(0.01, 0.5 * Math.exp(-epoch / 30) + 0.01),
      accuracy: Math.min(0.95, 0.3 + 0.6 * (1 - Math.exp(-epoch / 25)))
    }));
  };

  const trainingHistoryData = prepareTrainingHistoryData();

  // Chart configurations
  const lossChartConfig = {
    data: trainingHistoryData,
    xField: 'epoch',
    yField: 'loss',
    smooth: true,
    color: '#ff4d4f',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Epoch' },
    },
    yAxis: {
      title: { text: 'Loss' },
    },
  };

  const accuracyChartConfig = {
    data: trainingHistoryData,
    xField: 'epoch',
    yField: 'accuracy',
    smooth: true,
    color: '#52c41a',
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    xAxis: {
      title: { text: 'Epoch' },
    },
    yAxis: {
      title: { text: 'Accuracy' },
    },
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>AI Model Dashboard</Title>
        <Text type="secondary">Upravljanje i monitoring AI modela za optimizaciju magacina</Text>
      </div>

      {/* Overall Status */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={16} align="middle">
          <Col>
            <Space>
              <BulbOutlined style={{ fontSize: '24px', color: '#1890ff' }} />
              <div>
                <div style={{ fontSize: '18px', fontWeight: 500 }}>AI Model Status</div>
                <div style={{ fontSize: '14px', color: '#666' }}>
                  {modelStatus ? getStatusText(modelStatus.overall_status) : 'Učitavanje...'}
                </div>
              </div>
            </Space>
          </Col>
          <Col flex="auto" />
          <Col>
            <Space>
              <Tag color={getStatusColor(modelStatus?.overall_status || 'not_trained')}>
                {modelStatus ? getStatusText(modelStatus.overall_status) : 'Nepoznat'}
              </Tag>
              <Button
                icon={<ReloadOutlined />}
                onClick={() => refetchStatus()}
                loading={statusLoading}
              >
                Osveži
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Model Statistics */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Neural Network"
              value={modelStatus?.neural_network?.performance?.final_accuracy ? Math.round(modelStatus.neural_network.performance.final_accuracy * 100) : 0}
              suffix="%"
              prefix={getModelIcon('neural_network')}
              valueStyle={{ color: '#1890ff' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {modelStatus?.neural_network?.training_status?.is_trained ? 'Treniran' : 'Nije treniran'}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Reinforcement Learning"
              value={modelStatus?.reinforcement_learning?.performance?.average_reward ? Math.round(modelStatus.reinforcement_learning.performance.average_reward) : 0}
              suffix=" pts"
              prefix={getModelIcon('reinforcement_learning')}
              valueStyle={{ color: '#52c41a' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              {modelStatus?.reinforcement_learning?.training_status?.is_trained ? 'Treniran' : 'Nije treniran'}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno parametara"
              value={modelStatus?.neural_network?.architecture?.total_parameters || 0}
              prefix={<BarChartOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Neural Network
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Epizode treniranja"
              value={modelStatus?.reinforcement_learning?.training_status?.total_episodes || 0}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
            <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
              Reinforcement Learning
            </div>
          </Card>
        </Col>
      </Row>

      {/* Training Status Alert */}
      {modelStatus?.overall_status === 'not_trained' && (
        <Alert
          message="🤖 AI modeli nisu trenirani"
          description="Za optimalne preporuke, potrebno je trenirati neuralnu mrežu i reinforcement learning model. Kliknite 'Treniraj sada' da počnete."
          type="warning"
          showIcon
          style={{ marginBottom: '24px' }}
          action={
            <Button size="small" type="primary" onClick={handleStartTraining}>
              Treniraj sada
            </Button>
          }
        />
      )}

      {/* Training Charts */}
      {modelStatus?.neural_network?.training_status?.is_trained && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col xs={24} lg={12}>
            <Card title="Training Loss" loading={statusLoading}>
              <div style={{ height: '300px' }}>
                {trainingHistoryData.length > 0 ? (
                  <Line {...lossChartConfig} />
                ) : (
                  <div style={{ 
                    height: '100%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    color: '#999'
                  }}>
                    Nema podataka o treniranju
                  </div>
                )}
              </div>
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="Training Accuracy" loading={statusLoading}>
              <div style={{ height: '300px' }}>
                {trainingHistoryData.length > 0 ? (
                  <Line {...accuracyChartConfig} />
                ) : (
                  <div style={{ 
                    height: '100%', 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    color: '#999'
                  }}>
                    Nema podataka o treniranju
                  </div>
                )}
              </div>
            </Card>
          </Col>
        </Row>
      )}

      {/* Model Details */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={12}>
          <Card title="Neural Network Model" loading={statusLoading}>
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Arhitektura:</Text>
              <div style={{ marginTop: '8px' }}>
                <div>Input: {modelStatus?.neural_network?.architecture?.input_size || 0} neurons</div>
                <div>Hidden: {modelStatus?.neural_network?.architecture?.hidden_size || 0} neurons</div>
                <div>Output: {modelStatus?.neural_network?.architecture?.output_size || 0} neurons</div>
              </div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Performanse:</Text>
              <div style={{ marginTop: '8px' }}>
                <div>Finalna tačnost: {modelStatus?.neural_network?.performance?.final_accuracy ? Math.round(modelStatus.neural_network.performance.final_accuracy * 100) : 0}%</div>
                <div>Najbolja tačnost: {modelStatus?.neural_network?.performance?.best_accuracy ? Math.round(modelStatus.neural_network.performance.best_accuracy * 100) : 0}%</div>
                <div>Finalni loss: {modelStatus?.neural_network?.performance?.final_loss?.toFixed(4) || 'N/A'}</div>
              </div>
            </div>
            
            <div>
              <Text strong>Status treniranja:</Text>
              <div style={{ marginTop: '8px' }}>
                <div>Sesije treniranja: {modelStatus?.neural_network?.training_status?.training_sessions || 0}</div>
                <div>Poslednje treniranje: {modelStatus?.neural_network?.training_status?.last_trained ? new Date(modelStatus.neural_network.training_status.last_trained).toLocaleString('sr-RS') : 'Nikad'}</div>
              </div>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Reinforcement Learning Model" loading={statusLoading}>
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Konfiguracija:</Text>
              <div style={{ marginTop: '8px' }}>
                <div>State size: {modelStatus?.reinforcement_learning?.architecture?.state_size || 0}</div>
                <div>Action size: {modelStatus?.reinforcement_learning?.architecture?.action_size || 0}</div>
                <div>Learning rate: {modelStatus?.reinforcement_learning?.architecture?.learning_rate || 0}</div>
                <div>Discount factor: {modelStatus?.reinforcement_learning?.architecture?.discount_factor || 0}</div>
              </div>
            </div>
            
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Performanse:</Text>
              <div style={{ marginTop: '8px' }}>
                <div>Prosečna nagrada: {modelStatus?.reinforcement_learning?.performance?.average_reward?.toFixed(2) || 0}</div>
                <div>Najbolja nagrada: {modelStatus?.reinforcement_learning?.performance?.best_reward?.toFixed(2) || 0}</div>
                <div>Epizoda konvergencije: {modelStatus?.reinforcement_learning?.performance?.convergence_episode || 'N/A'}</div>
              </div>
            </div>
            
            <div>
              <Text strong>Status treniranja:</Text>
              <div style={{ marginTop: '8px' }}>
                <div>Ukupno epizoda: {modelStatus?.reinforcement_learning?.training_status?.total_episodes || 0}</div>
                <div>Poslednje treniranje: {modelStatus?.reinforcement_learning?.training_status?.last_trained ? new Date(modelStatus.reinforcement_learning.training_status.last_trained).toLocaleString('sr-RS') : 'Nikad'}</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Action Buttons */}
      <Card>
        <Row gutter={16}>
          <Col>
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={handleStartTraining}
              loading={trainingMutation.isPending}
            >
              Treniraj sada
            </Button>
          </Col>
          <Col>
            <Button
              size="large"
              icon={<ReloadOutlined />}
              onClick={() => {
                refetchStatus();
                message.success('Status modela osvežen');
              }}
            >
              Osveži status
            </Button>
          </Col>
          <Col>
            <Popconfirm
              title="Resetuj AI modele"
              description="Da li ste sigurni da želite da resetujete sve AI modele? Ovo će obrisati sve treniranje."
              onConfirm={handleResetModels}
              okText="Da"
              cancelText="Ne"
            >
              <Button
                size="large"
                danger
                icon={<ExclamationCircleOutlined />}
                loading={resetMutation.isPending}
              >
                Resetuj modele
              </Button>
            </Popconfirm>
          </Col>
        </Row>
      </Card>

      {/* Training Modal */}
      <Modal
        title="Treniraj AI Model"
        open={trainingModalVisible}
        onCancel={() => {
          setTrainingModalVisible(false);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleTrainingSubmit}
          initialValues={{
            model_type: 'neural_network',
            epochs: 100,
            learning_rate: 0.001,
            batch_size: 32
          }}
        >
          <Form.Item
            name="model_type"
            label="Tip modela"
            rules={[{ required: true, message: 'Molimo odaberite tip modela' }]}
          >
            <Select placeholder="Odaberite tip modela">
              <Option value="neural_network">
                <Space>
                  <BulbOutlined />
                  <span>Neural Network (Predviđanje performansi)</span>
                </Space>
              </Option>
              <Option value="reinforcement_learning">
                <Space>
                  <RobotOutlined />
                  <span>Reinforcement Learning (Adaptivna optimizacija)</span>
                </Space>
              </Option>
            </Select>
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="epochs"
                label="Broj epoha"
                rules={[{ required: true, message: 'Molimo unesite broj epoha' }]}
              >
                <InputNumber
                  min={10}
                  max={1000}
                  style={{ width: '100%' }}
                  placeholder="100"
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="learning_rate"
                label="Learning rate"
                rules={[{ required: true, message: 'Molimo unesite learning rate' }]}
              >
                <InputNumber
                  min={0.0001}
                  max={0.1}
                  step={0.001}
                  style={{ width: '100%' }}
                  placeholder="0.001"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="batch_size"
            label="Batch size"
            rules={[{ required: true, message: 'Molimo unesite batch size' }]}
          >
            <InputNumber
              min={8}
              max={128}
              style={{ width: '100%' }}
              placeholder="32"
            />
          </Form.Item>

          <Alert
            message="Treniranje može potrajati"
            description="Neural Network treniranje može potrajati do 60 sekundi, Reinforcement Learning do 2 minuta."
            type="info"
            showIcon
            style={{ marginBottom: '16px' }}
          />

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={trainingMutation.isPending}
                icon={<PlayCircleOutlined />}
              >
                Počni treniranje
              </Button>
              <Button onClick={() => setTrainingModalVisible(false)}>
                Otkaži
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIModelDashboardPage;
