import React, { useState } from 'react';
import { Card, Table, Tag, Space, Button, Progress, Statistic, Row, Col, Typography, Badge, Tooltip, Modal, Form, Input, Select, message, Popconfirm } from 'antd';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { TeamOutlined, ClockCircleOutlined, TrophyOutlined, SyncOutlined, EyeOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import { getTeams, getTeamPerformance, getLiveDashboard, createTeam, updateTeam, deleteTeam, Team, TeamPerformance, LiveDashboard } from '../api';
import client from '../api';

const { Title, Text } = Typography;

const TeamsPage: React.FC = () => {
  const [selectedTeamId, setSelectedTeamId] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTeam, setEditingTeam] = useState<Team | null>(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  // Fetch teams
  const { data: teams, isLoading: teamsLoading, refetch: refetchTeams } = useQuery<Team[]>({
    queryKey: ['teams'],
    queryFn: getTeams,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  // Fetch live dashboard
  const { data: liveDashboard, isLoading: dashboardLoading } = useQuery<LiveDashboard>({
    queryKey: ['live-dashboard'],
    queryFn: () => getLiveDashboard('day'),
    refetchInterval: 15000, // Refresh every 15 seconds
  });

  // Fetch selected team performance
  const { data: teamPerformance } = useQuery<TeamPerformance>({
    queryKey: ['team-performance', selectedTeamId],
    queryFn: () => getTeamPerformance(selectedTeamId!),
    enabled: !!selectedTeamId,
  });

  // Fetch workers for team creation/editing
  const { data: workers } = useQuery({
    queryKey: ['workers'],
    queryFn: async () => {
      const response = await client.get('/admin/users?role_filter=magacioner&active_filter=true&per_page=100');
      return response.data.users;
    },
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: createTeam,
    onSuccess: () => {
      message.success('Tim uspješno kreiran!');
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      setModalOpen(false);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška pri kreiranju tima');
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => updateTeam(id, data),
    onSuccess: () => {
      message.success('Tim uspješno ažuriran!');
      queryClient.invalidateQueries({ queryKey: ['teams'] });
      setModalOpen(false);
      setEditingTeam(null);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška pri ažuriranju tima');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTeam,
    onSuccess: () => {
      message.success('Tim uspješno obrisan!');
      queryClient.invalidateQueries({ queryKey: ['teams'] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška pri brisanju tima');
    },
  });

  const handleOpenModal = (team?: Team) => {
    if (team) {
      setEditingTeam(team);
      form.setFieldsValue({
        name: team.name,
        worker1_id: team.worker1.id,
        worker2_id: team.worker2.id,
        shift: team.shift,
      });
    } else {
      setEditingTeam(null);
      form.resetFields();
    }
    setModalOpen(true);
  };

  const handleSubmit = async (values: any) => {
    if (editingTeam) {
      updateMutation.mutate({ id: editingTeam.id, data: values });
    } else {
      createMutation.mutate(values);
    }
  };

  const handleDelete = (teamId: string) => {
    deleteMutation.mutate(teamId);
  };

  const getShiftColor = (shift: string) => {
    return shift === 'A' ? 'blue' : 'green';
  };

  const getStatusBadge = (shift: string, activeShift: string | null) => {
    if (!activeShift) {
      return <Badge status="default" text="Nije aktivan" />;
    }
    if (shift === activeShift) {
      return <Badge status="processing" text="Radi" />;
    }
    return <Badge status="default" text="Neaktivan" />;
  };

  const formatCountdown = (seconds: number | null) => {
    if (!seconds) return '--:--:--';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const columns = [
    {
      title: 'Tim',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <TeamOutlined />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: 'Članovi',
      key: 'members',
      render: (record: Team) => (
        <Space direction="vertical" size="small">
          <Text>{record.worker1.first_name} {record.worker1.last_name}</Text>
          <Text>{record.worker2.first_name} {record.worker2.last_name}</Text>
        </Space>
      ),
    },
    {
      title: 'Smjena',
      dataIndex: 'shift',
      key: 'shift',
      render: (shift: string) => (
        <Tag color={getShiftColor(shift)}>Smjena {shift}</Tag>
      ),
    },
    {
      title: 'Progres',
      key: 'progress',
      render: (record: Team) => {
        const teamData = liveDashboard?.team_progress.find(t => t.team_id === record.id);
        if (!teamData) return <Progress percent={0} size="small" />;
        
        const percent = Math.round(teamData.completion * 100);
        return (
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            <Progress percent={percent} size="small" />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {teamData.tasks_completed} / {teamData.tasks_total} zadataka
            </Text>
          </Space>
        );
      },
    },
    {
      title: 'Status',
      key: 'status',
      render: (record: Team) => getStatusBadge(record.shift, liveDashboard?.shift_status.active_shift || null),
    },
    {
      title: 'Akcije',
      key: 'actions',
      render: (record: Team) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => setSelectedTeamId(record.id)}
          >
            Performanse
          </Button>
          <Button 
            type="link" 
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            Uredi
          </Button>
          <Popconfirm
            title="Brisanje tima"
            description="Da li ste sigurni da želite obrisati ovaj tim?"
            onConfirm={() => handleDelete(record.id)}
            okText="Da"
            cancelText="Ne"
          >
            <Button 
              type="link" 
              danger
              icon={<DeleteOutlined />}
              loading={deleteMutation.isPending}
            >
              Obriši
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const getShiftStatusInfo = () => {
    if (!liveDashboard) return null;
    
    const activeShift = liveDashboard.shift_status.active_shift;
    const shiftData = activeShift === 'A' 
      ? liveDashboard.shift_status.shift_a 
      : liveDashboard.shift_status.shift_b;
    
    if (!shiftData) return null;

    let statusText = '';
    let statusColor = '';
    let countdown = '';

    switch (shiftData.status) {
      case 'working':
        statusText = 'Radi';
        statusColor = 'success';
        countdown = shiftData.countdown_formatted || '';
        break;
      case 'on_break':
        statusText = 'Pauza';
        statusColor = 'warning';
        countdown = shiftData.countdown_formatted || '';
        break;
      case 'not_started':
        statusText = 'Nije počela';
        statusColor = 'default';
        countdown = shiftData.countdown_formatted || '';
        break;
      case 'ended':
        statusText = 'Završeno';
        statusColor = 'error';
        break;
      default:
        statusText = 'Nepoznato';
        statusColor = 'default';
    }

    return { statusText, statusColor, countdown, activeShift };
  };

  const shiftInfo = getShiftStatusInfo();

  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <TeamOutlined /> Timovi i Smjene
      </Title>

      {/* Shift Status Header */}
      {shiftInfo && (
        <Card 
          style={{ marginBottom: '24px', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          bodyStyle={{ padding: '16px 24px' }}
        >
          <Row gutter={24} align="middle">
            <Col>
              <Space size="large">
                <Statistic
                  title={<span style={{ color: 'white' }}>Aktivna Smjena</span>}
                  value={shiftInfo.activeShift || 'Nema'}
                  valueStyle={{ color: 'white', fontSize: '32px' }}
                  prefix={<ClockCircleOutlined />}
                />
                <Statistic
                  title={<span style={{ color: 'white' }}>Status</span>}
                  value={shiftInfo.statusText}
                  valueStyle={{ color: 'white', fontSize: '24px' }}
                />
                {shiftInfo.countdown && (
                  <Statistic
                    title={<span style={{ color: 'white' }}>Odbrojavanje</span>}
                    value={shiftInfo.countdown}
                    valueStyle={{ color: 'white', fontSize: '24px', fontFamily: 'monospace' }}
                  />
                )}
              </Space>
            </Col>
          </Row>
        </Card>
      )}

      {/* KPI Summary */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Ukupno Zadataka Danas"
              value={liveDashboard?.total_tasks_today || 0}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Završeno"
              value={liveDashboard?.completed_tasks || 0}
              valueStyle={{ color: '#3f8600' }}
              prefix={<TrophyOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Aktivni Timovi"
              value={liveDashboard?.active_teams || 0}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Prosječna Završenost"
              value={
                liveDashboard?.team_progress.length 
                  ? Math.round(
                      liveDashboard.team_progress.reduce((sum, t) => sum + t.completion, 0) / 
                      liveDashboard.team_progress.length * 100
                    )
                  : 0
              }
              suffix="%"
              valueStyle={{ color: '#cf1322' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Teams Table */}
      <Card 
        title="Pregled Timova"
        extra={
          <Space>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={() => handleOpenModal()}
            >
              Dodaj Tim
            </Button>
            <Button icon={<SyncOutlined />} onClick={() => refetchTeams()}>
              Osvježi
            </Button>
          </Space>
        }
      >
        <Table
          dataSource={teams || []}
          columns={columns}
          rowKey="id"
          loading={teamsLoading}
          pagination={false}
        />
      </Card>

      {/* Team Performance Modal - shown when team is selected */}
      {selectedTeamId && teamPerformance && (
        <Card 
          title={`Performanse: ${teamPerformance.team_name}`}
          style={{ marginTop: '24px' }}
          extra={
            <Button onClick={() => setSelectedTeamId(null)}>Zatvori</Button>
          }
        >
          <Row gutter={16}>
            <Col span={8}>
              <Statistic
                title="Ukupno Zadataka"
                value={teamPerformance.total_tasks}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Završeno"
                value={teamPerformance.completed_tasks}
                valueStyle={{ color: '#3f8600' }}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="U Toku"
                value={teamPerformance.in_progress_tasks}
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
          </Row>
          <Row gutter={16} style={{ marginTop: '24px' }}>
            <Col span={8}>
              <Statistic
                title="Stopa Završenosti"
                value={teamPerformance.completion_rate}
                suffix="%"
                precision={2}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Ukupno Skeniranja"
                value={teamPerformance.total_scans}
              />
            </Col>
            <Col span={8}>
              <Statistic
                title="Prosječna Brzina"
                value={teamPerformance.average_speed_per_hour}
                suffix="/ sat"
                precision={2}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Create/Edit Team Modal */}
      <Modal
        title={editingTeam ? 'Uredi Tim' : 'Dodaj Novi Tim'}
        open={modalOpen}
        onCancel={() => {
          setModalOpen(false);
          setEditingTeam(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            label="Naziv Tima"
            name="name"
            rules={[{ required: true, message: 'Unesite naziv tima' }]}
          >
            <Input placeholder="npr. Team A1" />
          </Form.Item>

          <Form.Item
            label="Radnik 1"
            name="worker1_id"
            rules={[{ required: true, message: 'Odaberite prvog radnika' }]}
          >
            <Select
              placeholder="Odaberite radnika"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={workers?.map((w: any) => ({
                label: `${w.first_name} ${w.last_name}`,
                value: w.id,
              }))}
            />
          </Form.Item>

          <Form.Item
            label="Radnik 2"
            name="worker2_id"
            rules={[{ required: true, message: 'Odaberite drugog radnika' }]}
          >
            <Select
              placeholder="Odaberite radnika"
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={workers?.map((w: any) => ({
                label: `${w.first_name} ${w.last_name}`,
                value: w.id,
              }))}
            />
          </Form.Item>

          <Form.Item
            label="Smjena"
            name="shift"
            rules={[{ required: true, message: 'Odaberite smjenu' }]}
          >
            <Select placeholder="Odaberite smjenu">
              <Select.Option value="A">Smjena A (08:00 - 15:00)</Select.Option>
              <Select.Option value="B">Smjena B (12:00 - 19:00)</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={createMutation.isPending || updateMutation.isPending}
              >
                {editingTeam ? 'Ažuriraj' : 'Kreiraj'}
              </Button>
              <Button onClick={() => {
                setModalOpen(false);
                setEditingTeam(null);
                form.resetFields();
              }}>
                Otkaži
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TeamsPage;

