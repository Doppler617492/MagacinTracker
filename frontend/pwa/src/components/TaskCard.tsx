import React from 'react';
import {
  ClockCircleOutlined,
  FileTextOutlined,
  EnvironmentOutlined,
  UserOutlined,
  WarningOutlined,
  RobotOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { Progress, Tag } from 'antd';
import { theme } from '../theme';

interface TaskCardProps {
  documentNumber: string;
  location: string;
  totalItems: number;
  completedItems: number;
  partialItems?: number; // Items closed with shortage
  shortageQty?: number;
  dueTime?: string;
  assignedBy?: string;
  status: 'new' | 'in_progress' | 'completed';
  progress?: number;
  aiNote?: string;
  estimatedTime?: number; // in minutes
  onClick?: () => void;
}

const TaskCard: React.FC<TaskCardProps> = ({
  documentNumber,
  location,
  totalItems,
  completedItems,
  partialItems = 0,
  shortageQty = 0,
  dueTime,
  assignedBy,
  status,
  progress,
  aiNote,
  estimatedTime,
  onClick,
}) => {
  const computedProgress =
    typeof progress === 'number'
      ? Math.round(progress)
      : totalItems > 0
        ? Math.round((completedItems / totalItems) * 100)
        : 0;

  const hasPartial = partialItems > 0;
  const shortageDisplay = shortageQty > 0 ? `${Math.round(shortageQty)} kom` : '-';

  const statusMeta: Record<
    TaskCardProps['status'],
    { label: string; color: string; background: string }
  > = {
    new: {
      label: 'Novo',
      color: '#3B82F6',
      background: 'rgba(59, 130, 246, 0.12)',
    },
    in_progress: {
      label: 'U toku',
      color: theme.colors.accent,
      background: 'rgba(0, 200, 150, 0.12)',
    },
    completed: {
      label: 'Završeno',
      color: theme.colors.success,
      background: 'rgba(0, 200, 150, 0.12)',
    },
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (!onClick) return;
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onClick();
    }
  };

  return (
    <div
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : -1}
      onClick={onClick}
      onKeyDown={handleKeyDown}
      style={{
        background: theme.colors.cardBackground,
        border: `1px solid ${theme.colors.border}`,
        borderRadius: theme.borderRadius.xl,
        padding: theme.spacing.lg,
        boxShadow: theme.shadows.lg,
        display: 'flex',
        gap: theme.spacing.lg,
        cursor: onClick ? 'pointer' : 'default',
        transition: 'transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-2px)';
        e.currentTarget.style.boxShadow = '0 10px 25px rgba(0,0,0,0.35)';
        e.currentTarget.style.borderColor = theme.colors.accent;
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)';
        e.currentTarget.style.boxShadow = theme.shadows.lg;
        e.currentTarget.style.borderColor = theme.colors.border;
      }}
    >
      <div
        style={{
          width: '96px',
          minWidth: '96px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: theme.spacing.md,
        }}
      >
        <Tag
          color={statusMeta[status].background}
          style={{
            color: statusMeta[status].color,
            borderColor: 'transparent',
            fontWeight: theme.typography.weights.semibold,
            fontSize: theme.typography.sizes.xs,
            padding: `${parseInt(theme.spacing.xs, 10) / 2}px ${parseInt(theme.spacing.sm, 10)}px`,
            borderRadius: theme.borderRadius.md,
          }}
        >
          {statusMeta[status].label}
        </Tag>
        <Progress
          type="circle"
          percent={Math.min(computedProgress, 100)}
          width={70}
          strokeColor={hasPartial ? theme.colors.warning : theme.colors.accent}
          trailColor={theme.colors.neutral}
          format={(percent) => `${percent}%`}
        />
        {hasPartial && (
          <div
            style={{
              fontSize: theme.typography.sizes.xs,
              fontWeight: theme.typography.weights.medium,
              color: theme.colors.warning,
              textTransform: 'uppercase',
            }}
          >
            {partialItems} djel.
          </div>
        )}
      </div>

      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: theme.spacing.md }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: theme.spacing.md }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.xs }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: theme.spacing.sm,
                color: theme.colors.text,
                fontSize: theme.typography.sizes.lg,
                fontWeight: theme.typography.weights.semibold,
                letterSpacing: '0.4px',
              }}
            >
              <FileTextOutlined style={{ color: theme.colors.accent }} />
              {documentNumber}
            </div>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: theme.spacing.sm,
                color: theme.colors.textSecondary,
                fontSize: theme.typography.sizes.sm,
              }}
            >
              <EnvironmentOutlined />
              <span style={{ color: theme.colors.text }}>{location}</span>
            </div>
            {assignedBy && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: theme.spacing.sm,
                  color: theme.colors.textSecondary,
                  fontSize: theme.typography.sizes.sm,
                }}
              >
                <UserOutlined />
                <span>Dodijelio: </span>
                <span style={{ color: theme.colors.text, fontWeight: theme.typography.weights.medium }}>
                  {assignedBy}
                </span>
              </div>
            )}
          </div>

          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'flex-end',
              gap: theme.spacing.sm,
            }}
          >
            {dueTime && (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: theme.spacing.xs,
                  color: theme.colors.textSecondary,
                  fontSize: theme.typography.sizes.sm,
                }}
              >
                <ClockCircleOutlined />
                <span>{dueTime}</span>
              </div>
            )}
            {estimatedTime && (
              <div
                style={{
                  color: theme.colors.textSecondary,
                  fontSize: theme.typography.sizes.xs,
                }}
              >
                ETA: ~{Math.round(estimatedTime)} min
              </div>
            )}
            {hasPartial && (
              <Tag color="warning" style={{ margin: 0, borderRadius: theme.borderRadius.sm }}>
                <WarningOutlined /> Djelimično
              </Tag>
            )}
          </div>
        </div>

        <div
          style={{
            display: 'grid',
            gap: theme.spacing.sm,
            gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
            background: 'rgba(17, 24, 39, 0.6)',
            padding: `${theme.spacing.sm} ${theme.spacing.md}`,
            borderRadius: theme.borderRadius.lg,
            border: `1px solid ${theme.colors.border}`,
          }}
        >
          <Metric label="Stavki ukupno" value={totalItems} />
          <Metric label="Zatvoreno" value={completedItems} />
          <Metric label="Razlika" value={shortageDisplay} highlight={hasPartial} />
        </div>

        {aiNote && (
          <div
            style={{
              display: 'flex',
              gap: theme.spacing.sm,
              padding: theme.spacing.sm,
              background: 'rgba(0, 122, 204, 0.12)',
              borderRadius: theme.borderRadius.md,
              color: theme.colors.text,
              fontSize: theme.typography.sizes.sm,
            }}
          >
            <RobotOutlined style={{ color: theme.colors.accent, fontSize: '16px' }} />
            <div>{aiNote}</div>
          </div>
        )}

        <div
          style={{
            display: 'flex',
            justifyContent: 'flex-end',
            marginTop: theme.spacing.sm,
          }}
        >
          <button
            type="button"
            onClick={(event) => {
              event.stopPropagation();
              onClick?.();
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.sm,
              background: 'transparent',
              border: `1px solid ${theme.colors.accent}`,
              color: theme.colors.accent,
              padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
              borderRadius: theme.borderRadius.md,
              fontWeight: theme.typography.weights.semibold,
              fontSize: theme.typography.sizes.sm,
              cursor: 'pointer',
              transition: 'all 0.18s ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'rgba(0, 200, 150, 0.12)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent';
            }}
          >
            Otvori zadatak
            <ArrowRightOutlined />
          </button>
        </div>
      </div>
    </div>
  );
};

interface MetricProps {
  label: string;
  value: string | number;
  highlight?: boolean;
}

const Metric: React.FC<MetricProps> = ({ label, value, highlight = false }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.xs }}>
    <span
      style={{
        color: theme.colors.textSecondary,
        fontSize: theme.typography.sizes.xs,
        textTransform: 'uppercase',
        letterSpacing: '0.6px',
      }}
    >
      {label}
    </span>
    <span
      style={{
        color: highlight ? theme.colors.warning : theme.colors.text,
        fontSize: theme.typography.sizes.base,
        fontWeight: theme.typography.weights.semibold,
      }}
    >
      {value}
    </span>
  </div>
);

export default TaskCard;
