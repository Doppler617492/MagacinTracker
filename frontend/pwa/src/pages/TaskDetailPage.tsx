/**
 * TaskDetailPage - Manual-only picking (NO barcode scanning)
 * 
 * Features:
 * - Manual quantity entry
 * - Close item with shortage (Djelimično)
 * - Mandatory reasons for shortages
 * - Document completion with partial confirmation
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, message, Tag, Modal, Input, Select, Progress, Divider, Switch, Checkbox } from 'antd';
import {
  CheckCircleOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { theme } from '../theme';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';
import HeaderStatusBar from '../components/HeaderStatusBar';
import NumPad from '../components/NumPad';

interface TaskItem {
  id: string;
  naziv: string;
  artikl_sifra: string;
  kolicina_trazena: number;
  picked_qty: number;
  missing_qty: number;
  discrepancy_status: string;
  discrepancy_reason?: string;
  needs_barcode: boolean;
  barkod?: string;
}

interface TaskDetail {
  id: string;
  dokument_broj: string;
  lokacija: string;
  lokacija_naziv: string;
  stavke_total: number;
  stavke_completed: number;
  partial_items: number;
  shortage_qty: number;
  progress: number;
  status: string;
  due_at?: string;
  assigned_by_name?: string;
  assigned_by_id?: string;
  trebovanje_id: string;
  stavke: TaskItem[];
}

const fetchTaskDetail = async (taskId: string): Promise<TaskDetail> => {
  const { data } = await client.get(`/worker/tasks/${taskId}`);
  return data;
};

const TaskDetailPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? 'Tranzitno skladište'
  );

  // UI State
  const [quantityModalVisible, setQuantityModalVisible] = useState(false);
  const [completeModalVisible, setCompleteModalVisible] = useState(false);
  
  const [selectedItem, setSelectedItem] = useState<TaskItem | null>(null);
  const [quantity, setQuantity] = useState<number>(0);
  const [closeItem, setCloseItem] = useState(false);
  const [reason, setReason] = useState<string | undefined>(undefined);
  const [note, setNote] = useState<string>('');
  const [confirmIncompleteChecked, setConfirmIncompleteChecked] = useState(false);

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    const handleQueueChange = (state: OfflineQueueState) => {
      setPendingSync(state.pending);
      setLastSyncedAt(state.lastSyncedAt);
    };

    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueueChange);

    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueueChange);
    };
  }, []);

  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

  // Data Query
  const { data, isLoading } = useQuery({
    queryKey: ['worker', 'tasks', id],
    queryFn: () => fetchTaskDetail(id ?? ''),
    enabled: Boolean(id),
    refetchInterval: 30000, // Refetch every 30s
  });

  // Manual Quantity Entry Mutation
  const manualEntryMutation = useMutation({
    mutationFn: async (payload: { 
      stavkaId: string; 
      quantity: number; 
      closeItem: boolean;
      reason?: string;
      note?: string;
      operationId: string;
    }) => {
      return client.post(`/worker/tasks/${payload.stavkaId}/manual-entry`, {
        quantity: payload.quantity,
        close_item: payload.closeItem,
        reason: payload.reason,
        note: payload.note,
        operation_id: payload.operationId,
      });
    },
    onSuccess: (response) => {
      message.success(response.data.message || 'Količina unesena!');
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks', id] });
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      setQuantityModalVisible(false);
      resetModalState();
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || 'Greška pri unosu količine';
      message.error(errorMsg);
    },
  });

  useEffect(() => {
    if (data?.lokacija_naziv) {
      setWarehouseName(data.lokacija_naziv);
      localStorage.setItem('user_location', data.lokacija_naziv);
    }
  }, [data?.lokacija_naziv]);

  const shortageItems = useMemo(() => {
    if (!data) return [] as TaskItem[];
    return data.stavke.filter(
      (item) => item.discrepancy_status !== 'none' && item.missing_qty > 0
    );
  }, [data]);

  const partialItems = data?.partial_items ?? shortageItems.length;

  const totalShortageQty = useMemo(
    () => shortageItems.reduce((sum, item) => sum + item.missing_qty, 0),
    [shortageItems]
  );

  const inProgressItems = useMemo(() => {
    if (!data) return [] as TaskItem[];
    return data.stavke.filter(
      (item) =>
        item.discrepancy_status === 'none' &&
        item.picked_qty > 0 &&
        item.picked_qty < item.kolicina_trazena
    );
  }, [data]);

  const untouchedItems = useMemo(() => {
    if (!data) return [] as TaskItem[];
    return data.stavke.filter(
      (item) => item.discrepancy_status === 'none' && item.picked_qty === 0
    );
  }, [data]);

  const itemsNeedingAction = inProgressItems.length + untouchedItems.length;

  // Complete Document Mutation
  const completeMutation = useMutation({
    mutationFn: async (payload: { trebovanjeId: string; confirmIncomplete: boolean; operationId: string }) => {
      return client.post(`/worker/documents/${payload.trebovanjeId}/complete`, {
        confirm_incomplete: payload.confirmIncomplete,
        operation_id: payload.operationId,
      });
    },
    onSuccess: () => {
      message.success('Dokument završen!');
      navigate('/');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška pri završavanju');
    },
  });

  // Handlers
  const handleQuantityClick = (item: TaskItem) => {
    setSelectedItem(item);
    setQuantity(item.kolicina_trazena - item.picked_qty);
    setCloseItem(false);
    setReason(undefined);
    setNote('');
    setQuantityModalVisible(true);
  };

  const resetModalState = () => {
    setSelectedItem(null);
    setQuantity(0);
    setCloseItem(false);
    setReason(undefined);
    setNote('');
  };

  const handleQuantityConfirm = (confirmedQuantity: number) => {
    if (!selectedItem) return;

    const required = selectedItem.kolicina_trazena;

    if (confirmedQuantity > required) {
      message.error(`Količina ne može biti veća od tražene (${required})`);
      return;
    }

    const reasonRequired = confirmedQuantity < required || (closeItem && confirmedQuantity === 0);
    if (reasonRequired && !reason) {
      message.error('Razlog je obavezan kad je količina manja od tražene ili zatvarate stavku sa 0');
      return;
    }

    const operationId = `manual-${selectedItem.id}-${Date.now()}`;

    setQuantity(confirmedQuantity);

    if (networkManager.isConnected()) {
      manualEntryMutation.mutate({
        stavkaId: selectedItem.id,
        quantity: confirmedQuantity,
        closeItem,
        reason,
        note: note?.trim() ? note : undefined,
        operationId,
      });
    } else {
      offlineQueue.addAction('manual-entry', selectedItem.id, {
        quantity: confirmedQuantity,
        close_item: closeItem,
        reason,
        note,
        operation_id: operationId,
      });
      message.info('Offline - akcija dodana u red');
      setQuantityModalVisible(false);
      resetModalState();
    }
  };

  const handleCompleteClick = () => {
    if (!data) return;

    if (itemsNeedingAction > 0) {
      message.warning('Postoje stavke bez potvrđenog unosa. Unesite količine ili označite djelimično zatvaranje.');
      return;
    }

    if (partialItems > 0) {
      setConfirmIncompleteChecked(false);
      setCompleteModalVisible(true);
      return;
    }

    handleCompleteConfirm(false);
  };

  const handleCompleteConfirm = (confirmIncomplete: boolean) => {
    if (!data) return;

    if (confirmIncomplete && partialItems > 0 && !confirmIncompleteChecked) {
      message.warning('Potvrdite djelimično završavanje dokumenta.');
      return;
    }

    const operationId = `complete-${data.trebovanje_id}-${Date.now()}`;

    if (networkManager.isConnected()) {
      completeMutation.mutate({
        trebovanjeId: data.trebovanje_id,
        confirmIncomplete,
        operationId,
      });
    } else {
      offlineQueue.addAction('complete-document', data.trebovanje_id, {
        confirm_incomplete: confirmIncomplete,
        operation_id: operationId,
      });
      message.info('Offline - akcija dodana u red');
      navigate('/');
    }

    setConfirmIncompleteChecked(false);
    setCompleteModalVisible(false);
  };

  const displayRole = userProfile?.role
    ? userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)
    : 'Magacioner';

  if (isLoading || !data) {
    return (
      <div
        style={{
          minHeight: '100vh',
          background: theme.colors.background,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        <HeaderStatusBar
          warehouseName={warehouseName}
          userName={userProfile?.fullName ?? 'Worker'}
          userRole={displayRole}
          userEmail={userProfile?.email}
          isOnline={isOnline}
          pendingSyncCount={pendingSync}
          lastSyncedAt={lastSyncedAt}
        />
        <div style={{ padding: theme.spacing.lg, textAlign: 'center', flex: 1 }}>
          <p style={{ color: theme.colors.text }}>Učitavanje zadatka...</p>
        </div>
      </div>
    );
  }

  const allItemsProcessed = itemsNeedingAction === 0;

  const documentStatusTag = data.status === 'done'
    ? { color: 'green', label: 'Završen' }
    : data.status === 'in_progress'
      ? { color: 'orange', label: 'U toku' }
      : { color: 'blue', label: 'Dodijeljen' };

  const totalRequested = data.stavke.reduce((sum, item) => sum + item.kolicina_trazena, 0);
  const totalEntered = data.stavke.reduce((sum, item) => sum + item.picked_qty, 0);
  const overallProgressPercent = totalRequested ? Math.round((totalEntered / totalRequested) * 100) : 0;

  const formatNumber = (val: number) =>
    Number.isInteger(val) ? val.toString() : val.toLocaleString('sr-Latn-ME', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });

  const dueDateLabel = data.due_at ? new Date(data.due_at).toLocaleString('sr-Latn-ME') : '—';

  const allowDecimalForSelected = selectedItem
    ? Math.abs(selectedItem.kolicina_trazena - Math.round(selectedItem.kolicina_trazena)) > 0.0001
    : false;

  const reasonIsRequired = selectedItem
    ? quantity < selectedItem.kolicina_trazena || (closeItem && quantity === 0)
    : false;

  const quantityExtras = selectedItem ? (
    <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
      <div
        style={{
          padding: theme.spacing.sm,
          background: theme.colors.background,
          borderRadius: theme.borderRadius.sm,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ color: theme.colors.text, fontWeight: 600 }}>Zatvori stavku</div>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
            Završi stavku čak i ako je količina manja od tražene
          </div>
        </div>
        <Switch checked={closeItem} onChange={setCloseItem} />
      </div>

      <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs }}>
        Maksimalno: {formatNumber(selectedItem.kolicina_trazena)}
      </div>

      {(reasonIsRequired || reason) && (
        <div
          style={{
            padding: theme.spacing.md,
            background: 'rgba(255, 193, 7, 0.1)',
            border: `1px solid ${theme.colors.warning}`,
            borderRadius: theme.borderRadius.sm,
            display: 'flex',
            flexDirection: 'column',
            gap: theme.spacing.sm,
          }}
        >
          <div style={{ color: theme.colors.text, fontWeight: 600 }}>Razlog (obavezno)</div>
          <Select
            value={reason}
            onChange={setReason}
            placeholder="Odaberite razlog"
            size="large"
            style={{ width: '100%' }}
            options={[
              { value: 'Nije na stanju', label: 'Nije na stanju' },
              { value: 'Nije pronađeno', label: 'Nije pronađeno' },
              { value: 'Oštećeno', label: 'Oštećeno' },
              { value: 'Pogrešan navod u dokumentu', label: 'Pogrešan navod u dokumentu' },
              { value: 'Drugo', label: 'Drugo' },
            ]}
          />
          <Input.TextArea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Napomena (opciono)"
            rows={2}
            style={{ fontSize: theme.typography.sizes.sm }}
          />
        </div>
      )}
    </div>
  ) : undefined;

  return (
    <div
      style={{
        minHeight: '100vh',
        background: theme.colors.background,
        display: 'flex',
        flexDirection: 'column',
        paddingBottom: '80px',
      }}
    >
      <HeaderStatusBar
        warehouseName={warehouseName}
        userName={userProfile?.fullName ?? 'Worker'}
        userRole={displayRole}
        userEmail={userProfile?.email}
        isOnline={isOnline}
        pendingSyncCount={pendingSync}
        lastSyncedAt={lastSyncedAt}
      />

      <div style={{ flex: 1, padding: theme.spacing.md, paddingBottom: '140px' }}>
        {/* Header */}
        <div style={{ marginBottom: theme.spacing.lg }}>
          <h1 style={{ color: theme.colors.text, fontSize: theme.typography.sizes.xl, margin: 0 }}>
            {data.dokument_broj}
          </h1>
        <div style={{ color: theme.colors.textSecondary, margin: `${theme.spacing.xs} 0` }}>
          {data.lokacija_naziv}
        </div>
        <Tag color={documentStatusTag.color}>{documentStatusTag.label}</Tag>

        <div
          style={{
            marginTop: theme.spacing.md,
            background: theme.colors.cardBackground,
            borderRadius: theme.borderRadius.md,
            border: `1px solid ${theme.colors.border}`,
            padding: theme.spacing.md,
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))',
            gap: theme.spacing.sm,
          }}
        >
          <div>
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Lokacija
            </div>
            <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.base, fontWeight: 600 }}>
              {data.lokacija_naziv}
            </div>
          </div>
          <div>
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Dodijelio
            </div>
            <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.base, fontWeight: 600 }}>
              {data.assigned_by_name ?? '—'}
            </div>
          </div>
          <div>
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Rok
            </div>
            <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.base, fontWeight: 600 }}>
              {dueDateLabel}
            </div>
          </div>
          <div>
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Djelimično
            </div>
            <div style={{ color: partialItems > 0 ? theme.colors.warning : theme.colors.text, fontSize: theme.typography.sizes.base, fontWeight: 600 }}>
              {partialItems} linija
            </div>
          </div>
        </div>
      </div>

      {/* Summary Card */}
      <div
        style={{
          background: theme.colors.cardBackground,
          padding: theme.spacing.md,
          borderRadius: theme.borderRadius.md,
          marginBottom: theme.spacing.md,
          border: `1px solid ${theme.colors.border}`,
        }}
      >
        <div style={{ marginBottom: theme.spacing.sm }}>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Traženo
          </span>
          <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.lg, fontWeight: 600, float: 'right' }}>
            {formatNumber(totalRequested)}
          </span>
        </div>
        <div style={{ marginBottom: theme.spacing.sm }}>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Uneseno
          </span>
          <span style={{ color: theme.colors.accent, fontSize: theme.typography.sizes.lg, fontWeight: 600, float: 'right' }}>
            {formatNumber(totalEntered)}
          </span>
        </div>
        <div style={{ marginBottom: theme.spacing.sm }}>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Razlika
          </span>
          <span style={{ color: theme.colors.warning, fontSize: theme.typography.sizes.lg, fontWeight: 600, float: 'right' }}>
            {totalShortageQty > 0 ? `-${formatNumber(totalShortageQty)}` : '0'}
          </span>
        </div>
        <Divider style={{ margin: `${theme.spacing.sm} 0`, background: theme.colors.border }} />
        <div>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Zatvorene stavke
          </span>
          <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.md, fontWeight: 600, float: 'right' }}>
            {data.stavke_completed} / {data.stavke_total}
          </span>
        </div>
        <div>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Djelimično zatvorene
          </span>
          <span style={{ color: partialItems > 0 ? theme.colors.warning : theme.colors.text, fontSize: theme.typography.sizes.md, fontWeight: 600, float: 'right' }}>
            {partialItems}
          </span>
        </div>
      </div>

      {/* Progress */}
      <div
        style={{
          background: theme.colors.cardBackground,
          padding: theme.spacing.md,
          borderRadius: theme.borderRadius.md,
          marginBottom: theme.spacing.md,
          border: `1px solid ${theme.colors.border}`,
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: theme.spacing.sm }}>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Napredak
          </span>
          <span style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            {overallProgressPercent}%
          </span>
        </div>
        <Progress
          percent={overallProgressPercent}
          strokeColor={theme.colors.accent}
          trailColor={theme.colors.neutral}
          strokeWidth={12}
        />
      </div>

      {/* Shortage Warning */}
      {partialItems > 0 && (
        <div
          style={{
            background: 'rgba(255, 193, 7, 0.1)',
            border: `1px solid ${theme.colors.warning}`,
            borderRadius: theme.borderRadius.md,
            padding: theme.spacing.md,
            marginBottom: theme.spacing.md,
            display: 'flex',
            alignItems: 'center',
            gap: theme.spacing.sm,
          }}
        >
          <WarningOutlined style={{ color: theme.colors.warning, fontSize: '20px' }} />
          <div>
            <div style={{ color: theme.colors.text, fontWeight: 600 }}>
              Djelimično: {partialItems} {partialItems === 1 ? 'linija' : 'linija'}
            </div>
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
              Razlika: {formatNumber(totalShortageQty)} kom
            </div>
          </div>
        </div>
      )}

      {/* Items List */}
      <div style={{ marginBottom: theme.spacing.lg }}>
        {data.stavke.map((item) => {
          const isComplete = item.picked_qty >= item.kolicina_trazena;
          const hasShortage = item.discrepancy_status !== 'none' && item.missing_qty > 0;
          const progressPercent = item.kolicina_trazena
            ? Math.min((item.picked_qty / item.kolicina_trazena) * 100, 100)
            : 0;

          let statusBadge = { text: 'Novo', color: 'default' as string };
          if (item.discrepancy_status === 'short_pick') {
            statusBadge = { text: 'Djelimično', color: 'orange' };
          } else if (item.discrepancy_status === 'not_found') {
            statusBadge = { text: 'Nije pronađeno', color: 'red' };
          } else if (item.discrepancy_status === 'damaged') {
            statusBadge = { text: 'Oštećeno', color: 'magenta' };
          } else if (isComplete) {
            statusBadge = { text: 'Zatvoreno', color: 'green' };
          } else if (item.picked_qty > 0) {
            statusBadge = { text: 'U toku', color: 'blue' };
          }

          return (
            <div
              key={item.id}
              style={{
                background: theme.colors.cardBackground,
                border: `1px solid ${hasShortage ? theme.colors.warning : theme.colors.border}`,
                borderRadius: theme.borderRadius.md,
                padding: theme.spacing.md,
                marginBottom: theme.spacing.md,
              }}
            >
              {/* Item Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: theme.spacing.sm }}>
                <div style={{ flex: 1 }}>
                  <div style={{ color: theme.colors.text, fontSize: theme.typography.sizes.md, fontWeight: 600 }}>
                    {item.naziv}
                  </div>
                  <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm, marginTop: '2px' }}>
                    Šifra: {item.artikl_sifra}
                  </div>
                </div>
                <div>
                  <Tag color={statusBadge.color as any}>{statusBadge.text}</Tag>
                </div>
              </div>

              {/* Quantity Info */}
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: '1fr 1fr 1fr', 
                gap: theme.spacing.xs,
                marginBottom: theme.spacing.sm,
                fontSize: theme.typography.sizes.sm,
              }}>
                <div>
                  <div style={{ color: theme.colors.textSecondary }}>Traženo:</div>
                  <div style={{ color: theme.colors.text, fontWeight: 600 }}>{formatNumber(item.kolicina_trazena)}</div>
                </div>
                <div>
                  <div style={{ color: theme.colors.textSecondary }}>Uneseno:</div>
                  <div style={{ color: theme.colors.accent, fontWeight: 600 }}>{formatNumber(item.picked_qty)}</div>
                </div>
                <div>
                  <div style={{ color: theme.colors.textSecondary }}>Razlika:</div>
                  <div style={{ color: item.missing_qty > 0 ? theme.colors.warning : theme.colors.success, fontWeight: 600 }}>
                    {item.missing_qty > 0 ? `-${formatNumber(item.missing_qty)}` : '0'}
                  </div>
                </div>
              </div>

              {/* Progress Bar */}
              <div style={{ marginBottom: theme.spacing.sm }}>
                <Progress
                  percent={Math.min(progressPercent, 100)}
                  strokeColor={hasShortage ? theme.colors.warning : theme.colors.accent}
                  trailColor={theme.colors.neutral}
                  showInfo={false}
                  strokeWidth={8}
                />
              </div>

              {/* Discrepancy Info */}
              {hasShortage && item.discrepancy_reason && (
                <div
                  style={{
                    background: theme.colors.background,
                    padding: theme.spacing.sm,
                    borderRadius: theme.borderRadius.sm,
                    marginBottom: theme.spacing.sm,
                  }}
                >
                  <div style={{ color: theme.colors.warning, fontSize: theme.typography.sizes.xs, fontWeight: 600 }}>
                    Razlog: {item.discrepancy_reason}
                  </div>
                </div>
              )}

              {/* Action Button - Always show "Unesi količinu" unless fully complete */}
              {(!isComplete || item.discrepancy_status !== 'none') && (
                <button
                  onClick={() => handleQuantityClick(item)}
                  style={{
                    width: '100%',
                    background: theme.colors.primary,
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: theme.borderRadius.sm,
                    padding: `${theme.spacing.md} ${theme.spacing.lg}`,
                    fontSize: theme.typography.sizes.md,
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: theme.spacing.sm,
                  }}
                >
                  <EditOutlined /> Unesi količinu
                </button>
              )}
            </div>
          );
        })}
      </div>

      </div>

      {/* Sticky Footer */}
      <div
        style={{
          position: 'fixed',
          bottom: '70px',
          left: 0,
          right: 0,
          padding: theme.spacing.md,
          background: theme.colors.background,
          borderTop: `1px solid ${theme.colors.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
          Stavke završene: {data.stavke_completed}/{data.stavke_total}
        </div>
        <div style={{ display: 'flex', gap: theme.spacing.sm }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: theme.colors.neutral,
              color: theme.colors.text,
              border: `1px solid ${theme.colors.border}`,
              borderRadius: theme.borderRadius.sm,
              padding: `${theme.spacing.sm} ${theme.spacing.md}`,
              fontSize: theme.typography.sizes.sm,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Sačuvaj i izađi
          </button>
          <button
            onClick={handleCompleteClick}
            style={{
              background: theme.colors.success,
              color: '#ffffff',
              border: 'none',
              borderRadius: theme.borderRadius.sm,
              padding: `${theme.spacing.sm} ${theme.spacing.lg}`,
              fontSize: theme.typography.sizes.sm,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.xs,
              opacity: allItemsProcessed ? 1 : 0.85,
            }}
          >
            <CheckCircleOutlined /> Završi dokument
          </button>
        </div>
      </div>


      {/* Manual Quantity Entry Modal */}
      <NumPad
        visible={quantityModalVisible}
        title={
          selectedItem
            ? `${selectedItem.naziv}${selectedItem.artikl_sifra ? ` — ${selectedItem.artikl_sifra}` : ''}`
            : 'Unesite količinu'
        }
        defaultValue={quantity}
        maxValue={selectedItem?.kolicina_trazena}
        allowDecimal={allowDecimalForSelected}
        confirmLabel="Sačuvaj"
        cancelLabel="Odustani"
        confirmLoading={manualEntryMutation.isPending}
        onCancel={() => {
          setQuantityModalVisible(false);
          resetModalState();
        }}
        onValueChange={(val) => setQuantity(val)}
        onConfirm={handleQuantityConfirm}
        extraContent={quantityExtras}
      />

      {/* Complete Confirmation Modal */}
      <Modal
        open={completeModalVisible}
        title="Potvrdi završetak"
        onCancel={() => {
          setCompleteModalVisible(false);
          setConfirmIncompleteChecked(false);
        }}
        footer={null}
        styles={{ body: { background: theme.colors.background } }}
      >
        <div style={{ marginBottom: theme.spacing.lg }}>
          <div style={{ color: theme.colors.warning, fontSize: theme.typography.sizes.md, fontWeight: 600, marginBottom: theme.spacing.sm }}>
            <ExclamationCircleOutlined /> Dokument sadrži djelimične stavke
          </div>
          <div style={{ color: theme.colors.text, marginBottom: theme.spacing.xs }}>
            {partialItems} {partialItems === 1 ? 'linija' : 'linija'} sa razlikom
          </div>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Ukupna razlika: {formatNumber(totalShortageQty)} kom
          </div>
          <Divider />
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Želite li završiti dokument sa evidentiranim razlikama?
          </div>
        </div>
        <Checkbox
          checked={confirmIncompleteChecked}
          onChange={(event) => setConfirmIncompleteChecked(event.target.checked)}
          style={{ marginBottom: theme.spacing.md }}
        >
          Potvrđujem djelimično završavanje
        </Checkbox>
        <div style={{ display: 'flex', gap: theme.spacing.sm }}>
          <Button
            size="large"
            onClick={() => {
              setCompleteModalVisible(false);
              setConfirmIncompleteChecked(false);
            }}
            style={{ flex: 1 }}
          >
            Odustani
          </Button>
          <Button
            type="primary"
            size="large"
            onClick={() => handleCompleteConfirm(true)}
            loading={completeMutation.isPending}
            disabled={!confirmIncompleteChecked || completeMutation.isPending}
            style={{ flex: 1 }}
          >
            Završi sada
          </Button>
        </div>
      </Modal>
    </div>
  );
};

export default TaskDetailPage;
