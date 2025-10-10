import React, { useState } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  TimePicker,
  InputNumber,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic,
  Divider,
  Typography
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  MailOutlined,
  SlackOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import {
  getReportSchedules,
  createReportSchedule,
  updateReportSchedule,
  deleteReportSchedule,
  runReportNow,
  ReportSchedule,
  ReportScheduleCreate,
  ReportScheduleUpdate
} from '../api';

const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;

const ReportsPage: React.FC = () => {
  const [modalVisible, setModalVisible] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<ReportSchedule | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch report schedules
  const { data: schedules = [], isLoading } = useQuery({
    queryKey: ['report-schedules'],
    queryFn: getReportSchedules,
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createReportSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
      setModalVisible(false);
      form.resetFields();
      message.success('Raspored izvještaja kreiran uspešno!');
    },
    onError: (error: any) => {
      message.error('Greška pri kreiranju rasporeda');
      console.error('Create error:', error);
    }
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: ReportScheduleUpdate }) => 
      updateReportSchedule(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
      setModalVisible(false);
      setEditingSchedule(null);
      form.resetFields();
      message.success('Raspored izvještaja ažuriran uspešno!');
    },
    onError: (error: any) => {
      message.error('Greška pri ažuriranju rasporeda');
      console.error('Update error:', error);
    }
  });

  const deleteMutation = useMutation({
    mutationFn: deleteReportSchedule,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
      message.success('Raspored izvještaja obrisan uspešno!');
    },
    onError: (error: any) => {
      message.error('Greška pri brisanju rasporeda');
      console.error('Delete error:', error);
    }
  });

  const runNowMutation = useMutation({
    mutationFn: runReportNow,
    onSuccess: () => {
      message.success('Izvještaj je poslat odmah!');
    },
    onError: (error: any) => {
      message.error('Greška pri slanju izvještaja');
      console.error('Run now error:', error);
    }
  });

  const handleCreate = () => {
    setEditingSchedule(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (schedule: ReportSchedule) => {
    setEditingSchedule(schedule);
    form.setFieldsValue({
      ...schedule,
      time: dayjs().hour(schedule.time_hour).minute(schedule.time_minute)
    });
    setModalVisible(true);
  };

  const handleDelete = (id: string) => {
    deleteMutation.mutate(id);
  };

  const handleRunNow = (id: string) => {
    runNowMutation.mutate(id);
  };

  const handleToggleEnabled = (schedule: ReportSchedule) => {
    updateMutation.mutate({
      id: schedule.id,
      data: { enabled: !schedule.enabled }
    });
  };

  const handleSubmit = async (values: any) => {
    const { time, ...otherValues } = values;
    
    const scheduleData: ReportScheduleCreate | ReportScheduleUpdate = {
      ...otherValues,
      time_hour: time.hour(),
      time_minute: time.minute()
    };

    if (editingSchedule) {
      updateMutation.mutate({ id: editingSchedule.id, data: scheduleData });
    } else {
      createMutation.mutate(scheduleData as ReportScheduleCreate);
    }
  };

  const getChannelIcon = (channel: string) => {
    switch (channel) {
      case 'email': return <MailOutlined style={{ color: '#1890ff' }} />;
      case 'slack': return <SlackOutlined style={{ color: '#e91e63' }} />;
      case 'both': return <><MailOutlined style={{ color: '#1890ff' }} /> <SlackOutlined style={{ color: '#e91e63' }} /></>;
      default: return null;
    }
  };

  const getFrequencyText = (frequency: string) => {
    switch (frequency) {
      case 'daily': return 'Dnevno';
      case 'weekly': return 'Nedeljno';
      case 'monthly': return 'Mesečno';
      default: return frequency;
    }
  };

  const getStatusTag = (schedule: ReportSchedule) => {
    if (schedule.enabled) {
      return <Tag color="green" icon={<CheckCircleOutlined />}>Aktivan</Tag>;
    } else {
      return <Tag color="red" icon={<PauseCircleOutlined />}>Neaktivan</Tag>;
    }
  };

  const columns = [
    {
      title: 'Naziv',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: ReportSchedule) => (
        <div>
          <div style={{ fontWeight: 500 }}>{text}</div>
          {record.description && (
            <div style={{ fontSize: '12px', color: '#666' }}>{record.description}</div>
          )}
        </div>
      ),
    },
    {
      title: 'Kanal',
      dataIndex: 'channel',
      key: 'channel',
      render: (channel: string) => (
        <Space>
          {getChannelIcon(channel)}
          <span>{channel.toUpperCase()}</span>
        </Space>
      ),
    },
    {
      title: 'Frekvencija',
      dataIndex: 'frequency',
      key: 'frequency',
      render: (frequency: string) => getFrequencyText(frequency),
    },
    {
      title: 'Vreme slanja',
      key: 'time',
      render: (record: ReportSchedule) => (
        <Space>
          <ClockCircleOutlined />
          <span>{record.time_hour.toString().padStart(2, '0')}:{record.time_minute.toString().padStart(2, '0')}</span>
        </Space>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: ReportSchedule) => getStatusTag(record),
    },
    {
      title: 'Statistike',
      key: 'stats',
      render: (record: ReportSchedule) => (
        <div>
          <div>Poslano: {record.total_sent}</div>
          <div style={{ color: record.total_failed > 0 ? '#ff4d4f' : '#52c41a' }}>
            Neuspešno: {record.total_failed}
          </div>
        </div>
      ),
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: (record: ReportSchedule) => (
        <Space>
          <Tooltip title="Pokreni odmah">
            <Button
              type="primary"
              size="small"
              icon={<PlayCircleOutlined />}
              onClick={() => handleRunNow(record.id)}
              loading={runNowMutation.isPending}
            />
          </Tooltip>
          
          <Tooltip title="Uredi">
            <Button
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          
          <Tooltip title={record.enabled ? 'Deaktiviraj' : 'Aktiviraj'}>
            <Button
              size="small"
              icon={record.enabled ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
              onClick={() => handleToggleEnabled(record)}
              loading={updateMutation.isPending}
            />
          </Tooltip>
          
          <Popconfirm
            title="Obriši raspored"
            description="Da li ste sigurni da želite da obrišete ovaj raspored?"
            onConfirm={() => handleDelete(record.id)}
            okText="Da"
            cancelText="Ne"
          >
            <Tooltip title="Obriši">
              <Button
                size="small"
                danger
                icon={<DeleteOutlined />}
                loading={deleteMutation.isPending}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  // Calculate statistics
  const totalSchedules = schedules.length;
  const activeSchedules = schedules.filter(s => s.enabled).length;
  const totalSent = schedules.reduce((sum, s) => sum + s.total_sent, 0);
  const totalFailed = schedules.reduce((sum, s) => sum + s.total_failed, 0);

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>Automatski Izvještaji</Title>
        <Text type="secondary">Upravljanje rasporedima za automatsko slanje KPI izvještaja</Text>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno rasporeda"
              value={totalSchedules}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Aktivni rasporedi"
              value={activeSchedules}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Ukupno poslano"
              value={totalSent}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Neuspešno"
              value={totalFailed}
              valueStyle={{ color: totalFailed > 0 ? '#ff4d4f' : '#52c41a' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Reports Table */}
      <Card
        title="Rasporedi Izvještaja"
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Novi Raspored
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={schedules}
          rowKey="id"
          loading={isLoading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} od ${total} rasporeda`
          }}
        />
      </Card>

      {/* Create/Edit Modal */}
      <Modal
        title={editingSchedule ? 'Uredi Raspored' : 'Novi Raspored'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingSchedule(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            channel: 'email',
            frequency: 'daily',
            enabled: true,
            time_hour: 7,
            time_minute: 0,
            recipients: [],
            filters: {}
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="name"
                label="Naziv"
                rules={[{ required: true, message: 'Molimo unesite naziv' }]}
              >
                <Input placeholder="Naziv rasporeda" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="channel"
                label="Kanal"
                rules={[{ required: true, message: 'Molimo odaberite kanal' }]}
              >
                <Select placeholder="Odaberite kanal">
                  <Option value="email">Email</Option>
                  <Option value="slack">Slack</Option>
                  <Option value="both">Email + Slack</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="description"
            label="Opis"
          >
            <TextArea rows={2} placeholder="Opis rasporeda (opciono)" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="frequency"
                label="Frekvencija"
                rules={[{ required: true, message: 'Molimo odaberite frekvenciju' }]}
              >
                <Select placeholder="Odaberite frekvenciju">
                  <Option value="daily">Dnevno</Option>
                  <Option value="weekly">Nedeljno</Option>
                  <Option value="monthly">Mesečno</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="time"
                label="Vreme slanja"
                rules={[{ required: true, message: 'Molimo odaberite vreme' }]}
              >
                <TimePicker
                  format="HH:mm"
                  style={{ width: '100%' }}
                  placeholder="Odaberite vreme"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="recipients"
            label="Primaoci"
            rules={[{ required: true, message: 'Molimo unesite primaoce' }]}
          >
            <Select
              mode="tags"
              placeholder="Unesite email adrese ili Slack kanale"
              style={{ width: '100%' }}
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="filters.radnja"
                label="Radnja"
              >
                <Select placeholder="Sve radnje" allowClear>
                  <Option value="pantheon">Pantheon</Option>
                  <Option value="maxi">Maxi</Option>
                  <Option value="idea">Idea</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="filters.period"
                label="Period"
              >
                <Select placeholder="7 dana" allowClear>
                  <Option value="1d">1 dan</Option>
                  <Option value="7d">7 dana</Option>
                  <Option value="30d">30 dana</Option>
                  <Option value="90d">90 dana</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="enabled"
            label="Status"
            valuePropName="checked"
          >
            <Switch checkedChildren="Aktivan" unCheckedChildren="Neaktivan" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingSchedule ? 'Ažuriraj' : 'Kreiraj'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                Otkaži
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default ReportsPage;
