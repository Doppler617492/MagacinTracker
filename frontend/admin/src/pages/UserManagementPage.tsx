import React, { useState, useEffect } from 'react';
import { 
  Button, 
  Card, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Table, 
  Space, 
  Tag, 
  message,
  Tooltip,
  Popconfirm,
  Row,
  Col,
  Typography,
  Divider
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  KeyOutlined,
  DownloadOutlined,
  SearchOutlined
} from '@ant-design/icons';
import client from '../api';

const { Title } = Typography;
const { Option } = Select;

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login: string | null;
  created_by: string | null;
}

interface UserCreate {
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  password: string;
  is_active: boolean;
}

interface UserUpdate {
  first_name?: string;
  last_name?: string;
  role?: string;
  is_active?: boolean;
  new_password?: string;
}

const ROLES = [
  { value: 'ADMIN', label: 'Administrator' },
  { value: 'MENADZER', label: 'Menadžer' },
  { value: 'SEF', label: 'Šef' },
  { value: 'KOMERCIJALISTA', label: 'Komercijalista' },
  { value: 'MAGACIONER', label: 'Magacioner' },
];

// Updated: Password change field added to edit form
const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [perPage] = useState(50);
  
  // Filters
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [activeFilter, setActiveFilter] = useState<boolean | null>(null);
  const [search, setSearch] = useState('');
  
  // Modals
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  // Forms
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        page: page.toString(),
        per_page: perPage.toString(),
      });
      
      if (roleFilter) params.append('role_filter', roleFilter);
      if (activeFilter !== null) params.append('active_filter', activeFilter.toString());
      if (search) params.append('search', search);
      
      const response = await client.get(`/admin/users?${params}`);
      setUsers(response.data.users);
      setTotal(response.data.total);
    } catch (error) {
      console.error('Failed to load users:', error);
      message.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (values: UserCreate) => {
    try {
      await client.post('/admin/users', values);
      message.success('User created successfully');
      setCreateModalVisible(false);
      createForm.resetFields();
      loadUsers();
    } catch (error) {
      console.error('Failed to create user:', error);
      message.error('Failed to create user');
    }
  };

  const handleEditUser = async (values: UserUpdate) => {
    if (!selectedUser) return;
    
    try {
      // If password is provided, call reset-password endpoint separately
      if (values.new_password) {
        await client.post(`/admin/users/${selectedUser.id}/reset-password`, {
          new_password: values.new_password
        });
      }
      
      // Update other fields (excluding password)
      const { new_password, ...updateData } = values;
      if (Object.keys(updateData).length > 0) {
        await client.patch(`/admin/users/${selectedUser.id}`, updateData);
      }
      
      message.success('User updated successfully');
      setEditModalVisible(false);
      setSelectedUser(null);
      editForm.resetFields();
      loadUsers();
    } catch (error) {
      console.error('Failed to update user:', error);
      message.error('Failed to update user');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    try {
      await client.delete(`/admin/users/${userId}`);
      message.success('User deactivated successfully');
      loadUsers();
    } catch (error) {
      console.error('Failed to deactivate user:', error);
      message.error('Failed to deactivate user');
    }
  };

  const handleResetPassword = async (userId: string) => {
    try {
      await client.post(`/admin/users/${userId}/reset-password`, {
        new_password: 'TempPassword123!'
      });
      message.success('Password reset successfully');
    } catch (error) {
      console.error('Failed to reset password:', error);
      message.error('Failed to reset password');
    }
  };

  const openEditModal = (user: User) => {
    setSelectedUser(user);
    editForm.setFieldsValue({
      first_name: user.first_name,
      last_name: user.last_name,
      role: user.role,
      is_active: user.is_active,
    });
    setEditModalVisible(true);
  };

  const exportCSV = async () => {
    try {
      const response = await client.get('/admin/users/export', {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'users.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      
      message.success('Users exported successfully');
    } catch (error) {
      console.error('Failed to export users:', error);
      message.error('Failed to export users');
    }
  };

  useEffect(() => {
    loadUsers();
  }, [page, roleFilter, activeFilter, search]);

  const columns = [
    {
      title: 'Name',
      dataIndex: 'full_name',
      key: 'full_name',
      sorter: true,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      sorter: true,
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === 'ADMIN' ? 'red' : role === 'SEF' ? 'blue' : 'green'}>
          {ROLES.find(r => r.value === role)?.label || role}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (lastLogin: string | null) => 
        lastLogin ? new Date(lastLogin).toLocaleString() : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: User) => (
        <Space>
          <Tooltip title="Edit User">
            <Button 
              type="link" 
              icon={<EditOutlined />} 
              onClick={() => openEditModal(record)}
            />
          </Tooltip>
          <Tooltip title="Reset Password">
            <Button 
              type="link" 
              icon={<KeyOutlined />} 
              onClick={() => handleResetPassword(record.id)}
            />
          </Tooltip>
          <Popconfirm
            title="Deactivate User"
            description="Are you sure you want to deactivate this user?"
            onConfirm={() => handleDeleteUser(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Deactivate User">
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
          <Col>
            <Title level={2} style={{ margin: 0 }}>User Management</Title>
          </Col>
          <Col>
            <Space>
              <Button 
                icon={<ReloadOutlined />} 
                onClick={loadUsers}
                loading={loading}
              >
                Refresh
              </Button>
              <Button 
                icon={<DownloadOutlined />} 
                onClick={exportCSV}
              >
                Export CSV
              </Button>
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={() => setCreateModalVisible(true)}
              >
                Add User
              </Button>
            </Space>
          </Col>
        </Row>

        <Divider />

        {/* Filters */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Input
              placeholder="Search users..."
              prefix={<SearchOutlined />}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={4}>
            <Select
              placeholder="Filter by role"
              value={roleFilter}
              onChange={setRoleFilter}
              allowClear
              style={{ width: '100%' }}
            >
              {ROLES.map(role => (
                <Option key={role.value} value={role.value}>
                  {role.label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col span={4}>
            <Select
              placeholder="Filter by status"
              value={activeFilter}
              onChange={setActiveFilter}
              allowClear
              style={{ width: '100%' }}
            >
              <Option value={true}>Active</Option>
              <Option value={false}>Inactive</Option>
            </Select>
          </Col>
        </Row>

        {/* Users Table */}
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            current: page,
            pageSize: perPage,
            total: total,
            onChange: setPage,
            showSizeChanger: false,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} users`,
          }}
        />
      </Card>

      {/* Create User Modal */}
      <Modal
        title="Add New User"
        open={createModalVisible}
        onCancel={() => {
          setCreateModalVisible(false);
          createForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={createForm}
          layout="vertical"
          onFinish={handleCreateUser}
        >
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Please enter email' },
              { type: 'email', message: 'Please enter valid email' }
            ]}
          >
            <Input />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="first_name"
                label="First Name"
                rules={[{ required: true, message: 'Please enter first name' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="last_name"
                label="Last Name"
                rules={[{ required: true, message: 'Please enter last name' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Please select role' }]}
          >
            <Select>
              {ROLES.map(role => (
                <Option key={role.value} value={role.value}>
                  {role.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="password"
            label="Password"
            rules={[
              { required: true, message: 'Please enter password' },
              { min: 8, message: 'Password must be at least 8 characters' }
            ]}
          >
            <Input.Password />
          </Form.Item>
          
          <Form.Item
            name="is_active"
            label="Status"
            valuePropName="checked"
            initialValue={true}
          >
            <Select>
              <Option value={true}>Active</Option>
              <Option value={false}>Inactive</Option>
            </Select>
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Create User
              </Button>
              <Button onClick={() => {
                setCreateModalVisible(false);
                createForm.resetFields();
              }}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* Edit User Modal */}
      <Modal
        title="Edit User"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setSelectedUser(null);
          editForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={editForm}
          layout="vertical"
          onFinish={handleEditUser}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="first_name"
                label="First Name"
                rules={[{ required: true, message: 'Please enter first name' }]}
              >
                <Input />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="last_name"
                label="Last Name"
                rules={[{ required: true, message: 'Please enter last name' }]}
              >
                <Input />
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Please select role' }]}
          >
            <Select>
              {ROLES.map(role => (
                <Option key={role.value} value={role.value}>
                  {role.label}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="is_active"
            label="Status"
          >
            <Select>
              <Option value={true}>Active</Option>
              <Option value={false}>Inactive</Option>
            </Select>
          </Form.Item>
          
          <Divider>Change Password (Optional)</Divider>
          
          <Form.Item
            name="new_password"
            label="New Password"
            help="Leave empty to keep current password"
            rules={[
              { min: 8, message: 'Password must be at least 8 characters' }
            ]}
          >
            <Input.Password placeholder="Enter new password (optional)" />
          </Form.Item>
          
          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Update User
              </Button>
              <Button onClick={() => {
                setEditModalVisible(false);
                setSelectedUser(null);
                editForm.resetFields();
              }}>
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagementPage;