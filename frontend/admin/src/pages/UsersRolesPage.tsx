/**
 * Users & Roles Page - RBAC Administration
 * Manhattan Active WMS - User management
 * Language: Serbian (Srpski)
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Popconfirm,
  Tooltip,
  Typography
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  PlusOutlined,
  EditOutlined,
  KeyOutlined,
  DeleteOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import api from '../api';
import './UsersRolesPage.css';

const { Title, Text } = Typography;
const { Option } = Select;

interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  team_id?: string;
  team_name?: string;
  magacin_id?: string;
  magacin_naziv?: string;
  is_active: boolean;
}

const roleLabels: Record<string, string> = {
  'admin': 'Administrator',
  'menadzer': 'Menadžer',
  'sef': 'Šef',
  'komercijalista': 'Komercijalista',
  'magacioner': 'Magacioner'
};

const roleColors: Record<string, string> = {
  'admin': 'red',
  'menadzer': 'purple',
  'sef': 'blue',
  'komercijalista': 'cyan',
  'magacioner': 'green'
};

const visibilityTooltips: Record<string, string> = {
  'admin': 'Potpun pristup - vidi sve lokacije i sve zadatke',
  'menadzer': 'Globalni pristup - vidi sve zadatke i izvještaje',
  'sef': 'Pristup po lokaciji - vidi zadatke svog magacina',
  'komercijalista': 'Samo čitanje - vidi sve, ne može mijenjati',
  'magacioner': 'Samo moji i tim - vidi svoje i timske zadatke'
};

export const UsersRolesPage: React.FC = () => {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [form] = Form.useForm();

  // Fetch users
  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const response = await api.get('/users');
      return response.data;
    }
  });

  // Fetch teams
  const { data: teams = [] } = useQuery({
    queryKey: ['teams'],
    queryFn: async () => {
      const response = await api.get('/teams');
      return response.data;
    }
  });

  // Fetch magacini
  const { data: magacini = [] } = useQuery({
    queryKey: ['magacini'],
    queryFn: async () => {
      const response = await api.get('/catalog/magacini');
      return response.data;
    }
  });

  // Create/Update user mutation
  const saveMutation = useMutation({
    mutationFn: async (values: any) => {
      if (editingUser) {
        const response = await api.put(`/users/${editingUser.id}`, values);
        return response.data;
      } else {
        const response = await api.post('/users', values);
        return response.data;
      }
    },
    onSuccess: () => {
      message.success(editingUser ? 'Korisnik ažuriran' : 'Korisnik kreiran');
      setIsModalOpen(false);
      setEditingUser(null);
      form.resetFields();
      queryClient.invalidateQueries({ queryKey: ['users'] });
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'Greška pri čuvanju');
    }
  });

  // Reset password mutation
  const resetPasswordMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await api.post(`/users/${userId}/reset-password`, {
        new_password: 'temp123'  // Temporary password
      });
      return response.data;
    },
    onSuccess: () => {
      message.success('Lozinka resetovana na: temp123');
    }
  });

  // Deactivate user mutation
  const deactivateMutation = useMutation({
    mutationFn: async (userId: string) => {
      const response = await api.delete(`/users/${userId}`);
      return response.data;
    },
    onSuccess: () => {
      message.success('Korisnik deaktiviran');
      queryClient.invalidateQueries({ queryKey: ['users'] });
    }
  });

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setIsModalOpen(true);
  };

  const handleEdit = (user: User) => {
    setEditingUser(user);
    form.setFieldsValue({
      first_name: user.first_name,
      last_name: user.last_name,
      email: user.email,
      role: user.role,
      team_id: user.team_id,
      magacin_id: user.magacin_id,
      is_active: user.is_active
    });
    setIsModalOpen(true);
  };

  const handleSubmit = () => {
    form.validateFields().then((values) => {
      saveMutation.mutate(values);
    });
  };

  const columns: ColumnsType<User> = [
    {
      title: 'Ime i prezime',
      key: 'name',
      render: (_, record) => (
        <Space>
          <Text strong>{record.first_name} {record.last_name}</Text>
        </Space>
      )
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email'
    },
    {
      title: (
        <Space>
          Uloga
          <Tooltip title="Kliknite za politiku vidljivosti">
            <QuestionCircleOutlined />
          </Tooltip>
        </Space>
      ),
      key: 'role',
      render: (_, record) => (
        <Tooltip title={visibilityTooltips[record.role]}>
          <Tag color={roleColors[record.role]}>
            {roleLabels[record.role]}
          </Tag>
        </Tooltip>
      )
    },
    {
      title: 'Tim',
      dataIndex: 'team_name',
      key: 'team',
      render: (team) => team || '-'
    },
    {
      title: 'Magacin',
      dataIndex: 'magacin_naziv',
      key: 'magacin',
      render: (magacin) => magacin || '-'
    },
    {
      title: 'Aktivan',
      key: 'active',
      render: (_, record) => (
        <Tag color={record.is_active ? 'success' : 'default'}>
          {record.is_active ? 'Da' : 'Ne'}
        </Tag>
      )
    },
    {
      title: 'Akcije',
      key: 'actions',
      width: 180,
      render: (_, record) => (
        <Space>
          <Tooltip title="Izmijeni">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="Resetuj lozinku">
            <Button
              type="text"
              icon={<KeyOutlined />}
              onClick={() => resetPasswordMutation.mutate(record.id)}
            />
          </Tooltip>
          <Tooltip title="Deaktiviraj">
            <Popconfirm
              title="Deaktivirati korisnika?"
              description="Korisnik neće moći pristupiti sistemu"
              onConfirm={() => deactivateMutation.mutate(record.id)}
              okText="Da"
              cancelText="Ne"
            >
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      )
    }
  ];

  return (
    <div className="users-roles-page">
      <div className="users-roles-page__header">
        <Title level={2}>Korisnici i uloge</Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size="large"
        >
          Kreiraj korisnika
        </Button>
      </div>

      <Table
        columns={columns}
        dataSource={users}
        loading={isLoading}
        rowKey="id"
        pagination={{ pageSize: 20 }}
      />

      {/* Create/Edit Modal */}
      <Modal
        title={editingUser ? 'Izmijeni korisnika' : 'Kreiraj korisnika'}
        open={isModalOpen}
        onOk={handleSubmit}
        onCancel={() => {
          setIsModalOpen(false);
          setEditingUser(null);
        }}
        okText={editingUser ? 'Sačuvaj' : 'Kreiraj'}
        cancelText="Otkaži"
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="first_name"
            label="Ime"
            rules={[{ required: true, message: 'Obavezno polje' }]}
          >
            <Input size="large" />
          </Form.Item>

          <Form.Item
            name="last_name"
            label="Prezime"
            rules={[{ required: true, message: 'Obavezno polje' }]}
          >
            <Input size="large" />
          </Form.Item>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Obavezno polje' },
              { type: 'email', message: 'Nevalidan email' }
            ]}
          >
            <Input size="large" />
          </Form.Item>

          <Form.Item
            name="role"
            label={
              <Space>
                Uloga
                <Tooltip title="Uloga određuje pristupna prava">
                  <QuestionCircleOutlined />
                </Tooltip>
              </Space>
            }
            rules={[{ required: true, message: 'Obavezno polje' }]}
          >
            <Select size="large" placeholder="Odaberite ulogu">
              <Option value="admin">Administrator</Option>
              <Option value="menadzer">Menadžer</Option>
              <Option value="sef">Šef</Option>
              <Option value="komercijalista">Komercijalista</Option>
              <Option value="magacioner">Magacioner</Option>
            </Select>
          </Form.Item>

          <Form.Item noStyle shouldUpdate={(prev, curr) => prev.role !== curr.role}>
            {({ getFieldValue }) => {
              const role = getFieldValue('role');
              
              if (role === 'magacioner') {
                return (
                  <Form.Item
                    name="team_id"
                    label="Tim"
                    rules={[{ required: true, message: 'Dodijeli tim magacioneru' }]}
                  >
                    <Select size="large" placeholder="Odaberite tim">
                      {teams.map((team: any) => (
                        <Option key={team.id} value={team.id}>
                          {team.name} (Smjena {team.shift})
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                );
              }

              if (role === 'sef') {
                return (
                  <Form.Item
                    name="magacin_id"
                    label="Magacin"
                    rules={[{ required: true, message: 'Dodijeli magacin šefu' }]}
                  >
                    <Select size="large" placeholder="Odaberite magacin">
                      {magacini.map((mag: any) => (
                        <Option key={mag.id} value={mag.id}>
                          {mag.naziv}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                );
              }

              return null;
            }}
          </Form.Item>

          {!editingUser && (
            <Form.Item
              name="password"
              label="Početna lozinka"
              rules={[
                { required: true, message: 'Obavezno polje' },
                { min: 6, message: 'Minimum 6 karaktera' }
              ]}
            >
              <Input.Password size="large" />
            </Form.Item>
          )}

          <Form.Item name="is_active" label="Aktivan" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UsersRolesPage;

