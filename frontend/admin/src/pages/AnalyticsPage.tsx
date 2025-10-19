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
  Divider
} from 'antd';
import { 
  Line, 
  Column, 
  Pie 
} from '@ant-design/charts';
import { DownloadOutlined, ReloadOutlined, RobotOutlined, EyeOutlined, WarningOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getDailyStats, getTopWorkers, getManualCompletion, exportCSV, getKPIForecast, ForecastData, getUsers } from '../api';
import AIAssistantModal from '../components/AIAssistantModal';

const { RangePicker } = DatePicker;
const { Option } = Select;

interface Filters {
  radnja?: string;
  period?: string;
  radnik?: string;
  dateRange?: [dayjs.Dayjs, dayjs.Dayjs];
}

const AnalyticsPage: React.FC = () => {
  const [filters, setFilters] = useState<Filters>({
    period: '7d',
    dateRange: [dayjs().subtract(7, 'day'), dayjs()]
  });
  const [aiModalVisible, setAiModalVisible] = useState(false);
  const [showForecast, setShowForecast] = useState(false);

  // Users Query for dropdown
  const { data: usersData } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers
  });

  // KPI Data Queries
  const { data: dailyStats, isLoading: dailyLoading, refetch: refetchDaily } = useQuery({
    queryKey: ['dailyStats', filters],
    queryFn: () => getDailyStats({
      radnja: filters.radnja,
      period: filters.period,
      radnik: filters.radnik
    }),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: topWorkers, isLoading: workersLoading, refetch: refetchWorkers } = useQuery({
    queryKey: ['topWorkers', filters],
    queryFn: () => getTopWorkers({
      radnja: filters.radnja,
      period: filters.period
    }),
    staleTime: 5 * 60 * 1000,
  });

  const { data: manualCompletion, isLoading: manualLoading, refetch: refetchManual } = useQuery({
    queryKey: ['manualCompletion', filters],
    queryFn: () => getManualCompletion({
      radnja: filters.radnja,
      period: filters.period
    }),
    staleTime: 5 * 60 * 1000,
  });

  // Forecast Query
  const { data: forecastData, isLoading: forecastLoading } = useQuery({
    queryKey: ['forecast', filters, showForecast],
    queryFn: () => getKPIForecast({
      metric: 'items_completed',
      period: filters.period === '1d' ? 7 : 
              filters.period === '7d' ? 30 : 
              filters.period === '30d' ? 90 : 90,
      horizon: 7,
      radnja_id: filters.radnja,
      radnik_id: filters.radnik
    }),
    enabled: showForecast,
    staleTime: 10 * 60 * 1000, // 10 minutes cache for forecasts
  });

  const handleFilterChange = (key: keyof Filters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const handleDateRangeChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setFilters(prev => ({ 
        ...prev, 
        dateRange: dates,
        period: undefined // Clear period when custom date range is selected
      }));
    }
  };

  const handleExportCSV = async () => {
    try {
      const blob = await exportCSV({
        radnja: filters.radnja,
        period: filters.period,
        radnik: filters.radnik
      });
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `magacin-report-${dayjs().format('YYYY-MM-DD')}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('CSV izvezen uspešno!');
    } catch (error) {
      message.error('Greška pri izvozu CSV-a');
      console.error('Export error:', error);
    }
  };

  const handleRefresh = () => {
    refetchDaily();
    refetchWorkers();
    refetchManual();
    message.success('Podaci osveženi');
  };

  const handleForecastToggle = () => {
    setShowForecast(!showForecast);
    if (!showForecast) {
      message.info('🔮 Prognoza je uključena - prikazuju se predviđanja za narednih 7 dana');
    }
  };

  // Prepare chart data with forecast
  const prepareChartData = () => {
    const baseData = dailyStats || [];
    
    if (!showForecast || !forecastData) {
      return baseData;
    }
    
    // Combine actual and forecast data
    const combinedData = [
      ...baseData.map(item => ({
        ...item,
        type: 'actual'
      })),
      ...forecastData.forecast.map(item => ({
        date: item.date,
        value: item.value,
        type: 'forecast',
        lower_bound: item.lower_bound,
        upper_bound: item.upper_bound
      }))
    ];
    
    return combinedData;
  };

  // Chart configurations
  const lineConfig = {
    data: prepareChartData(),
    xField: 'date',
    yField: 'value',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
    color: (type: string) => {
      switch (type) {
        case 'actual': return '#1890ff';
        case 'forecast': return '#722ed1';
        default: return '#1890ff';
      }
    },
    legend: {
      position: 'top' as const,
    },
    xAxis: {
      type: 'time',
      tickCount: 5,
    },
    yAxis: {
      label: {
        formatter: (v: number) => `${v}`,
      },
    },
    // Add confidence interval area for forecast
    ...(showForecast && forecastData && {
      area: {
        style: {
          fill: 'l(270) 0:#722ed1 1:#722ed1',
          fillOpacity: 0.1,
        },
      },
    }),
  };

  const columnConfig = {
    data: topWorkers || [],
    xField: 'worker_name',
    yField: 'completed_tasks',
    color: '#1890ff',
    animation: {
      appear: {
        animation: 'scale-in-y',
        duration: 1000,
      },
    },
    xAxis: {
      label: {
        autoRotate: false,
      },
    },
    yAxis: {
      label: {
        formatter: (v: number) => `${v}`,
      },
    },
  };

  const pieConfig = {
    data: manualCompletion || [],
    angleField: 'value',
    colorField: 'type',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name}: {percentage}',
    },
    color: ['#1890ff', '#52c41a'],
    animation: {
      appear: {
        animation: 'scale-in',
        duration: 1000,
      },
    },
  };

  const isLoading = dailyLoading || workersLoading || manualLoading;

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ margin: 0, fontSize: '24px', fontWeight: 600 }}>Analitika</h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Pregled KPI metrika i performansi sistema
        </p>
      </div>

      {/* Filters */}
      <Card style={{ marginBottom: '24px' }}>
        <Row gutter={[16, 16]} align="middle">
          <Col>
            <Space>
              <span>Radnja:</span>
              <Select
                placeholder="Sve radnje"
                style={{ width: 150 }}
                allowClear
                value={filters.radnja}
                onChange={(value) => handleFilterChange('radnja', value)}
              >
                <Option value="pantheon">Pantheon</Option>
                <Option value="maxi">Maxi</Option>
                <Option value="idea">Idea</Option>
              </Select>
            </Space>
          </Col>
          
          <Col>
            <Space>
              <span>Period:</span>
              <Select
                style={{ width: 120 }}
                value={filters.period}
                onChange={(value) => handleFilterChange('period', value)}
              >
                <Option value="1d">1 dan</Option>
                <Option value="7d">7 dana</Option>
                <Option value="30d">30 dana</Option>
                <Option value="90d">90 dana</Option>
              </Select>
            </Space>
          </Col>

          <Col>
            <Space>
              <span>Datum:</span>
              <RangePicker
                value={filters.dateRange}
                onChange={handleDateRangeChange}
                format="DD.MM.YYYY"
              />
            </Space>
          </Col>

          <Col>
            <Space>
              <span>Radnik:</span>
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
              <Button 
                icon={<ReloadOutlined />} 
                onClick={handleRefresh}
                loading={isLoading}
              >
                Osveži
              </Button>
              <Button 
                type="primary" 
                icon={<DownloadOutlined />} 
                onClick={handleExportCSV}
              >
                Izvezi CSV
              </Button>
              <Button 
                type={showForecast ? "primary" : "default"}
                icon={<EyeOutlined />} 
                onClick={handleForecastToggle}
                loading={forecastLoading}
                style={showForecast ? {} : { borderColor: '#722ed1', color: '#722ed1' }}
              >
                🔮 Prikaži prognozu
              </Button>
              <Button 
                type="default"
                icon={<RobotOutlined />} 
                onClick={() => setAiModalVisible(true)}
                style={{ borderColor: '#1890ff', color: '#1890ff' }}
              >
                AI Asistent
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Anomaly Warning */}
      {showForecast && forecastData?.anomaly_detected && (
        <Card style={{ marginBottom: '24px', borderColor: '#ff4d4f' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <WarningOutlined style={{ color: '#ff4d4f', fontSize: '20px' }} />
            <div>
              <div style={{ fontWeight: 500, color: '#ff4d4f' }}>
                ⚠️ Upozorenje: Detektovane anomalije u performansama!
              </div>
              <div style={{ color: '#666', fontSize: '14px' }}>
                Sistem je detektovao {forecastData.anomalies.length} anomalija u poslednjih {forecastData.horizon} dana. 
                Preporučuje se provera operativnih procesa.
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* KPI Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno stavki"
              value={dailyStats?.summary?.total_items || 0}
              valueStyle={{ color: '#1890ff' }}
            />
            {showForecast && forecastData && (
              <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                🔮 Prognoza: {Math.round(forecastData.summary.forecast_avg)} stavki/dan
              </div>
            )}
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Manual %"
              value={dailyStats?.summary?.manual_percentage || 0}
              suffix="%"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Prosječno vrijeme"
              value={dailyStats?.summary?.avg_time_per_task || 0}
              suffix="min"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Aktivni radnici"
              value={topWorkers?.summary?.active_workers || 0}
              valueStyle={{ color: '#722ed1' }}
            />
            {showForecast && forecastData && (
              <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                Trend: {forecastData.summary.trend_direction}
              </div>
            )}
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card 
            title={
              <div>
                Dnevni trend
                {showForecast && forecastData && (
                  <div style={{ fontSize: '12px', color: '#666', fontWeight: 'normal' }}>
                    🔮 Prognoza za narednih {forecastData.horizon} dana (pouzdanost: {Math.round(forecastData.confidence * 100)}%)
                  </div>
                )}
              </div>
            } 
            loading={dailyLoading || forecastLoading}
          >
            <div style={{ height: '300px' }}>
              {dailyStats?.data?.length > 0 ? (
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
        
        <Col xs={24} lg={8}>
          <Card title="Top 5 radnika" loading={workersLoading}>
            <div style={{ height: '300px' }}>
              {topWorkers?.length > 0 ? (
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

      <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
        <Col xs={24} lg={12}>
          <Card title="Ručne potvrde vs Skeniranje" loading={manualLoading}>
            <div style={{ height: '300px' }}>
              {manualCompletion?.length > 0 ? (
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
        
        <Col xs={24} lg={12}>
          <Card title="Detaljni pregled">
            <div style={{ padding: '16px 0' }}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title="Skenirano stavki"
                    value={manualCompletion?.summary?.scanned_items || 0}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Ručno potvrđeno"
                    value={manualCompletion?.summary?.manual_items || 0}
                    valueStyle={{ color: '#faad14' }}
                  />
                </Col>
              </Row>
              
              <Divider />
              
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Statistic
                    title="Ukupno zadataka"
                    value={dailyStats?.summary?.total_tasks || 0}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Završeno zadataka"
                    value={dailyStats?.summary?.completed_tasks || 0}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
              </Row>
            </div>
          </Card>
        </Col>
      </Row>

      {/* AI Assistant Modal */}
      <AIAssistantModal
        visible={aiModalVisible}
        onClose={() => setAiModalVisible(false)}
        filters={{
          radnja: filters.radnja,
          period: filters.period,
          radnik: filters.radnik
        }}
      />
    </div>
  );
};

export default AnalyticsPage;
