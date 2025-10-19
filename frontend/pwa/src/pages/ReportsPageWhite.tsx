/**
 * ReportsPage/History - White Enterprise Theme
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, History as HistoryIcon } from 'lucide-react';
import { whiteTheme } from '../theme-white';
import { useTranslation } from '../hooks/useTranslation';

const ReportsPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');

  return (
    <div style={{ minHeight: '100vh', background: whiteTheme.colors.background }}>
      <div
        style={{
          background: whiteTheme.colors.cardBackground,
          borderBottom: `1px solid ${whiteTheme.colors.border}`,
          padding: whiteTheme.spacing.lg,
          boxShadow: whiteTheme.shadows.sm,
        }}
      >
        <button onClick={() => navigate('/')} className="wms-btn wms-btn-secondary" style={{ marginBottom: whiteTheme.spacing.md }}>
          <ArrowLeft size={16} /> Home
        </button>
        <h1 style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
          History
        </h1>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        <div className="wms-empty">
          <div className="wms-empty-icon">
            <HistoryIcon size={48} color={whiteTheme.colors.textMuted} />
          </div>
          <div className="wms-empty-text">History Module</div>
          <div className="wms-empty-description">
            View completed tasks, exceptions, and stock counts here.
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportsPageWhite;

