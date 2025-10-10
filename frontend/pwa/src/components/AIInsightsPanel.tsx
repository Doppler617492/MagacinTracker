import React, { useState } from 'react';
import { 
  ThunderboltOutlined, 
  LineChartOutlined,
  CloseOutlined,
  DownOutlined,
  UpOutlined
} from '@ant-design/icons';
import { theme } from '../theme';

interface AIInsight {
  id: string;
  icon: React.ReactNode;
  title: string;
  message: string;
  type: 'info' | 'warning' | 'success';
}

interface AIInsightsPanelProps {
  isEdgeMode?: boolean;
  predictedWorkload?: number;
  predictedDays?: number;
}

const AIInsightsPanel: React.FC<AIInsightsPanelProps> = ({
  isEdgeMode = false,
  predictedWorkload = 0,
  predictedDays = 7,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [dismissedInsights, setDismissedInsights] = useState<Set<string>>(new Set());

  const insights: AIInsight[] = [
    ...(isEdgeMode ? [{
      id: 'edge-mode',
      icon: <ThunderboltOutlined style={{ fontSize: '20px' }} />,
      title: 'Edge Mode Aktivan',
      message: 'Uređaj radi u offline režimu. Predviđanja se generišu lokalno iz keširanih podataka i biće automatski sinhronizovana kada se veza vrati.',
      type: 'info' as const,
    }] : []),
    ...(predictedWorkload > 0 ? [{
      id: 'workload-prediction',
      icon: <LineChartOutlined style={{ fontSize: '20px' }} />,
      title: `Predviđeno povećanje opterećenja`,
      message: `AI sistem predviđa povećanje opterećenja — približno ${predictedWorkload} stavki u narednih ${predictedDays} dana. Pripremite se u skladu s tim.`,
      type: 'warning' as const,
    }] : []),
  ];

  const visibleInsights = insights.filter(insight => !dismissedInsights.has(insight.id));

  const handleDismiss = (insightId: string) => {
    setDismissedInsights(prev => new Set([...prev, insightId]));
  };

  const getTypeColor = (type: AIInsight['type']) => {
    switch (type) {
      case 'warning':
        return theme.colors.warning;
      case 'success':
        return theme.colors.success;
      default:
        return theme.colors.primary;
    }
  };

  if (visibleInsights.length === 0) {
    return null;
  }

  return (
    <div
      style={{
        background: theme.colors.background,
        borderBottom: `1px solid ${theme.colors.border}`,
      }}
    >
      {/* Collapsible Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
          cursor: 'pointer',
          background: theme.colors.cardBackground,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: theme.spacing.sm }}>
          <ThunderboltOutlined style={{ fontSize: '16px', color: theme.colors.accent }} />
          <span
            style={{
              color: theme.colors.text,
              fontSize: theme.typography.sizes.sm,
              fontWeight: theme.typography.weights.semibold,
              letterSpacing: '0.5px',
            }}
          >
            AI UVIDI
          </span>
          <span
            style={{
              background: theme.colors.neutral,
              color: theme.colors.textSecondary,
              fontSize: theme.typography.sizes.xs,
              padding: '2px 6px',
              borderRadius: theme.borderRadius.sm,
              fontWeight: theme.typography.weights.medium,
            }}
          >
            {visibleInsights.length}
          </span>
        </div>
        {isExpanded ? (
          <UpOutlined style={{ fontSize: '12px', color: theme.colors.textSecondary }} />
        ) : (
          <DownOutlined style={{ fontSize: '12px', color: theme.colors.textSecondary }} />
        )}
      </div>

      {/* Insights Cards */}
      {isExpanded && (
        <div
          style={{
            padding: `${theme.spacing.sm} ${theme.spacing.lg} ${theme.spacing.lg}`,
            display: 'flex',
            flexDirection: 'column',
            gap: theme.spacing.md,
          }}
        >
          {visibleInsights.map((insight) => (
            <div
              key={insight.id}
              style={{
                background: theme.colors.cardBackground,
                border: `1px solid ${theme.colors.border}`,
                borderLeft: `3px solid ${getTypeColor(insight.type)}`,
                borderRadius: theme.borderRadius.lg,
                padding: theme.spacing.md,
                display: 'flex',
                gap: theme.spacing.md,
                alignItems: 'flex-start',
                boxShadow: theme.shadows.sm,
              }}
            >
              {/* Icon */}
              <div
                style={{
                  color: getTypeColor(insight.type),
                  flexShrink: 0,
                }}
              >
                {insight.icon}
              </div>

              {/* Content */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    color: theme.colors.text,
                    fontSize: theme.typography.sizes.sm,
                    fontWeight: theme.typography.weights.semibold,
                    marginBottom: theme.spacing.xs,
                  }}
                >
                  {insight.title}
                </div>
                <div
                  style={{
                    color: theme.colors.textSecondary,
                    fontSize: theme.typography.sizes.xs,
                    lineHeight: '1.5',
                  }}
                >
                  {insight.message}
                </div>
              </div>

              {/* Dismiss Button */}
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleDismiss(insight.id);
                }}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: theme.colors.textSecondary,
                  cursor: 'pointer',
                  padding: theme.spacing.xs,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: theme.borderRadius.sm,
                  flexShrink: 0,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = theme.colors.neutral)}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <CloseOutlined style={{ fontSize: '12px' }} />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AIInsightsPanel;

