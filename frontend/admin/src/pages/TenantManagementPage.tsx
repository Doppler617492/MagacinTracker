import React, { useState } from 'react';
import { Card, Table, Button, Tag, Space, Modal, Form, Input, Select, Row, Col, Statistic, Descriptions, Switch } from 'antd';
import { ShopOutlined, UserOutlined, DatabaseOutlined, PlusOutlined, SettingOutlined, CheckCircleOutlined } from '@ant-design/icons';

const { Option } = Select;

const TenantManagementPage: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const tenants = [
    {
      id: '1',
      name: 'Magacin Beograd',
      subdomain: 'magacin-bg',
      status: 'active',
      plan: 'enterprise',
      users: 45,
      warehouses: 3,
      createdAt: '2024-08-15',
      expiresAt: '2025-08-15'
    },
    {
      id: '2',
      name: 'Distribucija Centar',
      subdomain: 'distribucija-ns',
      status: 'active',
      plan: 'professional',
      users: 28,
      warehouses: 2,
      createdAt: '2024-10-01',
      expiresAt: '2025-10-01'
    },
    {
      id: '3',
      name: 'Demo Skladište',
      subdomain: 'demo',
      status: 'trial',
      plan: 'free_trial',
      users: 5,
      warehouses: 1,
      createdAt: '2025-10-10',
      expiresAt: '2025-10-24'
    }
  ];

  const columns = [
    {
      title: 'Tenant',
      key: 'tenant',
      render: (_: any, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.name}</div>
          <div style={{ fontSize: 12, color: '#888', fontFamily: 'monospace' }}>
            {record.subdomain}.cunguwms.com
          </div>
        </div>
      )
    },
    {
      title: 'Plan',
      dataIndex: 'plan',
      key: 'plan',
      render: (plan: string) => {
        const colors: Record<string, string> = {
          enterprise: 'purple',
          professional: 'blue',
          standard: 'cyan',
          free_trial: 'orange'
        };
        const labels: Record<string, string> = {
          enterprise: 'Enterprise',
          professional: 'Professional',
          standard: 'Standard',
          free_trial: 'Free Trial'
        };
        return <Tag color={colors[plan]}>{labels[plan]}</Tag>;
      }
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : status === 'trial' ? 'orange' : 'red'}>
          {status === 'active' ? 'Aktivan' : status === 'trial' ? 'Probni' : 'Suspendovan'}
        </Tag>
      )
    },
    {
      title: 'Korisnici',
      dataIndex: 'users',
      key: 'users',
      render: (val: number) => <Space><UserOutlined /> {val}</Space>
    },
    {
      title: 'Magacini',
      dataIndex: 'warehouses',
      key: 'warehouses',
      render: (val: number) => <Space><ShopOutlined /> {val}</Space>
    },
    {
      title: 'Kreiran',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: 'Ističe',
      dataIndex: 'expiresAt',
      key: 'expiresAt'
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: () => (
        <Space>
          <Button type="link">Detalji</Button>
          <Button type="link" icon={<SettingOutlined />}>Podešavanja</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>Tenant Management</h1>
          <p style={{ margin: '8px 0 0 0', color: '#666' }}>
            Multi-tenant SaaS administracija
          </p>
        </div>
        <Button type="primary" size="large" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          Novi Tenant
        </Button>
      </div>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno Tenanata"
              value={38}
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Aktivni"
              value={35}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Trial"
              value={3}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupni Korisnici"
              value={1250}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Tenants Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={tenants}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Create Tenant Modal */}
      <Modal
        title="Kreiranje Novog Tenanta"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="companyName"
            label="Naziv Kompanije"
            rules={[{ required: true, message: 'Unesite naziv kompanije' }]}
          >
            <Input placeholder="Magacin Beograd doo" />
          </Form.Item>

          <Form.Item
            name="subdomain"
            label="Subdomain"
            rules={[{ required: true, message: 'Unesite subdomain' }]}
            extra="URL: {subdomain}.cunguwms.com"
          >
            <Input placeholder="magacin-beograd" addonAfter=".cunguwms.com" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="contactEmail"
                label="Admin Email"
                rules={[{ required: true, type: 'email' }]}
              >
                <Input placeholder="admin@example.com" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="contactPhone"
                label="Telefon"
                rules={[{ required: true }]}
              >
                <Input placeholder="+381 11 123 4567" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="plan"
            label="Subscription Plan"
            rules={[{ required: true }]}
            initialValue="free_trial"
          >
            <Select>
              <Option value="free_trial">Free Trial (14 dana)</Option>
              <Option value="standard">Standard ($299/mesec)</Option>
              <Option value="professional">Professional ($599/mesec)</Option>
              <Option value="enterprise">Enterprise ($1,299/mesec)</Option>
            </Select>
          </Form.Item>

          <Form.Item style={{ marginTop: 24 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsModalVisible(false)}>Otkaži</Button>
              <Button type="primary" htmlType="submit">Kreiraj Tenanta (30-60s)</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TenantManagementPage;

