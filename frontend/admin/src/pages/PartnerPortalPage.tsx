import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Button, Modal, Form, Input, Select, message, Tabs, Space, Tag } from 'antd';
import { DollarOutlined, TeamOutlined, ShopOutlined, RiseOutlined, PlusOutlined, EyeOutlined } from '@ant-design/icons';
import { Line, Column } from '@ant-design/plots';

const { TabPane } = Tabs;
const { Option } = Select;

interface PartnerMetrics {
  activePartners: number;
  totalTenants: number;
  monthlyRevenue: number;
  totalCommission: number;
}

interface Partner {
  id: string;
  companyName: string;
  contactName: string;
  contactEmail: string;
  status: string;
  region: string;
  tenantCount: number;
  totalRevenue: number;
  commissionEarned: number;
  createdAt: string;
}

const PartnerPortalPage: React.FC = () => {
  const [metrics, setMetrics] = useState<PartnerMetrics>({
    activePartners: 12,
    totalTenants: 48,
    monthlyRevenue: 125000,
    totalCommission: 37500
  });
  
  const [partners, setPartners] = useState<Partner[]>([
    {
      id: '1',
      companyName: 'TechIntegrator doo',
      contactName: 'Marko Petrović',
      contactEmail: 'marko@techintegrator.rs',
      status: 'active',
      region: 'Beograd',
      tenantCount: 8,
      totalRevenue: 28000,
      commissionEarned: 8400,
      createdAt: '2025-01-15'
    },
    {
      id: '2',
      companyName: 'LogistikaPro',
      contactName: 'Ana Jovanović',
      contactEmail: 'ana@logistikapro.rs',
      status: 'active',
      region: 'Novi Sad',
      tenantCount: 12,
      totalRevenue: 42000,
      commissionEarned: 12600,
      createdAt: '2024-11-20'
    }
  ]);

  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const handleCreatePartner = (values: any) => {
    message.success('Partner uspešno kreiran!');
    setIsModalVisible(false);
    form.resetFields();
  };

  const revenueData = [
    { month: 'Jan', revenue: 85000, commission: 25500 },
    { month: 'Feb', revenue: 92000, commission: 27600 },
    { month: 'Mar', revenue: 105000, commission: 31500 },
    { month: 'Apr', revenue: 115000, commission: 34500 },
    { month: 'Maj', revenue: 125000, commission: 37500 }
  ];

  const partnerColumns = [
    {
      title: 'Kompanija',
      dataIndex: 'companyName',
      key: 'companyName',
      render: (text: string, record: Partner) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <div style={{ fontSize: 12, color: '#888' }}>{record.contactEmail}</div>
        </div>
      )
    },
    {
      title: 'Kontakt Osoba',
      dataIndex: 'contactName',
      key: 'contactName'
    },
    {
      title: 'Region',
      dataIndex: 'region',
      key: 'region'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'orange'}>
          {status === 'active' ? 'Aktivan' : 'Pending'}
        </Tag>
      )
    },
    {
      title: 'Tenanti',
      dataIndex: 'tenantCount',
      key: 'tenantCount',
      align: 'center' as const
    },
    {
      title: 'Prihod',
      dataIndex: 'totalRevenue',
      key: 'totalRevenue',
      render: (value: number) => `$${value.toLocaleString()}`
    },
    {
      title: 'Provizija (30%)',
      dataIndex: 'commissionEarned',
      key: 'commissionEarned',
      render: (value: number) => (
        <span style={{ color: '#52c41a', fontWeight: 500 }}>
          ${value.toLocaleString()}
        </span>
      )
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: (_: any, record: Partner) => (
        <Space>
          <Button type="link" icon={<EyeOutlined />}>Detalji</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>Partner Portal</h1>
          <p style={{ margin: '8px 0 0 0', color: '#666' }}>
            Upravljanje partnerima i komisijama
          </p>
        </div>
        <Button type="primary" size="large" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          Novi Partner
        </Button>
      </div>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Aktivni Partneri"
              value={metrics.activePartners}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno Tenanata"
              value={metrics.totalTenants}
              prefix={<ShopOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Mesečni Prihod"
              value={metrics.monthlyRevenue}
              prefix="$"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupna Provizija"
              value={metrics.totalCommission}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="partners">
        <TabPane tab="Partneri" key="partners">
          <Card>
            <Table
              columns={partnerColumns}
              dataSource={partners}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="Prihodi i Provizije" key="revenue">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Mesečni Trend">
                <Line
                  data={revenueData}
                  xField="month"
                  yField="revenue"
                  seriesField="type"
                  height={300}
                  color={['#1890ff', '#52c41a']}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="Performanse" key="performance">
          <Card title="Top Partneri po Prihodu">
            <Column
              data={partners.map(p => ({ name: p.companyName, value: p.totalRevenue }))}
              xField="name"
              yField="value"
              height={300}
              color="#1890ff"
            />
          </Card>
        </TabPane>
      </Tabs>

      {/* Create Partner Modal */}
      <Modal
        title="Novi Partner"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form form={form} layout="vertical" onFinish={handleCreatePartner}>
          <Form.Item
            name="companyName"
            label="Naziv Kompanije"
            rules={[{ required: true, message: 'Unesite naziv kompanije' }]}
          >
            <Input placeholder="TechIntegrator doo" />
          </Form.Item>
          
          <Form.Item
            name="contactName"
            label="Kontakt Osoba"
            rules={[{ required: true, message: 'Unesite ime kontakt osobe' }]}
          >
            <Input placeholder="Marko Petrović" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="contactEmail"
                label="Email"
                rules={[
                  { required: true, message: 'Unesite email' },
                  { type: 'email', message: 'Unesite validan email' }
                ]}
              >
                <Input placeholder="marko@example.com" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="contactPhone"
                label="Telefon"
                rules={[{ required: true, message: 'Unesite telefon' }]}
              >
                <Input placeholder="+381 11 123 4567" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="region"
            label="Region"
            rules={[{ required: true, message: 'Izaberite region' }]}
          >
            <Select placeholder="Izaberite region">
              <Option value="Beograd">Beograd</Option>
              <Option value="Novi Sad">Novi Sad</Option>
              <Option value="Niš">Niš</Option>
              <Option value="Kragujevac">Kragujevac</Option>
              <Option value="Ostalo">Ostalo</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="revenueShare"
            label="Procenat Provizije (%)"
            initialValue={30}
            rules={[{ required: true, message: 'Unesite procenat' }]}
          >
            <Input type="number" min={0} max={100} suffix="%" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, marginTop: 24 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsModalVisible(false)}>
                Otkaži
              </Button>
              <Button type="primary" htmlType="submit">
                Kreiraj Partnera
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PartnerPortalPage;

