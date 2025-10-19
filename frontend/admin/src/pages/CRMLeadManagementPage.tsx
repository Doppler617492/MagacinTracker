import React, { useState } from 'react';
import { Card, Table, Button, Tag, Space, Progress, Statistic, Row, Col, Select, Input, Modal, Form, Steps } from 'antd';
import { UserOutlined, PhoneOutlined, MailOutlined, SearchOutlined, PlusOutlined, RocketOutlined } from '@ant-design/icons';
import { Funnel } from '@ant-design/plots';

const { Option } = Select;
const { Step } = Steps;

const CRMLeadManagementPage: React.FC = () => {
  const [isModalVisible, setIsModalVisible] = useState(false);
  const [form] = Form.useForm();

  const leads = [
    {
      id: '1',
      firstName: 'Nikola',
      lastName: 'Jovanović',
      email: 'nikola@logistika-centar.rs',
      phone: '+381 11 234 5678',
      company: 'Logistika Centar doo',
      status: 'qualified',
      leadScore: 0.85,
      source: 'website',
      createdAt: '2025-10-18'
    },
    {
      id: '2',
      firstName: 'Marija',
      lastName: 'Petrović',
      email: 'marija@distribucija-plus.rs',
      phone: '+381 21 456 7890',
      company: 'Distribucija Plus',
      status: 'demo_scheduled',
      leadScore: 0.92,
      source: 'referral',
      createdAt: '2025-10-15'
    },
    {
      id: '3',
      firstName: 'Stefan',
      lastName: 'Nikolić',
      email: 'stefan@skladiste-ns.rs',
      phone: '+381 21 987 6543',
      company: 'Skladište Novi Sad',
      status: 'trial',
      leadScore: 0.78,
      source: 'partner',
      createdAt: '2025-10-10'
    }
  ];

  const pipelineData = [
    { stage: 'Novi Lead', value: 45, conversion: '100%' },
    { stage: 'Kontaktiran', value: 32, conversion: '71%' },
    { stage: 'Kvalifikovan', value: 24, conversion: '53%' },
    { stage: 'Demo Zakazan', value: 18, conversion: '40%' },
    { stage: 'Trial', value: 12, conversion: '27%' },
    { stage: 'Dobijen', value: 8, conversion: '18%' }
  ];

  const statusMap: Record<string, { text: string; color: string }> = {
    new: { text: 'Novi', color: 'default' },
    contacted: { text: 'Kontaktiran', color: 'blue' },
    qualified: { text: 'Kvalifikovan', color: 'cyan' },
    demo_scheduled: { text: 'Demo Zakazan', color: 'purple' },
    trial: { text: 'Probni Period', color: 'orange' },
    negotiation: { text: 'Pregovori', color: 'gold' },
    closed_won: { text: 'Dobijen', color: 'green' },
    closed_lost: { text: 'Izgubljen', color: 'red' }
  };

  const columns = [
    {
      title: 'Lead',
      key: 'lead',
      render: (_: any, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>{record.firstName} {record.lastName}</div>
          <div style={{ fontSize: 12, color: '#888' }}>{record.company}</div>
        </div>
      )
    },
    {
      title: 'Kontakt',
      key: 'contact',
      render: (_: any, record: any) => (
        <div>
          <div><MailOutlined /> {record.email}</div>
          <div><PhoneOutlined /> {record.phone}</div>
        </div>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={statusMap[status]?.color || 'default'}>
          {statusMap[status]?.text || status}
        </Tag>
      )
    },
    {
      title: 'Lead Score',
      dataIndex: 'leadScore',
      key: 'leadScore',
      render: (score: number) => (
        <div>
          <Progress
            percent={Math.round(score * 100)}
            size="small"
            strokeColor={score > 0.75 ? '#52c41a' : score > 0.5 ? '#faad14' : '#ff4d4f'}
          />
          <span style={{ fontSize: 12, color: '#888' }}>
            {score > 0.75 ? 'Visok prioritet' : score > 0.5 ? 'Srednji' : 'Nizak'}
          </span>
        </div>
      )
    },
    {
      title: 'Izvor',
      dataIndex: 'source',
      key: 'source',
      render: (source: string) => {
        const sourceMap: Record<string, string> = {
          website: 'Website',
          referral: 'Preporuka',
          partner: 'Partner',
          ads: 'Oglasi'
        };
        return sourceMap[source] || source;
      }
    },
    {
      title: 'Datum',
      dataIndex: 'createdAt',
      key: 'createdAt'
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: () => (
        <Space>
          <Button type="link">Detalji</Button>
          <Button type="link">Konvertuj</Button>
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 28, fontWeight: 600 }}>CRM & Lead Management</h1>
          <p style={{ margin: '8px 0 0 0', color: '#666' }}>
            Upravljanje potencijalnim klijentima i sales pipelineom
          </p>
        </div>
        <Button type="primary" size="large" icon={<PlusOutlined />} onClick={() => setIsModalVisible(true)}>
          Novi Lead
        </Button>
      </div>

      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno Leadova"
              value={145}
              prefix={<UserOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Conversion Rate"
              value={18}
              suffix="%"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Sales Cycle"
              value={23}
              suffix="dana"
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Pipeline Value"
              value={450000}
              prefix="$"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Sales Pipeline Funnel */}
      <Card title="Sales Pipeline" style={{ marginBottom: 24 }}>
        <Funnel
          data={pipelineData}
          xField="stage"
          yField="value"
          height={300}
          label={{
            formatter: (datum: any) => `${datum.stage}\n${datum.value} (${datum.conversion})`
          }}
        />
      </Card>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Space size="middle" wrap>
          <Input
            placeholder="Pretraži po imenu ili email-u"
            prefix={<SearchOutlined />}
            style={{ width: 250 }}
          />
          <Select placeholder="Status" style={{ width: 150 }} allowClear>
            {Object.entries(statusMap).map(([key, value]) => (
              <Option key={key} value={key}>{value.text}</Option>
            ))}
          </Select>
          <Select placeholder="Izvor" style={{ width: 150 }} allowClear>
            <Option value="website">Website</Option>
            <Option value="referral">Preporuka</Option>
            <Option value="partner">Partner</Option>
            <Option value="ads">Oglasi</Option>
          </Select>
          <Button type="primary" icon={<SearchOutlined />}>Pretraži</Button>
        </Space>
      </Card>

      {/* Leads Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={leads}
          rowKey="id"
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* Create Lead Modal */}
      <Modal
        title="Novi Lead"
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        footer={null}
        width={700}
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="firstName" label="Ime" rules={[{ required: true }]}>
                <Input placeholder="Nikola" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="lastName" label="Prezime" rules={[{ required: true }]}>
                <Input placeholder="Jovanović" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="company" label="Kompanija" rules={[{ required: true }]}>
            <Input placeholder="Logistika Centar doo" />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
                <Input placeholder="nikola@example.com" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="phone" label="Telefon" rules={[{ required: true }]}>
                <Input placeholder="+381 11 123 4567" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="source" label="Izvor" rules={[{ required: true }]}>
            <Select placeholder="Izaberite izvor">
              <Option value="website">Website</Option>
              <Option value="referral">Preporuka</Option>
              <Option value="partner">Partner</Option>
              <Option value="ads">Oglasi</Option>
            </Select>
          </Form.Item>
          <Form.Item style={{ marginTop: 24 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsModalVisible(false)}>Otkaži</Button>
              <Button type="primary" htmlType="submit">Kreiraj Lead</Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default CRMLeadManagementPage;

