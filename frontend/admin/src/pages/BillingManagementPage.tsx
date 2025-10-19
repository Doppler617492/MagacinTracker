import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Table, Button, Tag, Tabs, Space, Progress, Descriptions, Badge } from 'antd';
import { DollarOutlined, CreditCardOutlined, FileTextOutlined, RiseOutlined, DownloadOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Column } from '@ant-design/plots';

const { TabPane } = Tabs;

const BillingManagementPage: React.FC = () => {
  const subscriptions = [
    {
      id: '1',
      tenantName: 'Magacin Beograd',
      plan: 'Enterprise',
      status: 'active',
      monthlyPrice: 1299,
      nextBilling: '2025-11-15',
      users: 45,
      maxUsers: 'unlimited'
    },
    {
      id: '2',
      tenantName: 'Distribucija Novi Sad',
      plan: 'Professional',
      status: 'active',
      monthlyPrice: 599,
      nextBilling: '2025-11-10',
      users: 32,
      maxUsers: 50
    },
    {
      id: '3',
      tenantName: 'Skladište Niš',
      plan: 'Standard',
      status: 'trial',
      monthlyPrice: 299,
      nextBilling: '2025-10-25',
      users: 8,
      maxUsers: 10
    }
  ];

  const invoices = [
    { id: 'INV-2025-001', tenant: 'Magacin Beograd', amount: 1299, status: 'paid', date: '2025-10-15' },
    { id: 'INV-2025-002', tenant: 'Distribucija Novi Sad', amount: 599, status: 'paid', date: '2025-10-10' },
    { id: 'INV-2025-003', tenant: 'Skladište Niš', amount: 299, status: 'pending', date: '2025-10-20' }
  ];

  const revenueData = [
    { month: 'Jan', mrr: 15000 },
    { month: 'Feb', mrr: 18500 },
    { month: 'Mar', mrr: 22000 },
    { month: 'Apr', mrr: 28500 },
    { month: 'Maj', mrr: 35000 }
  ];

  const subscriptionColumns = [
    {
      title: 'Tenant',
      dataIndex: 'tenantName',
      key: 'tenantName',
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          <Tag color={record.plan === 'Enterprise' ? 'purple' : record.plan === 'Professional' ? 'blue' : 'green'}>
            {record.plan}
          </Tag>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Badge status={status === 'active' ? 'success' : 'warning'} text={status === 'active' ? 'Aktivan' : 'Probni'} />
      )
    },
    {
      title: 'Mesečna Cena',
      dataIndex: 'monthlyPrice',
      key: 'monthlyPrice',
      render: (price: number) => `$${price}/mesec`
    },
    {
      title: 'Korisnici',
      key: 'users',
      render: (_: any, record: any) => `${record.users} / ${record.maxUsers === 'unlimited' ? '∞' : record.maxUsers}`
    },
    {
      title: 'Sledeća Naplata',
      dataIndex: 'nextBilling',
      key: 'nextBilling'
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: () => (
        <Space>
          <Button type="link">Detalji</Button>
          <Button type="link">Uredi</Button>
        </Space>
      )
    }
  ];

  const invoiceColumns = [
    {
      title: 'Broj Fakture',
      dataIndex: 'id',
      key: 'id',
      render: (text: string) => <span style={{ fontFamily: 'monospace', fontWeight: 500 }}>{text}</span>
    },
    {
      title: 'Tenant',
      dataIndex: 'tenant',
      key: 'tenant'
    },
    {
      title: 'Iznos',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => <span style={{ fontSize: 16, fontWeight: 500 }}>${amount}</span>
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={status === 'paid' ? 'green' : 'orange'} icon={status === 'paid' ? <CheckCircleOutlined /> : undefined}>
          {status === 'paid' ? 'Plaćeno' : 'Na čekanju'}
        </Tag>
      )
    },
    {
      title: 'Datum',
      dataIndex: 'date',
      key: 'date'
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: () => (
        <Space>
          <Button type="link" icon={<DownloadOutlined />}>PDF</Button>
          <Button type="link">Detalji</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>Billing & Pretplate</h1>
        <p style={{ margin: '8px 0 0 0', color: '#666' }}>
          Upravljanje pretplatama i fakturama
        </p>
      </div>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="MRR (Mesečni Prihod)"
              value={35000}
              prefix="$"
              valueStyle={{ color: '#1890ff' }}
              suffix={<RiseOutlined style={{ fontSize: 16 }} />}
            />
            <div style={{ marginTop: 8, fontSize: 12, color: '#52c41a' }}>
              +23% u odnosu na prošli mesec
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="ARR (Godišnji Prihod)"
              value={420000}
              prefix="$"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Aktivne Pretplate"
              value={38}
              prefix={<CreditCardOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupne Fakture"
              value={142}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Tabs defaultActiveKey="subscriptions">
        <TabPane tab="Pretplate" key="subscriptions">
          <Card>
            <Table
              columns={subscriptionColumns}
              dataSource={subscriptions}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="Fakture" key="invoices">
          <Card>
            <Table
              columns={invoiceColumns}
              dataSource={invoices}
              rowKey="id"
              pagination={{ pageSize: 10 }}
            />
          </Card>
        </TabPane>

        <TabPane tab="Revenue Analytics" key="analytics">
          <Row gutter={[16, 16]}>
            <Col span={24}>
              <Card title="Mesečni Recurring Revenue (MRR)">
                <Column
                  data={revenueData}
                  xField="month"
                  yField="mrr"
                  height={300}
                  color="#1890ff"
                  label={{
                    position: 'top',
                    style: { fill: '#000', fontSize: 12 }
                  }}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Distribucija po Planovima">
                <Descriptions column={1}>
                  <Descriptions.Item label="Enterprise (40%)">
                    <Progress percent={40} strokeColor="#722ed1" />
                  </Descriptions.Item>
                  <Descriptions.Item label="Professional (45%)">
                    <Progress percent={45} strokeColor="#1890ff" />
                  </Descriptions.Item>
                  <Descriptions.Item label="Standard (15%)">
                    <Progress percent={15} strokeColor="#52c41a" />
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Finansijski Indikatori">
                <Descriptions column={1} bordered size="small">
                  <Descriptions.Item label="ARPU (Avg Revenue Per User)">$921</Descriptions.Item>
                  <Descriptions.Item label="Churn Rate">2.3%</Descriptions.Item>
                  <Descriptions.Item label="LTV (Lifetime Value)">$15,840</Descriptions.Item>
                  <Descriptions.Item label="CAC (Customer Acq. Cost)">$1,250</Descriptions.Item>
                  <Descriptions.Item label="LTV / CAC Ratio">12.7x</Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>
    </div>
  );
};

export default BillingManagementPage;

