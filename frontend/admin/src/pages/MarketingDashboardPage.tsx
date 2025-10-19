import React from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Progress, Tabs, Space, Button } from 'antd';
import { LineChartOutlined, GlobalOutlined, MailOutlined, RiseOutlined, FileTextOutlined, EyeOutlined } from '@ant-design/icons';
import { Line, Column } from '@ant-design/plots';

const { TabPane } = Tabs;

const MarketingDashboardPage: React.FC = () => {
  const campaigns = [
    {
      id: '1',
      name: 'Google Ads - Serbian Market',
      type: 'ads',
      status: 'active',
      budget: 5000,
      spent: 3200,
      impressions: 45000,
      clicks: 1200,
      conversions: 18,
      ctr: 2.67,
      conversionRate: 1.5
    },
    {
      id: '2',
      name: 'LinkedIn Campaign - 3PL Focus',
      type: 'social',
      status: 'active',
      budget: 3000,
      spent: 1800,
      impressions: 28000,
      clicks: 850,
      conversions: 12,
      ctr: 3.04,
      conversionRate: 1.41
    }
  ];

  const blogPosts = [
    {
      id: '1',
      title: '10 Načina da Optimizujete Skladište sa AI',
      views: 2450,
      aiGenerated: true,
      published: '2025-10-15',
      status: 'published'
    },
    {
      id: '2',
      title: 'RFID Tehnologija: Budućnost Warehouse Managementa',
      views: 1850,
      aiGenerated: true,
      published: '2025-10-10',
      status: 'published'
    }
  ];

  const trafficData = [
    { date: '10-15', visits: 450, signups: 8 },
    { date: '10-16', visits: 520, signups: 12 },
    { date: '10-17', visits: 680, signups: 15 },
    { date: '10-18', visits: 750, signups: 18 },
    { date: '10-19', visits: 820, signups: 22 }
  ];

  const campaignColumns = [
    {
      title: 'Kampanja',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <Tag color={record.type === 'ads' ? 'blue' : 'purple'}>{record.type.toUpperCase()}</Tag>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>
          {status === 'active' ? 'Aktivna' : 'Pauza'}
        </Tag>
      )
    },
    {
      title: 'Budget / Potrošeno',
      key: 'budget',
      render: (_: any, record: any) => (
        <div>
          <Progress percent={Math.round((record.spent / record.budget) * 100)} size="small" />
          <div style={{ fontSize: 12, marginTop: 4 }}>
            ${record.spent.toLocaleString()} / ${record.budget.toLocaleString()}
          </div>
        </div>
      )
    },
    {
      title: 'Impressions',
      dataIndex: 'impressions',
      key: 'impressions',
      render: (val: number) => val.toLocaleString()
    },
    {
      title: 'Clicks',
      dataIndex: 'clicks',
      key: 'clicks',
      render: (val: number) => val.toLocaleString()
    },
    {
      title: 'CTR',
      dataIndex: 'ctr',
      key: 'ctr',
      render: (val: number) => `${val.toFixed(2)}%`
    },
    {
      title: 'Konverzije',
      dataIndex: 'conversions',
      key: 'conversions',
      render: (val: number) => <span style={{ color: '#52c41a', fontWeight: 500 }}>{val}</span>
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: () => (
        <Space>
          <Button type="link">Detalji</Button>
          <Button type="link">Pauziraj</Button>
        </Space>
      )
    }
  ];

  const blogColumns = [
    {
      title: 'Naslov',
      dataIndex: 'title',
      key: 'title',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          {record.aiGenerated && (
            <Tag color="purple" style={{ marginTop: 4 }}>🤖 AI-Generated</Tag>
          )}
        </div>
      )
    },
    {
      title: 'Pregledi',
      dataIndex: 'views',
      key: 'views',
      render: (val: number) => (
        <Space>
          <EyeOutlined />
          {val.toLocaleString()}
        </Space>
      )
    },
    {
      title: 'Datum',
      dataIndex: 'published',
      key: 'published'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'published' ? 'green' : 'orange'}>
          {status === 'published' ? 'Objavljeno' : 'Draft'}
        </Tag>
      )
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: () => (
        <Space>
          <Button type="link">Uredi</Button>
          <Button type="link">Pregled</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>Marketing Dashboard</h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          AI-driven marketing automation i analytics
        </p>
      </div>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Website Traffic"
              value={3220}
              prefix={<GlobalOutlined />}
              valueStyle={{ color: '#1890ff' }}
              suffix="/mesec"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Newsletter Subscribers"
              value={845}
              prefix={<MailOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Blog Članci"
              value={24}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#722ed1' }}
              suffix="objavljeno"
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="SEO Score"
              value={94}
              suffix="/100"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="campaigns">
        <TabPane tab="Marketing Kampanje" key="campaigns">
          <Card>
            <Table
              columns={campaignColumns}
              dataSource={campaigns}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </TabPane>

        <TabPane tab="Blog & Content" key="blog">
          <Card
            extra={
              <Button type="primary" icon={<PlusOutlined />}>
                Generiši AI Blog Post
              </Button>
            }
          >
            <Table
              columns={blogColumns}
              dataSource={blogPosts}
              rowKey="id"
              pagination={false}
            />
          </Card>
        </TabPane>

        <TabPane tab="Website Analytics" key="analytics">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Traffic & Signups Trend">
                <Line
                  data={trafficData.flatMap(d => [
                    { date: d.date, type: 'Posete', value: d.visits },
                    { date: d.date, type: 'Registracije', value: d.signups * 30 }
                  ])}
                  xField="date"
                  yField="value"
                  seriesField="type"
                  height={300}
                  color={['#1890ff', '#52c41a']}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default MarketingDashboardPage;

