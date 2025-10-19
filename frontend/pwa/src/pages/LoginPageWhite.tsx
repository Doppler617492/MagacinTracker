/**
 * LoginPage - White Enterprise Theme
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Input, message } from 'antd';
import { User, Lock, LogIn } from 'lucide-react';
import { whiteTheme } from '../theme-white';
import { login } from '../api';
import { useTranslation } from '../hooks/useTranslation';

const LoginPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email || !password) {
      message.error('Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      message.success('Login successful');
      navigate('/');
    } catch (error: any) {
      message.error(error?.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: `linear-gradient(135deg, ${whiteTheme.colors.primary} 0%, ${whiteTheme.colors.accent} 100%)`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: whiteTheme.spacing.xl,
      }}
    >
      <div
        style={{
          background: whiteTheme.colors.cardBackground,
          borderRadius: whiteTheme.borderRadius.xl,
          padding: whiteTheme.spacing['2xl'],
          boxShadow: whiteTheme.shadows.xl,
          width: '100%',
          maxWidth: '400px',
        }}
      >
        {/* Logo/Title */}
        <div style={{ textAlign: 'center', marginBottom: whiteTheme.spacing['2xl'] }}>
          <h1
            style={{
              fontSize: whiteTheme.typography.sizes['3xl'],
              fontWeight: whiteTheme.typography.weights.bold,
              color: whiteTheme.colors.text,
              margin: 0,
              marginBottom: whiteTheme.spacing.xs,
            }}
          >
            Cungu WMS
          </h1>
          <p style={{ fontSize: whiteTheme.typography.sizes.base, color: whiteTheme.colors.textSecondary, margin: 0 }}>
            Worker Portal
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: whiteTheme.spacing.lg }}>
            <label
              style={{
                display: 'block',
                fontSize: whiteTheme.typography.sizes.sm,
                fontWeight: whiteTheme.typography.weights.medium,
                color: whiteTheme.colors.text,
                marginBottom: whiteTheme.spacing.sm,
              }}
            >
              Email
            </label>
            <Input
              size="large"
              placeholder="your.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              prefix={<User size={18} color={whiteTheme.colors.textSecondary} />}
              style={{ height: '48px' }}
            />
          </div>

          <div style={{ marginBottom: whiteTheme.spacing.xl }}>
            <label
              style={{
                display: 'block',
                fontSize: whiteTheme.typography.sizes.sm,
                fontWeight: whiteTheme.typography.weights.medium,
                color: whiteTheme.colors.text,
                marginBottom: whiteTheme.spacing.sm,
              }}
            >
              Password
            </label>
            <Input.Password
              size="large"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              prefix={<Lock size={18} color={whiteTheme.colors.textSecondary} />}
              style={{ height: '48px' }}
            />
          </div>

          <Button
            type="primary"
            size="large"
            block
            htmlType="submit"
            loading={loading}
            icon={<LogIn size={20} />}
            style={{
              height: '56px',
              fontSize: whiteTheme.typography.sizes.md,
              fontWeight: whiteTheme.typography.weights.semibold,
              background: whiteTheme.colors.primary,
            }}
          >
            Login
          </Button>
        </form>

        {/* Footer */}
        <div
          style={{
            marginTop: whiteTheme.spacing.xl,
            textAlign: 'center',
            fontSize: whiteTheme.typography.sizes.xs,
            color: whiteTheme.colors.textMuted,
          }}
        >
          Cungu WMS PWA • Version 1.0.0
          <br />© 2025 Doppler Systems
        </div>
      </div>
    </div>
  );
};

export default LoginPageWhite;

