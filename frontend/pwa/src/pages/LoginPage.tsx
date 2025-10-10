import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, Alert, Typography, Space } from 'antd';
import { LoginOutlined } from '@ant-design/icons';
import { login } from '../api';

const { Title } = Typography;

const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (values: { email: string; password: string }) => {
    setLoading(true);
    setError('');

    try {
      await login(values.email, values.password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Greška pri prijavljivanju');
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
      <Card style={{ width: 400, boxShadow: '0 10px 40px rgba(0,0,0,0.1)' }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div style={{ textAlign: 'center' }}>
            <Title level={2}>Magacin Worker</Title>
            <Typography.Text type="secondary">Prijavite se na sistem</Typography.Text>
          </div>

          {error && <Alert message={error} type="error" closable onClose={() => setError('')} />}

          <Form onFinish={handleLogin} layout="vertical">
            <Form.Item
              label="Email"
              name="email"
              rules={[{ required: true, message: 'Unesite email' }, { type: 'email', message: 'Nevažeći email' }]}
            >
              <Input size="large" placeholder="email@primer.com" />
            </Form.Item>

            <Form.Item
              label="Lozinka"
              name="password"
              rules={[{ required: true, message: 'Unesite lozinku' }]}
            >
              <Input.Password size="large" placeholder="••••••••" />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                icon={<LoginOutlined />}
                size="large"
                block
              >
                Prijavi se
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  );
};

export default LoginPage;

