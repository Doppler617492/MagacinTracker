import React, { useState } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Select, 
  DatePicker, 
  Button, 
  Statistic, 
  Spin,
  message,
  Space,
  Divider,
  Progress,
  Tag
} from 'antd';
import { 
  Line, 
  Column, 
  Pie 
} from '@ant-design/charts';
import { DownloadOutlined, ReloadOutlined, RobotOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getUsers } from '../api';
import AIAssistantModal from '../components/AIAssistantModal';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface Filters {
  radnja?: string;
  period?: string;
  radnik?: string;
  dateRange?: [dayjs.Dayjs, dayjs.Dayjs];
}

const TaskAnalyticsPage: React.FC = () => {
  const [filters, setFilters] = useState<Filters>({
    period: '7d',
    dateRange: [dayjs().subtract(7, 'day'), dayjs()]
  });
  const [aiModalVisible, setAiModalVisible] = useState(false);

  // Users Query for dropdown
  const { data: usersData } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers
  });

  // Task Summary Query
  const { data: taskSummary, isLoading: taskLoading, refetch: refetchTasks, error: taskError } = useQuery({
    queryKey: ['taskSummary', filters],
    queryFn: async () => {
      const response = await fetch('/api/tasks/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      const data = await response.json();
      console.log('📊 Task Summary Response:', data);
      return data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  // Worker Performance Query
  const { data: workerPerformance, isLoading: workersLoading, refetch: refetchWorkers, error: workersError } = useQuery({
    queryKey: ['workerPerformance', filters],
    queryFn: async () => {
      const response = await fetch('/api/tasks/worker-performance', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      const data = await response.json();
      console.log('👷 Worker Performance Response:', data);
      return data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  // Task Trends Query
  const { data: taskTrends, isLoading: trendsLoading, refetch: refetchTrends, error: trendsError } = useQuery({
    queryKey: ['taskTrends', filters],
    queryFn: async () => {
      const response = await fetch('/api/tasks/completion-trends', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });
      const data = await response.json();
      console.log('📈 Task Trends Response:', data);
      return data;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });

  const handleFilterChange = (key: keyof Filters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleRefresh = () => {
    refetchTasks();
    refetchWorkers();
    refetchTrends();
    message.success('Podaci osveženi');
  };

  const handleExportCSV = async () => {
    try {
      message.info('CSV izvoz u pripremi...');
    } catch (error) {
      message.error('Greška pri izvozu CSV-a');
    }
  };

  // Prepare chart data
  const prepareTrendData = () => {
    if (!taskTrends || !Array.isArray(taskTrends)) return [];
    
    return taskTrends.map((trend: any) => ({
      date: trend.date,
      completed: trend.completed_tasks || 0,
      pending: trend.pending_tasks || 0,
      total: trend.total_tasks || 0
    }));
  };

  const prepareWorkerData = () => {
    if (!workerPerformance || !Array.isArray(workerPerformance)) return [];
    
    return workerPerformance.map((worker: any) => ({
      worker_name: worker.full_name,
      completed_tasks: worker.completed_tasks || 0,
      completion_rate: worker.completion_rate || 0
    }));
  };

  const lineConfig = {
    data: prepareTrendData(),
    xField: 'date',
    yField: 'completed',
    point: {
      size: 5,
      shape: 'diamond',
    },
    label: {
      style: {
        fill: '#aaa',
      },
    },
  };

  const columnConfig = {
    data: prepareWorkerData(),
    xField: 'worker_name',
    yField: 'completed_tasks',
    color: '#1890ff',
  };

  const pieConfig = {
    data: [
      { type: 'Završeni zadaci', value: taskSummary?.completed_tasks || 0 },
      { type: 'Zadaci u toku', value: taskSummary?.pending_tasks || 0 },
      { type: 'Nezapočeti zadaci', value: taskSummary?.not_started_tasks || 0 }
    ],
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
  };

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>Analitika zadataka</h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Pregled performansi zadataka i radnika
        </p>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col>
            <Space>
              <span style={{ fontWeight: 500 }}>Period:</span>
              <Select
                value={filters.period}
                onChange={(value) => handleFilterChange('period', value)}
                style={{ width: 120 }}
              >
                <Option value="7d">7 dana</Option>
                <Option value="30d">30 dana</Option>
                <Option value="90d">90 dana</Option>
              </Select>
            </Space>
          </Col>

          <Col>
            <Space>
              <span style={{ fontWeight: 500 }}>Radnik:</span>
              <Select
                placeholder="Svi radnici"
                style={{ width: 150 }}
                allowClear
                value={filters.radnik}
                onChange={(value) => handleFilterChange('radnik', value)}
              >
                <Option value="">Svi radnici</Option>
                {usersData?.users?.filter(user => user.role === 'MAGACIONER').map(user => (
                  <Option key={user.id} value={user.email}>
                    {user.full_name}
                  </Option>
                ))}
              </Select>
            </Space>
          </Col>

          <Col flex="auto" />
          
          <Col>
            <Space>
              <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
                Osveži
              </Button>
              <Button icon={<DownloadOutlined />} onClick={handleExportCSV}>
                Izvezi CSV
              </Button>
              <Button 
                type="primary" 
                icon={<RobotOutlined />} 
                onClick={() => setAiModalVisible(true)}
              >
                AI Asistent
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Ukupno zadataka"
              value={taskSummary?.total_tasks || 0}
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Završeni zadaci"
              value={taskSummary?.completed_tasks || 0}
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="Stopa završetka"
              value={taskSummary?.completion_rate || 0}
              suffix="%"
              prefix={<EyeOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Trend završetka zadataka" loading={trendsLoading}>
            <div style={{ height: '300px' }}>
              {taskTrends?.length > 0 ? (
                <Line {...lineConfig} />
              ) : (
                <div style={{ 
                  height: '100%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  color: '#999'
                }}>
                  Nema podataka za prikaz
                </div>
              )}
            </div>
          </Card>
        </Col>
        
        <Col xs={24} lg={12}>
          <Card title="Status zadataka" loading={taskLoading}>
            <div style={{ height: '300px' }}>
              {taskSummary ? (
                <Pie {...pieConfig} />
              ) : (
                <div style={{ 
                  height: '100%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  color: '#999'
                }}>
                  Nema podataka za prikaz
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24}>
          <Card title="Performanse radnika" loading={workersLoading}>
            <div style={{ height: '300px' }}>
              {workerPerformance?.length > 0 ? (
                <Column {...columnConfig} />
              ) : (
                <div style={{ 
                  height: '100%', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  color: '#999'
                }}>
                  Nema podataka za prikaz
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* AI Assistant Modal */}
      <AIAssistantModal
        visible={aiModalVisible}
        onClose={() => setAiModalVisible(false)}
        context="task-analytics"
      />
    </div>
  );
};

export default TaskAnalyticsPage;
