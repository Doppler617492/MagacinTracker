import React, { useState } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import { login } from '../api';

const { Title } = Typography;

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onFinish = async (values: { email: string; password: string }) => {
    try {
      setLoading(true);
      setError(null);
      await login(values.email, values.password);
      // Call success callback if provided
      if (onLoginSuccess) {
        onLoginSuccess();
      } else {
        window.location.reload();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
    }}>
      <Card style={{ width: 400, boxShadow: '0 8px 32px rgba(0,0,0,0.1)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <Title level={2} style={{ color: '#1890ff', marginBottom: 8 }}>
            Magacin Admin
          </Title>
          <Typography.Text type="secondary">
            Prijavite se u admin panel
          </Typography.Text>
        </div>

        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
        >
          <Form.Item
            name="email"
            rules={[
              { required: true, message: 'Molimo unesite email' },
              { type: 'email', message: 'Molimo unesite validan email' }
            ]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="Email"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[
              { required: true, message: 'Molimo unesite lozinku' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="Lozinka"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
            >
              Prijavi se
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', marginTop: 16 }}>
          <Space direction="vertical" size="small">
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Testni korisnici:
            </Typography.Text>
            <Typography.Text code style={{ fontSize: 11 }}>
              it@cungu.com / Dekodera1989
            </Typography.Text>
            <Typography.Text code style={{ fontSize: 11 }}>
              admin@magacin.com / Admin123!
            </Typography.Text>
            <Typography.Text code style={{ fontSize: 11 }}>
              marko.sef@magacin.com / Magacin123!
            </Typography.Text>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default LoginPage;
