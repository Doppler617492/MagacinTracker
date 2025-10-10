/**
 * NumPad Component - Touch-optimized numeric keypad for quantity entry
 * 
 * Designed for Zebra handheld devices with large touch targets
 * and clear visual feedback.
 */

import React, { useState } from 'react';
import { Modal, Button, Space } from 'antd';
import { DeleteOutlined, CheckOutlined, CloseOutlined } from '@ant-design/icons';
import { theme } from '../theme';

interface NumPadProps {
  visible: boolean;
  title?: string;
  defaultValue?: number;
  maxValue?: number;
  minValue?: number;
  onConfirm: (value: number) => void;
  onCancel: () => void;
}

const NumPad: React.FC<NumPadProps> = ({
  visible,
  title = 'Unesite količinu',
  defaultValue,
  maxValue,
  minValue = 0,
  onConfirm,
  onCancel,
}) => {
  const [value, setValue] = useState(defaultValue?.toString() || '0');

  // Reset value when modal opens
  React.useEffect(() => {
    if (visible) {
      setValue(defaultValue?.toString() || '0');
    }
  }, [visible, defaultValue]);

  const handleNumberClick = (num: string) => {
    setValue(prev => {
      if (prev === '0') return num;
      return prev + num;
    });
  };

  const handleBackspace = () => {
    setValue(prev => {
      if (prev.length === 1) return '0';
      return prev.slice(0, -1);
    });
  };

  const handleClear = () => {
    setValue('0');
  };

  const handleConfirm = () => {
    const numValue = parseFloat(value);
    
    // Validation
    if (isNaN(numValue)) {
      setValue('0');
      return;
    }
    
    if (numValue < minValue) {
      setValue(minValue.toString());
      return;
    }
    
    if (maxValue !== undefined && numValue > maxValue) {
      setValue(maxValue.toString());
      return;
    }
    
    onConfirm(numValue);
  };

  const handleDecimal = () => {
    if (!value.includes('.')) {
      setValue(prev => prev + '.');
    }
  };

  // Number button style
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

  const confirmButtonStyle: React.CSSProperties = {
    ...numberButtonStyle,
    background: theme.colors.success,
    color: '#ffffff',
    fontSize: '20px',
  };

  const cancelButtonStyle: React.CSSProperties = {
    ...numberButtonStyle,
    background: theme.colors.error,
    color: '#ffffff',
    fontSize: '20px',
  };

  return (
    <Modal
      open={visible}
      title={null}
      footer={null}
      onCancel={onCancel}
      width={400}
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
        {/* Title */}
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

        {/* Display */}
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

        {/* Hints */}
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

        {/* Number Grid */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: theme.spacing.sm,
            marginBottom: theme.spacing.md,
          }}
        >
          {['7', '8', '9', '4', '5', '6', '1', '2', '3'].map(num => (
            <button
              key={num}
              onClick={() => handleNumberClick(num)}
              style={numberButtonStyle}
              onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
              onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
              onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
            >
              {num}
            </button>
          ))}

          {/* Bottom row: Clear, 0, Decimal */}
          <button
            onClick={handleClear}
            style={actionButtonStyle}
            onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
            onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            C
          </button>

          <button
            onClick={() => handleNumberClick('0')}
            style={numberButtonStyle}
            onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
            onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            0
          </button>

          <button
            onClick={handleDecimal}
            style={actionButtonStyle}
            onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
            onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            .
          </button>
        </div>

        {/* Action Row: Backspace */}
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
          onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.98)'}
          onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
          onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <DeleteOutlined style={{ fontSize: '20px' }} />
          <span>Obriši</span>
        </button>

        {/* Confirm/Cancel Row */}
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: theme.spacing.md,
          }}
        >
          <button
            onClick={onCancel}
            style={cancelButtonStyle}
            onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
            onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <CloseOutlined style={{ marginRight: theme.spacing.xs }} />
            Otkaži
          </button>

          <button
            onClick={handleConfirm}
            style={confirmButtonStyle}
            onMouseDown={(e) => e.currentTarget.style.transform = 'scale(0.95)'}
            onMouseUp={(e) => e.currentTarget.style.transform = 'scale(1)'}
            onMouseLeave={(e) => e.currentTarget.style.transform = 'scale(1)'}
          >
            <CheckOutlined style={{ marginRight: theme.spacing.xs }} />
            Potvrdi
          </button>
        </div>
      </div>
    </Modal>
  );
};

export default NumPad;

