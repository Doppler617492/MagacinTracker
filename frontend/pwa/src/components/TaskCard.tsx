import React from 'react';
import {
  ClockCircleOutlined,
  FileTextOutlined,
  EnvironmentOutlined,
  UserOutlined,
  CheckCircleOutlined,
  PlayCircleOutlined,
  RobotOutlined,
} from '@ant-design/icons';
import { Progress } from 'antd';
import { theme } from '../theme';

interface TaskCardProps {
  documentNumber: string;
  location: string;
  totalItems: number;
  completedItems: number;
  dueTime?: string;
  assignedBy?: string;
  status: 'new' | 'in_progress' | 'completed';
  aiNote?: string;
  estimatedTime?: number; // in minutes
  onClick?: () => void;
}

const TaskCard: React.FC<TaskCardProps> = ({
  documentNumber,
  location,
  totalItems,
  completedItems,
  dueTime,
  assignedBy,
  status,
  aiNote,
  estimatedTime,
  onClick,
}) => {
  const progressPercent = totalItems > 0 ? Math.round((completedItems / totalItems) * 100) : 0;

  const getButtonConfig = () => {
    switch (status) {
      case 'completed':
        return {
          text: 'Završeno',
          color: theme.colors.neutral,
          textColor: theme.colors.textSecondary,
          icon: <CheckCircleOutlined />,
        };
      case 'in_progress':
        return {
          text: 'Nastavi',
          color: theme.colors.success,
          textColor: '#ffffff',
          icon: <PlayCircleOutlined />,
        };
      default:
        return {
          text: 'Otvori zadatak',
          color: theme.colors.primary,
          textColor: '#ffffff',
          icon: <PlayCircleOutlined />,
        };
    }
  };

  const buttonConfig = getButtonConfig();

  return (
    <div
      style={{
        background: theme.colors.cardBackground,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.lg,
        padding: theme.spacing.lg,
        boxShadow: theme.shadows.md,
        display: 'flex',
        flexDirection: 'column',
        gap: theme.spacing.md,
      }}
    >
      {/* Header: Document Number */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: theme.spacing.sm,
          paddingBottom: theme.spacing.sm,
          borderBottom: `1px solid ${theme.colors.border}`,
        }}
      >
        <FileTextOutlined style={{ fontSize: '18px', color: theme.colors.accent }} />
        <span
          style={{
            color: theme.colors.text,
            fontSize: theme.typography.sizes.base,
            fontWeight: theme.typography.weights.semibold,
          }}
        >
          {documentNumber}
        </span>
      </div>

      {/* Task Details Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: '1fr',
          gap: theme.spacing.sm,
        }}
      >
        {/* Location */}
        <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
          <EnvironmentOutlined style={{ fontSize: '14px', color: theme.colors.textSecondary }} />
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Lokacija:
          </span>
          <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 500 }}>
            {location}
          </span>
        </div>

        {/* Items */}
        <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
          <CheckCircleOutlined style={{ fontSize: '14px', color: theme.colors.textSecondary }} />
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Stavke:
          </span>
          <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 500 }}>
            {completedItems} / {totalItems}
          </span>
        </div>

        {/* Due Time */}
        {dueTime && (
          <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <ClockCircleOutlined style={{ fontSize: '14px', color: theme.colors.textSecondary }} />
            <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
              Rok:
            </span>
            <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 500 }}>
              {dueTime}
            </span>
          </div>
        )}

        {/* Assigned By */}
        {assignedBy && (
          <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
            <UserOutlined style={{ fontSize: '14px', color: theme.colors.textSecondary }} />
            <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
              Dodijelio:
            </span>
            <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 500 }}>
              {assignedBy}
            </span>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: theme.spacing.xs,
          }}
        >
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
            Napredak
          </span>
          <span
            style={{
              color: theme.colors.text,
              fontSize: theme.typography.sizes.xs,
              fontWeight: theme.typography.weights.semibold,
            }}
          >
            {progressPercent}%
          </span>
        </div>
        <Progress
          percent={progressPercent}
          strokeColor={theme.colors.accent}
          trailColor={theme.colors.neutral}
          showInfo={false}
          strokeWidth={8}
        />
      </div>

      {/* AI Note (if available) */}
      {aiNote && (
        <div
          style={{
            background: theme.colors.background,
            border: `1px solid ${theme.colors.border}`,
            borderLeft: `3px solid ${theme.colors.accent}`,
            borderRadius: theme.borderRadius.md,
            padding: theme.spacing.md,
            display: 'flex',
            gap: theme.spacing.sm,
            alignItems: 'flex-start',
          }}
        >
          <RobotOutlined style={{ fontSize: '14px', color: theme.colors.accent, marginTop: '2px' }} />
          <div>
            <div
              style={{
                color: theme.colors.accent,
                fontSize: theme.typography.sizes.xs,
                fontWeight: theme.typography.weights.semibold,
                marginBottom: '2px',
              }}
            >
              AI Napomena
            </div>
            <div
              style={{
                color: theme.colors.textSecondary,
                fontSize: theme.typography.sizes.xs,
                lineHeight: '1.4',
              }}
            >
              {aiNote}
              {estimatedTime && ` — Procijenjeno ${estimatedTime} min`}
            </div>
          </div>
        </div>
      )}

      {/* Action Button */}
      <button
        onClick={onClick}
        disabled={status === 'completed'}
        style={{
          background: buttonConfig.color,
          color: buttonConfig.textColor,
          border: 'none',
          borderRadius: theme.borderRadius.md,
          padding: `${theme.spacing.md} ${theme.spacing.lg}`,
          fontSize: theme.typography.sizes.base,
          fontWeight: theme.typography.weights.semibold,
          cursor: status === 'completed' ? 'not-allowed' : 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: theme.spacing.sm,
          transition: 'all 0.2s',
          opacity: status === 'completed' ? 0.6 : 1,
        }}
        onMouseEnter={(e) => {
          if (status !== 'completed') {
            e.currentTarget.style.transform = 'translateY(-1px)';
            e.currentTarget.style.boxShadow = theme.shadows.md;
          }
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = 'none';
        }}
      >
        {buttonConfig.icon}
        {buttonConfig.text}
      </button>
    </div>
  );
};

export default TaskCard;

