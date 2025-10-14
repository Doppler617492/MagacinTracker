/**
 * NumPad Component - Touch-optimized numeric keypad for quantity entry
 *
 * Designed for Zebra handheld devices with large touch targets
 * and clear visual feedback.
 */

import React, { useEffect, useState } from 'react';
import { Modal, Button, Space } from 'antd';
import { DeleteOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { theme } from '../theme';

interface NumPadProps {
  visible: boolean;
  title?: string;
  defaultValue?: number;
  maxValue?: number;
  minValue?: number;
  allowDecimal?: boolean;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmLoading?: boolean;
  extraContent?: React.ReactNode;
  onConfirm: (value: number) => void;
  onCancel: () => void;
  onValueChange?: (value: number) => void;
}

const NumPad: React.FC<NumPadProps> = ({
  visible,
  title = 'Unesite količinu',
  defaultValue,
  maxValue,
  minValue = 0,
  allowDecimal = false,
  confirmLabel = 'Sačuvaj',
  cancelLabel = 'Odustani',
  confirmLoading = false,
  extraContent,
  onConfirm,
  onCancel,
  onValueChange,
}) => {
  const [value, setValue] = useState<string>(defaultValue?.toString() ?? '0');

  const emitValueChange = (next: string) => {
    setValue(next);
    if (onValueChange) {
      const parsed = parseFloat(next);
      onValueChange(Number.isNaN(parsed) ? 0 : parsed);
    }
  };

  useEffect(() => {
    if (visible) {
      const seed = defaultValue !== undefined ? defaultValue.toString() : '0';
      emitValueChange(seed);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible, defaultValue]);

  const handleNumberClick = (digit: string) => {
    const next = value === '0' ? digit : `${value}${digit}`;
    emitValueChange(next);
  };

  const handleBackspace = () => {
    if (value.length <= 1) {
      emitValueChange('0');
      return;
    }
    emitValueChange(value.slice(0, -1));
  };

  const handleClear = () => {
    emitValueChange('0');
  };

  const handleDecimal = () => {
    if (!allowDecimal || value.includes('.')) {
      return;
    }
    emitValueChange(`${value}.`);
  };

  const handleConfirm = () => {
    const numeric = parseFloat(value);

    if (Number.isNaN(numeric)) {
      emitValueChange('0');
      return;
    }

    if (numeric < minValue) {
      emitValueChange(minValue.toString());
      return;
    }

    if (maxValue !== undefined && numeric > maxValue) {
      emitValueChange(maxValue.toString());
      return;
    }

    onConfirm(numeric);
  };

  const numberButtonStyle: React.CSSProperties = {
    width: '100%',
    height: '70px',
    fontSize: '24px',
    fontWeight: 600,
    background: theme.colors.cardBackground,
    color: theme.colors.text,
    border: `2px solid ${theme.colors.border}`,
    borderRadius: theme.borderRadius.md,
    cursor: 'pointer',
    transition: 'all 0.2s ease',
    touchAction: 'manipulation',
  };

  const actionButtonStyle: React.CSSProperties = {
    ...numberButtonStyle,
    background: theme.colors.neutral,
    color: theme.colors.text,
  };

  return (
    <Modal
      open={visible}
      title={null}
      footer={null}
      onCancel={onCancel}
      width={420}
      style={{ maxWidth: '95vw' }}
      styles={{
        body: {
          background: theme.colors.background,
          padding: theme.spacing.lg,
        },
      }}
      closeIcon={<CloseOutlined style={{ color: theme.colors.text }} />}
    >
      <div>
        <div
          style={{
            color: theme.colors.text,
            fontSize: theme.typography.sizes.lg,
            fontWeight: theme.typography.weights.semibold,
            marginBottom: theme.spacing.md,
            textAlign: 'center',
          }}
        >
          {title}
        </div>

        <div
          style={{
            background: theme.colors.cardBackground,
            border: `2px solid ${theme.colors.primary}`,
            borderRadius: theme.borderRadius.md,
            padding: theme.spacing.lg,
            marginBottom: theme.spacing.lg,
            textAlign: 'right',
            minHeight: '80px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
          }}
        >
          <div
            style={{
              fontSize: '48px',
              fontWeight: 700,
              color: theme.colors.text,
              fontFamily: 'monospace',
            }}
          >
            {value}
          </div>
        </div>

        {maxValue !== undefined && (
          <div
            style={{
              color: theme.colors.textSecondary,
              fontSize: theme.typography.sizes.sm,
              marginBottom: theme.spacing.md,
              textAlign: 'center',
            }}
          >
            Maksimum: {maxValue}
          </div>
        )}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: theme.spacing.sm,
            marginBottom: theme.spacing.md,
          }}
        >
          {['7', '8', '9', '4', '5', '6', '1', '2', '3'].map((num) => (
            <button
              key={num}
              onClick={() => handleNumberClick(num)}
              style={numberButtonStyle}
              onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.95)')}
              onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
              onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
            >
              {num}
            </button>
          ))}

          <button
            onClick={handleClear}
            style={actionButtonStyle}
            onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.95)')}
            onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          >
            C
          </button>

          <button
            onClick={() => handleNumberClick('0')}
            style={numberButtonStyle}
            onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.95)')}
            onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          >
            0
          </button>

          <button
            onClick={handleDecimal}
            style={actionButtonStyle}
            onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.95)')}
            onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
            onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          >
            .
          </button>
        </div>

        <button
          onClick={handleBackspace}
          style={{
            ...actionButtonStyle,
            width: '100%',
            marginBottom: theme.spacing.md,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: theme.spacing.sm,
          }}
          onMouseDown={(e) => (e.currentTarget.style.transform = 'scale(0.98)')}
          onMouseUp={(e) => (e.currentTarget.style.transform = 'scale(1)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'scale(1)')}
        >
          <DeleteOutlined style={{ fontSize: '20px' }} />
          <span>Obriši</span>
        </button>

        {extraContent && (
          <div style={{ marginBottom: theme.spacing.md }}>{extraContent}</div>
        )}

        <Space size={theme.spacing.md} style={{ width: '100%' }}>
          <Button
            block
            size="large"
            onClick={onCancel}
            style={{
              height: '70px',
              background: theme.colors.error,
              color: '#ffffff',
              border: 'none',
              fontWeight: 600,
            }}
            icon={<CloseOutlined />}
          >
            {cancelLabel}
          </Button>

          <Button
            type="primary"
            block
            size="large"
            onClick={handleConfirm}
            loading={confirmLoading}
            style={{
              height: '70px',
              background: theme.colors.success,
              border: 'none',
              fontWeight: 600,
            }}
            icon={<CheckOutlined />}
          >
            {confirmLabel}
          </Button>
        </Space>
      </div>
    </Modal>
  );
};

export default NumPad;
