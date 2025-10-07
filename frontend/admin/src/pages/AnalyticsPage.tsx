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
  LineChart, 
  ColumnChart, 
  PieChart 
} from '@ant-design/charts';
import { DownloadOutlined, ReloadOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getDailyStats, getTopWorkers, getManualCompletion, exportCSV } from '../api';

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

  // Chart configurations
  const lineConfig = {
    data: dailyStats?.data || [],
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
    color: ['#1890ff', '#52c41a', '#faad14'],
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
  };

  const columnConfig = {
    data: topWorkers?.data || [],
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
    data: manualCompletion?.data || [],
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
                <Option value="marko.sef@example.com">Marko Šef</Option>
                <Option value="ana.radnik@example.com">Ana Radnik</Option>
                <Option value="petar.worker@example.com">Petar Worker</Option>
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
            </Space>
          </Col>
        </Row>
      </Card>

      {/* KPI Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno stavki"
              value={dailyStats?.summary?.total_items || 0}
              valueStyle={{ color: '#1890ff' }}
            />
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
          </Card>
        </Col>
      </Row>

      {/* Charts */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="Dnevni trend" loading={dailyLoading}>
            <div style={{ height: '300px' }}>
              {dailyStats?.data?.length > 0 ? (
                <LineChart {...lineConfig} />
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
              {topWorkers?.data?.length > 0 ? (
                <ColumnChart {...columnConfig} />
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
              {manualCompletion?.data?.length > 0 ? (
                <PieChart {...pieConfig} />
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
    </div>
  );
};

export default AnalyticsPage;
