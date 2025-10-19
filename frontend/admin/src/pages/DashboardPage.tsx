import React, { useState, useEffect, useCallback } from "react";
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Progress, 
  Button, 
  Space, 
  Typography, 
  Table, 
  Tag, 
  Drawer, 
  Badge, 
  Tooltip,
  Spin,
  Alert,
  Divider
} from "antd";
import { 
  ReloadOutlined, 
  BellOutlined, 
  RobotOutlined, 
  ClockCircleOutlined,
  UserOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  WarningOutlined
} from "@ant-design/icons";
import { Line, Pie } from "@ant-design/plots";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { 
  getTvSnapshot, 
  getDailyStats, 
  getTopWorkers, 
  getManualCompletion,
  getRecentEvents,
  getAISuggestions,
  processAIQuery
} from "../api";

const { Title, Text } = Typography;

// Shift calculation utilities
const SHIFT_1_START = 8; // 08:00
const SHIFT_1_END = 15; // 15:00
const SHIFT_2_START = 12; // 12:00
const SHIFT_2_END = 19; // 19:00

const calculateShiftTime = () => {
  const now = new Date();
  const currentHour = now.getHours();
  const currentMinute = now.getMinutes();
  const currentTimeInMinutes = currentHour * 60 + currentMinute;
  
  // Check if we're in shift 1 (08:00-15:00)
  const shift1Start = SHIFT_1_START * 60;
  const shift1End = SHIFT_1_END * 60;
  
  // Check if we're in shift 2 (12:00-19:00)
  const shift2Start = SHIFT_2_START * 60;
  const shift2End = SHIFT_2_END * 60;
  
  if (currentTimeInMinutes >= shift1Start && currentTimeInMinutes <= shift1End) {
    const remainingMinutes = shift1End - currentTimeInMinutes;
    const hours = Math.floor(remainingMinutes / 60);
    const minutes = remainingMinutes % 60;
    return {
      activeShift: "Shift 1",
      remaining: `${hours}h ${minutes}m`,
      remainingMinutes,
      isActive: true
    };
  } else if (currentTimeInMinutes >= shift2Start && currentTimeInMinutes <= shift2End) {
    const remainingMinutes = shift2End - currentTimeInMinutes;
    const hours = Math.floor(remainingMinutes / 60);
    const minutes = remainingMinutes % 60;
    return {
      activeShift: "Shift 2",
      remaining: `${hours}h ${minutes}m`,
      remainingMinutes,
      isActive: true
    };
  } else {
    return {
      activeShift: null,
      remaining: "Nema aktivne smjene",
      remainingMinutes: 0,
      isActive: false
    };
  }
};

const DashboardPage = () => {
  const [shiftTime, setShiftTime] = useState(calculateShiftTime());
  const [aiDrawerVisible, setAiDrawerVisible] = useState(false);
  const [aiInsights, setAiInsights] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const queryClient = useQueryClient();

  // Update shift time every minute
  useEffect(() => {
    const interval = setInterval(() => {
      setShiftTime(calculateShiftTime());
    }, 60000); // Update every minute
    
    return () => clearInterval(interval);
  }, []);

  // Auto-refresh data every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    }, 60000);
    
    return () => clearInterval(interval);
  }, [queryClient]);

  // Fetch TV snapshot data (contains KPI info)
  const { data: tvSnapshot, isLoading: tvLoading } = useQuery({
    queryKey: ["dashboard", "tv-snapshot"],
    queryFn: getTvSnapshot,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch daily stats
  const { data: dailyStats, isLoading: dailyLoading } = useQuery({
    queryKey: ["dashboard", "daily-stats"],
    queryFn: () => getDailyStats(),
    refetchInterval: 60000,
  });

  // Fetch top workers
  const { data: topWorkers, isLoading: workersLoading } = useQuery({
    queryKey: ["dashboard", "top-workers"],
    queryFn: () => getTopWorkers(),
    refetchInterval: 120000,
  });

  // Fetch manual completion stats
  const { data: manualStats, isLoading: manualLoading } = useQuery({
    queryKey: ["dashboard", "manual-completion"],
    queryFn: () => getManualCompletion(),
    refetchInterval: 120000,
  });

  // Fetch recent events
  const { data: recentEvents, isLoading: eventsLoading } = useQuery({
    queryKey: ["dashboard", "recent-events"],
    queryFn: () => getRecentEvents(20),
    refetchInterval: 30000,
  });

  // Manual refresh function
  const handleRefresh = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ["dashboard"] });
  }, [queryClient]);

  // AI Insights handler
  const handleAIInsights = async () => {
    setAiLoading(true);
    try {
      const response = await processAIQuery({
        query: "Generate today's key insights and recommendations for warehouse operations",
        context: {
          days: 1,
          language: "sr"
        }
      });
      setAiInsights(response);
      setAiDrawerVisible(true);
    } catch (error) {
      console.error("Failed to fetch AI insights:", error);
    } finally {
      setAiLoading(false);
    }
  };

  // Prepare chart data
  const preparePerformanceData = () => {
    // Generate hourly data for the last 8 hours
    const now = new Date();
    const data: Array<{time: string, completed: number, hour: number}> = [];
    
    for (let i = 7; i >= 0; i--) {
      const hour = new Date(now.getTime() - i * 60 * 60 * 1000);
      const hourStr = hour.getHours().toString().padStart(2, '0') + ':00';
      
      // Simulate task completion data (in real implementation, this would come from hourly stats API)
      const completed = Math.floor(Math.random() * 15) + 5;
      
      data.push({
        time: hourStr,
        completed,
        hour: hour.getHours()
      });
    }
    
    return data;
  };

  const prepareWorkloadData = () => {
    if (!topWorkers || !Array.isArray(topWorkers)) return [];
    
    return topWorkers.slice(0, 5).map((worker: any, index: number) => ({
      worker: `${worker.ime} ${worker.prezime}`,
      tasks: worker.completed_zadaci,
      completion_rate: worker.completion_rate,
      color: ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'][index]
    }));
  };

  // Event table columns
  const eventColumns = [
    {
      title: 'Vrijeme',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 100,
      render: (timestamp: string) => {
        const date = new Date(timestamp);
        return date.toLocaleTimeString('sr-RS', { 
          hour: '2-digit', 
          minute: '2-digit' 
        });
      }
    },
    {
      title: 'Tip',
      dataIndex: 'event_type',
      key: 'event_type',
      width: 100,
      render: (type: string) => {
        const typeConfig = {
          'Critical': { color: 'red', icon: <ExclamationCircleOutlined /> },
          'Warning': { color: 'orange', icon: <WarningOutlined /> },
          'Info': { color: 'blue', icon: <CheckCircleOutlined /> },
          'Partial': { color: 'yellow', icon: <WarningOutlined /> }
        };
        const config = typeConfig[type as keyof typeof typeConfig] || { color: 'default', icon: null };
        return (
          <Tag color={config.color} icon={config.icon}>
            {type}
          </Tag>
        );
      }
    },
    {
      title: 'Radnik',
      dataIndex: 'worker_id',
      key: 'worker_id',
      width: 100,
      render: (workerId: string) => workerId ? `#${workerId}` : 'Sistem'
    },
    {
      title: 'Poruka',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true
    }
  ];

  const isLoading = tvLoading || dailyLoading || workersLoading || manualLoading || eventsLoading;

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* Header with refresh and AI button */}
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: '24px' 
      }}>
        <Title level={2} style={{ margin: 0 }}>
          WMS Dashboard
        </Title>
        <Space>
          <Tooltip title="AI Insights">
            <Button 
              type="primary" 
              icon={<RobotOutlined />}
              onClick={handleAIInsights}
              loading={aiLoading}
            >
              AI Summary
            </Button>
          </Tooltip>
          <Tooltip title="Refresh Data">
            <Button 
              icon={<ReloadOutlined />}
              onClick={handleRefresh}
            >
              Refresh
            </Button>
          </Tooltip>
          <Badge count={0} size="small">
            <Button icon={<BellOutlined />} />
          </Badge>
        </Space>
      </div>

      {isLoading && (
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <Spin size="large" />
          <Text style={{ marginLeft: '12px' }}>Loading dashboard data...</Text>
        </div>
      )}

      {/* Top KPI Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno zadataka danas"
              value={tvSnapshot?.kpi?.total_tasks_today || 0}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Završeno (%)"
              value={tvSnapshot?.kpi?.completed_percentage || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
            <Progress 
              percent={tvSnapshot?.kpi?.completed_percentage || 0} 
              size="small" 
              strokeColor="#52c41a"
              style={{ marginTop: '8px' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Aktivni radnici"
              value={tvSnapshot?.kpi?.active_workers || 0}
              prefix={<UserOutlined />}
              valueStyle={{ 
                color: (tvSnapshot?.kpi?.active_workers || 0) > 0 ? '#52c41a' : '#f5222d' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Vrijeme do kraja smjene"
              value={shiftTime.remaining}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ 
                color: shiftTime.isActive ? '#1890ff' : '#8c8c8c' 
              }}
            />
            {shiftTime.activeShift && (
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {shiftTime.activeShift}
              </Text>
            )}
          </Card>
        </Col>
      </Row>

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} lg={16}>
          <Card title="Tasks Completed per Hour" extra={
            <Button 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={() => queryClient.invalidateQueries({ queryKey: ["dashboard", "daily-stats"] })}
            />
          }>
            <Line
              data={preparePerformanceData()}
              xField="time"
              yField="completed"
              height={300}
              smooth
              point={{
                size: 4,
                shape: 'circle',
              }}
              line={{
                size: 3,
              }}
              tooltip={{
                formatter: (datum) => ({
                  name: 'Completed Tasks',
                  value: `${datum.completed} tasks`,
                }),
              }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Warehouse Load Distribution" extra={
            <Button 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={() => queryClient.invalidateQueries({ queryKey: ["dashboard", "top-workers"] })}
            />
          }>
            <Pie
              data={prepareWorkloadData()}
              angleField="tasks"
              colorField="worker"
              radius={0.8}
              height={300}
              label={{
                type: 'outer',
                content: '{name}: {value}',
              }}
              legend={{
                position: 'bottom',
              }}
              tooltip={{
                formatter: (datum) => ({
                  name: datum.worker,
                  value: `${datum.tasks} tasks (${(datum.completion_rate * 100).toFixed(1)}%)`,
                }),
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Events Table */}
      <Card title="Recent Events" extra={
        <Button 
          size="small" 
          icon={<ReloadOutlined />} 
          onClick={() => queryClient.invalidateQueries({ queryKey: ["dashboard", "recent-events"] })}
        >
          Refresh
        </Button>
      }>
        <Table
          columns={eventColumns}
          dataSource={recentEvents?.events || []}
          pagination={{ pageSize: 10 }}
          size="small"
          rowKey="event_id"
          loading={eventsLoading}
        />
      </Card>

      {/* AI Insights Drawer */}
      <Drawer
        title="AI Insights"
        placement="right"
        width={400}
        open={aiDrawerVisible}
        onClose={() => setAiDrawerVisible(false)}
        extra={
          <Button 
            type="primary" 
            icon={<RobotOutlined />}
            onClick={handleAIInsights}
            loading={aiLoading}
          >
            Refresh Insights
          </Button>
        }
      >
        {aiInsights ? (
          <div>
            <Alert
              message="Today's Key Observations"
              type="info"
              style={{ marginBottom: '16px' }}
            />
            <div style={{ marginBottom: '16px' }}>
              <Text strong>Confidence: </Text>
              <Text>{Math.round(aiInsights.confidence * 100)}%</Text>
            </div>
            <Divider />
            <div style={{ whiteSpace: 'pre-wrap' }}>
              {aiInsights.answer}
            </div>
            {aiInsights.data && (
              <>
                <Divider />
                <Text strong>Additional Data:</Text>
                <pre style={{ fontSize: '12px', marginTop: '8px' }}>
                  {JSON.stringify(aiInsights.data, null, 2)}
                </pre>
              </>
            )}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <RobotOutlined style={{ fontSize: '48px', color: '#d9d9d9' }} />
            <div style={{ marginTop: '16px' }}>
              <Text type="secondary">Click "Refresh Insights" to generate AI analysis</Text>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default DashboardPage;