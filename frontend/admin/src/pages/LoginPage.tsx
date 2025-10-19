import React, { useState, useEffect } from 'react';
import { Form, Input, Button, Card, Typography, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined, DashboardOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { login } from '../api';

const { Title, Text } = Typography;

interface LoginPageProps {
  onLoginSuccess?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLoginSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 20,
        y: (e.clientY / window.innerHeight) * 20
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  const onFinish = async (values: { email: string; password: string }) => {
    try {
      setLoading(true);
      setError(null);
      await login(values.email, values.password);
      if (onLoginSuccess) {
        onLoginSuccess();
      } else {
        window.location.reload();
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Neispravni kredencijali. Molimo pokušajte ponovo.');
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
      background: 'linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%)',
      padding: '20px',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Animated Background Circles */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        left: '-10%',
        width: '120%',
        height: '120%',
        background: `radial-gradient(circle at ${50 + mousePosition.x}% ${50 + mousePosition.y}%, rgba(0, 122, 204, 0.1) 0%, transparent 50%)`,
        transition: 'background 0.3s ease',
        pointerEvents: 'none'
      }}/>

      {/* Floating Geometric Shapes */}
      <style>{`
        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(0deg); }
          50% { transform: translateY(-20px) rotate(5deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.05); }
        }
        .floating-shape {
          position: absolute;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.05);
          animation: float 6s ease-in-out infinite;
        }
        .shape-1 {
          width: 200px;
          height: 200px;
          top: 10%;
          right: 15%;
          animation-delay: 0s;
        }
        .shape-2 {
          width: 150px;
          height: 150px;
          bottom: 15%;
          left: 10%;
          animation-delay: 2s;
        }
        .shape-3 {
          width: 100px;
          height: 100px;
          top: 60%;
          right: 25%;
          animation-delay: 4s;
        }
        .login-card {
          animation: fadeInUp 0.6s ease-out;
        }
        @keyframes fadeInUp {
          from {
            opacity: 0;
            transform: translateY(30px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .feature-badge {
          animation: pulse 3s ease-in-out infinite;
        }
      `}</style>

      <div className="floating-shape shape-1" />
      <div className="floating-shape shape-2" />
      <div className="floating-shape shape-3" />

      <Card 
        className="login-card"
        style={{ 
          width: 520, 
          maxWidth: '100%',
          boxShadow: '0 25px 80px rgba(0,0,0,0.5)',
          borderRadius: '20px',
          border: 'none',
          position: 'relative',
          zIndex: 1,
          background: 'rgba(255, 255, 255, 0.98)',
          backdropFilter: 'blur(10px)'
        }}
        bodyStyle={{ padding: '56px 48px' }}
      >
        {/* Logo & Header */}
        <div style={{ textAlign: 'center', marginBottom: 48 }}>
          <div style={{
            width: 120,
            height: 120,
            margin: '0 auto 28px',
            borderRadius: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 15px 40px rgba(0, 122, 204, 0.5)',
            animation: 'pulse 3s ease-in-out infinite',
            overflow: 'hidden',
            background: 'transparent'
          }}>
            <img 
              src="/wms-logo.svg" 
              alt="CunguWMS Logo" 
              style={{ 
                width: '100%', 
                height: '100%', 
                objectFit: 'contain' 
              }} 
            />
          </div>
          
          <Title level={1} style={{ 
            marginBottom: 12, 
            fontWeight: 700, 
            fontSize: 32,
            background: 'linear-gradient(135deg, #007acc 0%, #005a9e 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            WMS
          </Title>
          <Text style={{ 
            fontSize: 16, 
            color: '#666',
            display: 'block',
            marginBottom: 8
          }}>
            Enterprise Warehouse Management
          </Text>
          <Text type="secondary" style={{ fontSize: 14 }}>
            Powered by Pantheon ERP Integration
          </Text>
        </div>

        {error && (
          <Alert
            message="Greška pri prijavi"
            description={error}
            type="error"
            showIcon
            closable
            onClose={() => setError(null)}
            style={{ 
              marginBottom: 28,
              borderRadius: '12px',
              border: 'none',
              boxShadow: '0 4px 12px rgba(255, 77, 79, 0.15)'
            }}
          />
        )}

        <Form
          name="login"
          onFinish={onFinish}
          autoComplete="off"
          size="large"
          layout="vertical"
        >
          <Form.Item
            label={<span style={{ fontWeight: 600, fontSize: 14 }}>Email adresa</span>}
            name="email"
            rules={[
              { required: true, message: 'Molimo unesite email adresu' },
              { type: 'email', message: 'Unesite validnu email adresu' }
            ]}
          >
            <Input
              prefix={<UserOutlined style={{ color: '#007acc' }} />}
              placeholder="vas.email@cungu.com"
              style={{ 
                borderRadius: '12px',
                height: '52px',
                fontSize: '15px',
                border: '2px solid #e8e8e8',
                transition: 'all 0.3s ease'
              }}
              onFocus={(e) => e.target.style.borderColor = '#007acc'}
              onBlur={(e) => e.target.style.borderColor = '#e8e8e8'}
            />
          </Form.Item>

          <Form.Item
            label={<span style={{ fontWeight: 600, fontSize: 14 }}>Lozinka</span>}
            name="password"
            rules={[
              { required: true, message: 'Molimo unesite lozinku' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined style={{ color: '#007acc' }} />}
              placeholder="••••••••••"
              style={{ 
                borderRadius: '12px',
                height: '52px',
                fontSize: '15px',
                border: '2px solid #e8e8e8',
                transition: 'all 0.3s ease'
              }}
              onFocus={(e) => e.target.parentElement!.style.borderColor = '#007acc'}
              onBlur={(e) => e.target.parentElement!.style.borderColor = '#e8e8e8'}
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 24, marginTop: 32 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              block
              size="large"
              style={{ 
                height: '56px',
                borderRadius: '12px',
                fontWeight: 600,
                fontSize: '17px',
                background: loading ? '#999' : 'linear-gradient(135deg, #007acc 0%, #005a9e 100%)',
                border: 'none',
                boxShadow: loading ? 'none' : '0 8px 24px rgba(0, 122, 204, 0.4)',
                transition: 'all 0.3s ease',
                transform: loading ? 'scale(0.98)' : 'scale(1)'
              }}
              onMouseEnter={(e) => {
                if (!loading) {
                  e.currentTarget.style.transform = 'scale(1.02)';
                  e.currentTarget.style.boxShadow = '0 12px 32px rgba(0, 122, 204, 0.5)';
                }
              }}
              onMouseLeave={(e) => {
                if (!loading) {
                  e.currentTarget.style.transform = 'scale(1)';
                  e.currentTarget.style.boxShadow = '0 8px 24px rgba(0, 122, 204, 0.4)';
                }
              }}
            >
              {loading ? (
                <Space>
                  <ThunderboltOutlined spin />
                  Prijavljivanje...
                </Space>
              ) : (
                'Prijavi se u sistem'
              )}
            </Button>
          </Form.Item>
        </Form>

        {/* Footer */}
        <div style={{ 
          textAlign: 'center', 
          marginTop: 40, 
          paddingTop: 28, 
          borderTop: '2px solid #f0f0f0' 
        }}>
          <Text style={{ 
            fontSize: 13, 
            color: '#999',
            display: 'block',
            marginBottom: 8
          }}>
            <strong style={{ color: '#333' }}>Cungu d.o.o.</strong> • Warehouse Management System
          </Text>
          <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 6 }}>
            Version 1.0 • © 2025 All rights reserved
          </Text>
          <Text type="secondary" style={{ fontSize: 11, fontStyle: 'italic' }}>
            Developed by <strong style={{ color: '#007acc' }}>Atdhe Tabaku</strong>
          </Text>
        </div>
      </Card>

      {/* Floating Stats (optional decoration) */}
      <div style={{
        position: 'absolute',
        top: 40,
        right: 40,
        background: 'rgba(255, 255, 255, 0.1)',
        backdropFilter: 'blur(10px)',
        padding: '16px 24px',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        color: '#fff',
        display: 'none' // Show on larger screens
      }}>
        <Text style={{ color: '#fff', fontSize: 12, opacity: 0.9 }}>
          🚀 System Status: <strong>Online</strong>
        </Text>
      </div>
    </div>
  );
};

export default LoginPage;
