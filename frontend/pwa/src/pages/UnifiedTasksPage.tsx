/**
 * UnifiedTasksPage - Combined My Tasks + Team Tasks
 * Shows both personal and team-assigned tasks with clear ownership indicators
 * White enterprise theme
 */

import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { Input, Tag, Progress } from 'antd';
import { Search, User, Users, ChevronRight, Clock } from 'lucide-react';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { whiteTheme } from '../theme-white';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';
import { useWebSocket } from '../hooks/useWebSocket';
import { useTranslation } from '../hooks/useTranslation';

interface TaskData {
  id: string;
  dokument: string;
  lokacija: string;
  progress: number;
  stavke_total: number;
  stavke_completed: number;
  partial_items: number;
  shortage_qty: number;
  status: string;
  due_at?: string;
  assigned_by?: string;
  assigned_by_id?: string;
  assigned_by_name?: string;
  assigned_to_team?: boolean;
  team_members?: string[];
  created_at?: string;
}

const fetchTasks = async (): Promise<TaskData[]> => {
  const { data } = await client.get('/worker/tasks');
  return data;
};

const UnifiedTasksPage: React.FC = () => {
  const navigate = useNavigate();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // WebSocket for real-time updates
  useWebSocket(['worker', 'kpi', 'dashboard']);

  const { data: tasks, isLoading, refetch: refetchTasks } = useQuery({
    queryKey: ['worker', 'tasks'],
    queryFn: fetchTasks,
    refetchInterval: isOnline ? 30000 : false,
  });

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => {
      setIsOnline(online);
      if (online) refetchTasks();
    };
    const handleQueue = (state: OfflineQueueState) => setPendingSync(state.pending);
    
    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueue);
    
    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueue);
    };
  }, [refetchTasks]);

  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

  const filteredTasks = useMemo(() => {
    if (!tasks) return [];

    const searchValue = searchTerm.trim().toLowerCase();

    return tasks
      .filter((task) => {
        // Status filter
        const matchesStatus =
          statusFilter === 'all' ||
          (statusFilter === 'active' && task.status !== 'done') ||
          (statusFilter === 'in_progress' && task.status === 'in_progress') ||
          (statusFilter === 'new' && task.status === 'assigned') ||
          (statusFilter === 'partial' && (task.partial_items ?? 0) > 0) ||
          (statusFilter === 'completed' && task.status === 'done');

        if (!matchesStatus) return false;

        // Search filter
        if (!searchValue) return true;

        const haystacks = [
          task.dokument,
          task.lokacija,
          task.assigned_by_name,
          task.assigned_by,
        ]
          .filter(Boolean)
          .map((value) => value!.toLowerCase());

        return haystacks.some((value) => value.includes(searchValue));
      })
      .sort((a, b) => {
        // Sort: partial first, then in_progress, then new, then done
        const aPartial = (a.partial_items ?? 0) > 0 ? 0 : 1;
        const bPartial = (b.partial_items ?? 0) > 0 ? 0 : 1;
        if (aPartial !== bPartial) return aPartial - bPartial;

        const statusPriority: Record<string, number> = {
          in_progress: 0,
          assigned: 1,
          done: 2,
        };

        return (statusPriority[a.status] ?? 99) - (statusPriority[b.status] ?? 99);
      });
  }, [tasks, statusFilter, searchTerm]);

  const summary = useMemo(() => {
    if (!tasks) return { total: 0, active: 0, completed: 0, partial: 0 };
    
    return {
      total: tasks.length,
      active: tasks.filter((t) => t.status !== 'done').length,
      completed: tasks.filter((t) => t.status === 'done').length,
      partial: tasks.filter((t) => (t.partial_items ?? 0) > 0).length,
    };
  }, [tasks]);

  const getStatusBadge = (task: TaskData) => {
    if (task.status === 'done') {
      return { bg: whiteTheme.colors.badge.done, color: whiteTheme.colors.badge.doneText, label: t.status.done };
    }
    if ((task.partial_items ?? 0) > 0) {
      return { bg: whiteTheme.colors.badge.partial, color: whiteTheme.colors.badge.partialText, label: t.status.partial };
    }
    if (task.status === 'in_progress') {
      return { bg: whiteTheme.colors.badge.inProgress, color: whiteTheme.colors.badge.inProgressText, label: t.status.inProgress };
    }
    return { bg: whiteTheme.colors.badge.new, color: whiteTheme.colors.badge.newText, label: t.status.new };
  };

  const getAge = (createdAt?: string) => {
    if (!createdAt) return '';
    const now = Date.now();
    const created = new Date(createdAt).getTime();
    const diff = now - created;
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return `${Math.floor(diff / (1000 * 60))}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: whiteTheme.colors.background,
        paddingBottom: '80px',
        paddingTop: whiteTheme.spacing.lg,
      }}
    >
      {/* Page Title */}
      <div
        style={{
          padding: `0 ${whiteTheme.spacing.lg}`,
          marginBottom: whiteTheme.spacing.lg,
        }}
      >
        <h1
          style={{
            fontSize: whiteTheme.typography.sizes.xl,
            fontWeight: whiteTheme.typography.weights.bold,
            color: whiteTheme.colors.text,
            margin: 0,
          }}
        >
          {t.tasks.title}
        </h1>

        {/* Summary Stats */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
          {[
            { label: t.tasks.totalTasks, value: summary.total, color: whiteTheme.colors.text },
            { label: t.tasks.activeTasks, value: summary.active, color: whiteTheme.colors.primary },
            { label: t.tasks.partialTasks, value: summary.partial, color: whiteTheme.colors.warning },
            { label: t.tasks.completedTasks, value: summary.completed, color: whiteTheme.colors.accent },
          ].map((stat) => (
            <div
              key={stat.label}
              style={{
                background: whiteTheme.colors.panelBackground,
                padding: whiteTheme.spacing.md,
                borderRadius: whiteTheme.borderRadius.md,
                border: `1px solid ${whiteTheme.colors.border}`,
              }}
            >
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                {stat.label}
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xl, fontWeight: whiteTheme.typography.weights.bold, color: stat.color }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>

        {/* Search & Filters */}
        <div style={{ display: 'flex', gap: whiteTheme.spacing.sm, marginBottom: whiteTheme.spacing.md, flexWrap: 'wrap' }}>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <Input
              prefix={<Search size={16} color={whiteTheme.colors.textSecondary} />}
              placeholder={t.tasks.searchPlaceholder}
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              allowClear
              style={{ height: '40px' }}
            />
          </div>
        </div>

        {/* Status Filters */}
        <div style={{ display: 'flex', gap: whiteTheme.spacing.sm, flexWrap: 'wrap' }}>
          {[
            { value: 'all', label: t.tasks.allTasks, count: summary.total },
            { value: 'active', label: t.tasks.activeTasks, count: summary.active },
            { value: 'partial', label: t.tasks.partialTasks, count: summary.partial },
            { value: 'completed', label: t.tasks.completedTasks, count: summary.completed },
          ].map((filter) => (
            <button
              key={filter.value}
              onClick={() => setStatusFilter(filter.value)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: whiteTheme.spacing.xs,
                padding: `${whiteTheme.spacing.xs} ${whiteTheme.spacing.md}`,
                borderRadius: whiteTheme.borderRadius.full,
                border: `1px solid ${statusFilter === filter.value ? whiteTheme.colors.primary : whiteTheme.colors.border}`,
                background: statusFilter === filter.value ? whiteTheme.colors.primaryLight : whiteTheme.colors.cardBackground,
                color: statusFilter === filter.value ? whiteTheme.colors.primary : whiteTheme.colors.text,
                fontSize: whiteTheme.typography.sizes.sm,
                fontWeight: whiteTheme.typography.weights.medium,
                cursor: 'pointer',
                transition: whiteTheme.transitions.fast,
              }}
            >
              {filter.label}
              <span
                style={{
                  background: statusFilter === filter.value ? whiteTheme.colors.primary : whiteTheme.colors.border,
                  color: statusFilter === filter.value ? 'white' : whiteTheme.colors.text,
                  borderRadius: whiteTheme.borderRadius.full,
                  padding: `0 ${whiteTheme.spacing.xs}`,
                  minWidth: '20px',
                  textAlign: 'center',
                  fontSize: whiteTheme.typography.sizes.xs,
                }}
              >
                {filter.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Task List */}
      <div style={{ padding: whiteTheme.spacing.lg }}>
        {isLoading ? (
          <div className="wms-loading">Loading tasks...</div>
        ) : filteredTasks.length === 0 ? (
          <div className="wms-empty">
            <div className="wms-empty-icon">📋</div>
            <div className="wms-empty-text">No tasks found</div>
            <div className="wms-empty-description">
              {searchTerm ? 'Try adjusting your search' : 'No tasks assigned yet'}
            </div>
          </div>
        ) : (
          filteredTasks.map((task) => {
            const statusBadge = getStatusBadge(task);
            
            return (
              <div
                key={task.id}
                onClick={() => navigate(`/tasks/${task.id}`)}
                style={{
                  background: whiteTheme.colors.cardBackground,
                  border: `1px solid ${whiteTheme.colors.border}`,
                  borderRadius: whiteTheme.borderRadius.lg,
                  padding: whiteTheme.spacing.lg,
                  marginBottom: whiteTheme.spacing.md,
                  cursor: 'pointer',
                  transition: whiteTheme.transitions.normal,
                  boxShadow: whiteTheme.shadows.card,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.boxShadow = whiteTheme.shadows.md;
                  e.currentTarget.style.borderColor = whiteTheme.colors.primary;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.boxShadow = whiteTheme.shadows.card;
                  e.currentTarget.style.borderColor = whiteTheme.colors.border;
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: whiteTheme.spacing.md }}>
                  <div style={{ flex: 1 }}>
                    <div
                      style={{
                        fontSize: whiteTheme.typography.sizes.lg,
                        fontWeight: whiteTheme.typography.weights.semibold,
                        color: whiteTheme.colors.text,
                        marginBottom: '4px',
                      }}
                    >
                      {task.dokument}
                    </div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                      {task.lokacija}
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.sm }}>
                    <div
                      style={{
                        background: statusBadge.bg,
                        color: statusBadge.color,
                        padding: `${whiteTheme.spacing.xs} ${whiteTheme.spacing.md}`,
                        borderRadius: whiteTheme.borderRadius.full,
                        fontSize: whiteTheme.typography.sizes.xs,
                        fontWeight: whiteTheme.typography.weights.semibold,
                      }}
                    >
                      {statusBadge.label}
                    </div>
                    <ChevronRight size={20} color={whiteTheme.colors.textMuted} />
                  </div>
                </div>

                {/* Progress */}
                <div style={{ marginBottom: whiteTheme.spacing.md }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: whiteTheme.spacing.xs }}>
                    <span style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                      Progress
                    </span>
                    <span style={{ fontSize: whiteTheme.typography.sizes.xs, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                      {task.stavke_completed} / {task.stavke_total} items
                    </span>
                  </div>
                  <Progress
                    percent={task.progress}
                    strokeColor={whiteTheme.colors.accent}
                    trailColor={whiteTheme.colors.divider}
                    strokeWidth={8}
                    showInfo={false}
                  />
                </div>

                {/* Meta Info */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: whiteTheme.spacing.sm }}>
                  {/* Assigned By */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.xs, fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                    {task.assigned_to_team ? (
                      <>
                        <Users size={14} />
                        <span>Team Task</span>
                      </>
                    ) : (
                      <>
                        <User size={14} />
                        <span>Personal</span>
                      </>
                    )}
                    {task.assigned_by_name && <span>• by {task.assigned_by_name}</span>}
                  </div>

                  {/* Age */}
                  {task.created_at && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.xs, fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textMuted }}>
                      <Clock size={14} />
                      {getAge(task.created_at)}
                    </div>
                  )}
                </div>

                {/* Partial Warning */}
                {(task.partial_items ?? 0) > 0 && (
                  <div
                    style={{
                      marginTop: whiteTheme.spacing.md,
                      padding: whiteTheme.spacing.sm,
                      background: whiteTheme.colors.badge.partial,
                      border: `1px solid ${whiteTheme.colors.badge.partialText}`,
                      borderRadius: whiteTheme.borderRadius.sm,
                      fontSize: whiteTheme.typography.sizes.xs,
                      color: whiteTheme.colors.badge.partialText,
                      fontWeight: whiteTheme.typography.weights.medium,
                    }}
                  >
                    ⚠️ {task.partial_items} item(s) with shortage • Missing: {task.shortage_qty}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

export default UnifiedTasksPage;

