import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic,
  Progress,
  Typography,
  Divider,
  Alert,
  Badge
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  EyeOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  BulbOutlined,
  RiseOutlined,
  UserOutlined,
  ShopOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Column } from '@ant-design/charts';
import {
  getAIRecommendations,
  applyRecommendation,
  dismissRecommendation,
  simulateLoadBalance,
  AIRecommendation,
  LoadBalanceSimulation
} from '../api';

const { Title, Text, Paragraph } = Typography;

const AIRecommendationsPage: React.FC = () => {
  const [simulationModalVisible, setSimulationModalVisible] = useState(false);
  const [selectedRecommendation, setSelectedRecommendation] = useState<AIRecommendation | null>(null);
  const [simulationData, setSimulationData] = useState<LoadBalanceSimulation | null>(null);
  const queryClient = useQueryClient();

  // Fetch AI recommendations
  const { data: recommendations = [], isLoading, refetch } = useQuery({
    queryKey: ['ai-recommendations'],
    queryFn: getAIRecommendations,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Mutations
  const applyMutation = useMutation({
    mutationFn: applyRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-recommendations'] });
      message.success('Preporuka je uspešno primijenjena!');
    },
    onError: (error: any) => {
      message.error('Greška pri primjeni preporuke');
      console.error('Apply error:', error);
    }
  });

  const dismissMutation = useMutation({
    mutationFn: dismissRecommendation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai-recommendations'] });
      message.success('Preporuka je odbačena');
    },
    onError: (error: any) => {
      message.error('Greška pri odbacivanju preporuke');
      console.error('Dismiss error:', error);
    }
  });

  const simulateMutation = useMutation({
    mutationFn: simulateLoadBalance,
    onSuccess: (data: LoadBalanceSimulation) => {
      setSimulationData(data);
      setSimulationModalVisible(true);
    },
    onError: (error: any) => {
      message.error('Greška pri simulaciji');
      console.error('Simulate error:', error);
    }
  });

  const handleApply = (recommendationId: string) => {
    applyMutation.mutate(recommendationId);
  };

  const handleDismiss = (recommendationId: string) => {
    dismissMutation.mutate(recommendationId);
  };

  const handleSimulate = (recommendation: AIRecommendation) => {
    setSelectedRecommendation(recommendation);
    
    // Mock data for simulation
    const mockSimulationRequest = {
      recommendation_id: recommendation.id,
      worker_metrics: [
        {
          worker_id: "worker_001",
          worker_name: "Marko Šef",
          current_tasks: 8,
          completed_tasks_today: 25,
          avg_completion_time: 4.2,
          efficiency_score: 0.85,
          idle_time_percentage: 0.15,
          location: "pantheon"
        },
        {
          worker_id: "worker_002",
          worker_name: "Ana Radnik",
          current_tasks: 12,
          completed_tasks_today: 18,
          avg_completion_time: 5.1,
          efficiency_score: 0.72,
          idle_time_percentage: 0.05,
          location: "pantheon"
        }
      ],
      store_metrics: [
        {
          store_id: "pantheon",
          store_name: "Pantheon",
          total_tasks: 45,
          completed_tasks: 30,
          pending_tasks: 15,
          avg_completion_time: 4.6,
          worker_count: 2,
          load_index: 0.75,
          efficiency_delta: 0.05
        },
        {
          store_id: "maxi",
          store_name: "Maxi",
          total_tasks: 20,
          completed_tasks: 18,
          pending_tasks: 2,
          avg_completion_time: 3.9,
          worker_count: 1,
          load_index: 0.20,
          efficiency_delta: -0.02
        }
      ]
    };

    simulateMutation.mutate(mockSimulationRequest);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'blue';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'load_balance': return <RiseOutlined />;
      case 'resource_allocation': return <UserOutlined />;
      case 'task_reassignment': return <ShopOutlined />;
      case 'efficiency_optimization': return <BulbOutlined />;
      default: return <BulbOutlined />;
    }
  };

  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.9) return <Badge status="success" text="Visoko pouzdano" />;
    if (confidence >= 0.7) return <Badge status="warning" text="Srednje pouzdano" />;
    return <Badge status="error" text="Nisko pouzdano" />;
  };

  const columns = [
    {
      title: 'Tip',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Space>
          {getTypeIcon(type)}
          <span>{type.replace('_', ' ').toUpperCase()}</span>
        </Space>
      ),
    },
    {
      title: 'Preporuka',
      dataIndex: 'title',
      key: 'title',
      render: (title: string, record: AIRecommendation) => (
        <div>
          <div style={{ fontWeight: 500, marginBottom: '4px' }}>{title}</div>
          <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
        </div>
      ),
    },
    {
      title: 'Prioritet',
      dataIndex: 'priority',
      key: 'priority',
      render: (priority: string) => (
        <Tag color={getPriorityColor(priority)}>
          {priority.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Pouzdanost',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence: number) => (
        <div>
          <div style={{ marginBottom: '4px' }}>
            {getConfidenceBadge(confidence)}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {Math.round(confidence * 100)}%
          </div>
        </div>
      ),
    },
    {
      title: 'Očekivano poboljšanje',
      key: 'improvement',
      render: (record: AIRecommendation) => (
        <div>
          {Object.entries(record.estimated_improvement).map(([key, value]) => (
            <div key={key} style={{ fontSize: '12px', marginBottom: '2px' }}>
              {key.replace('_', ' ')}: {value > 0 ? '+' : ''}{value.toFixed(1)}%
            </div>
          ))}
        </div>
      ),
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: (record: AIRecommendation) => (
        <Space>
          <Tooltip title="Simuliraj">
            <Button
              size="small"
              icon={<EyeOutlined />}
              onClick={() => handleSimulate(record)}
              loading={simulateMutation.isPending}
            />
          </Tooltip>
          
          <Tooltip title="Primijeni">
            <Button
              type="primary"
              size="small"
              icon={<CheckCircleOutlined />}
              onClick={() => handleApply(record.id)}
              loading={applyMutation.isPending}
            />
          </Tooltip>
          
          <Popconfirm
            title="Odbaci preporuku"
            description="Da li ste sigurni da želite da odbacite ovu preporuku?"
            onConfirm={() => handleDismiss(record.id)}
            okText="Da"
            cancelText="Ne"
          >
            <Tooltip title="Odbaci">
              <Button
                size="small"
                danger
                icon={<CloseCircleOutlined />}
                loading={dismissMutation.isPending}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Calculate statistics
  const totalRecommendations = recommendations.length;
  const highPriorityCount = recommendations.filter(r => r.priority === 'high').length;
  const avgConfidence = recommendations.length > 0 
    ? recommendations.reduce((sum, r) => sum + r.confidence, 0) / recommendations.length 
    : 0;
  const avgImpact = recommendations.length > 0
    ? recommendations.reduce((sum, r) => sum + r.impact_score, 0) / recommendations.length
    : 0;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>AI Preporuke</Title>
        <Text type="secondary">Inteligentne preporuke za optimizaciju operacija magacina</Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno preporuka"
              value={totalRecommendations}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Visok prioritet"
              value={highPriorityCount}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Prosečna pouzdanost"
              value={Math.round(avgConfidence * 100)}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Prosečni uticaj"
              value={Math.round(avgImpact)}
              suffix="%"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* AI Confidence Alert */}
      {avgConfidence > 0.8 && (
        <Alert
          message="🤖 AI sistem je visoko pouzdan"
          description={`Prosečna pouzdanost preporuka je ${Math.round(avgConfidence * 100)}%. Preporuke su bazirane na analizi istorijskih podataka i trenutnih metrika.`}
          type="success"
          showIcon
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* Recommendations Table */}
      <Card
        title="Preporuke za optimizaciju"
        extra={
          <Button
            icon={<PlayCircleOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
          >
            Osveži
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={recommendations}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} od ${total} preporuka`
          }}
        />
      </Card>

      {/* Simulation Modal */}
      <Modal
        title="Šta-ako simulacija"
        open={simulationModalVisible}
        onCancel={() => {
          setSimulationModalVisible(false);
          setSimulationData(null);
          setSelectedRecommendation(null);
        }}
        footer={null}
        width={800}
      >
        {simulationData && (
          <div>
            {/* Recommendation Summary */}
            <Card style={{ marginBottom: '16px' }}>
              <Title level={4}>{simulationData.recommendation.title}</Title>
              <Paragraph>{simulationData.recommendation.description}</Paragraph>
              <Space>
                <Tag color={getPriorityColor(simulationData.recommendation.priority)}>
                  {simulationData.recommendation.priority.toUpperCase()}
                </Tag>
                {getConfidenceBadge(simulationData.recommendation.confidence)}
              </Space>
            </Card>

            {/* Before/After Comparison */}
            <Row gutter={16}>
              <Col span={12}>
                <Card title="Pre primjene" size="small">
                  <div style={{ marginBottom: '16px' }}>
                    <Text strong>Opterećenje po radnjama:</Text>
                    {simulationData.before_simulation.store_metrics.map(store => (
                      <div key={store.store_id} style={{ marginTop: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>{store.store_name}</span>
                          <span>{Math.round(store.load_index * 100)}%</span>
                        </div>
                        <Progress 
                          percent={Math.round(store.load_index * 100)} 
                          size="small"
                          status={store.load_index > 0.8 ? 'exception' : 'normal'}
                        />
                      </div>
                    ))}
                  </div>
                  
                  <div>
                    <Text strong>Ukupne metrike:</Text>
                    <div style={{ marginTop: '8px' }}>
                      <div>Prosečna efikasnost: {Math.round(simulationData.before_simulation.overall_metrics.average_efficiency * 100)}%</div>
                      <div>Prosečno neaktivno vreme: {Math.round(simulationData.before_simulation.overall_metrics.average_idle_time * 100)}%</div>
                      <div>Ukupno radnika: {simulationData.before_simulation.overall_metrics.total_workers}</div>
                    </div>
                  </div>
                </Card>
              </Col>
              
              <Col span={12}>
                <Card title="Posle primjene" size="small">
                  <div style={{ marginBottom: '16px' }}>
                    <Text strong>Opterećenje po radnjama:</Text>
                    {simulationData.after_simulation.store_metrics.map(store => (
                      <div key={store.store_id} style={{ marginTop: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span>{store.store_name}</span>
                          <span>{Math.round(store.load_index * 100)}%</span>
                        </div>
                        <Progress 
                          percent={Math.round(store.load_index * 100)} 
                          size="small"
                          status={store.load_index > 0.8 ? 'exception' : 'normal'}
                        />
                      </div>
                    ))}
                  </div>
                  
                  <div>
                    <Text strong>Ukupne metrike:</Text>
                    <div style={{ marginTop: '8px' }}>
                      <div>Prosečna efikasnost: {Math.round(simulationData.after_simulation.overall_metrics.average_efficiency * 100)}%</div>
                      <div>Prosečno neaktivno vreme: {Math.round(simulationData.after_simulation.overall_metrics.average_idle_time * 100)}%</div>
                      <div>Ukupno radnika: {simulationData.after_simulation.overall_metrics.total_workers}</div>
                    </div>
                  </div>
                </Card>
              </Col>
            </Row>

            {/* Improvement Metrics */}
            <Card title="Očekivana poboljšanja" style={{ marginTop: '16px' }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="Balans opterećenja"
                    value={simulationData.improvement_metrics.load_balance_improvement}
                    suffix="%"
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Efikasnost"
                    value={simulationData.improvement_metrics.efficiency_improvement}
                    suffix="%"
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Vreme izvršenja"
                    value={simulationData.improvement_metrics.completion_time_improvement}
                    suffix="%"
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
              </Row>
            </Card>

            {/* Action Buttons */}
            <div style={{ marginTop: '24px', textAlign: 'center' }}>
              <Space>
                <Button
                  type="primary"
                  size="large"
                  icon={<CheckCircleOutlined />}
                  onClick={() => {
                    handleApply(simulationData.recommendation.id);
                    setSimulationModalVisible(false);
                  }}
                  loading={applyMutation.isPending}
                >
                  Primijeni preporuku
                </Button>
                <Button
                  size="large"
                  onClick={() => setSimulationModalVisible(false)}
                >
                  Zatvori
                </Button>
              </Space>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AIRecommendationsPage;
