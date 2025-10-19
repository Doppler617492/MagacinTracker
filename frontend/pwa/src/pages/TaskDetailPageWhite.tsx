/**
 * TaskDetailPage - White Enterprise Theme
 * Manual quantity entry with professional WMS design
 */

import React, { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, message, Tag, Modal, Input, Select, Progress, Checkbox, Switch } from 'antd';
import { CheckCircle, Edit3, AlertCircle, AlertTriangle, ArrowLeft, Save, ScanBarcode, Clock, Target } from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { whiteTheme } from '../theme-white';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';
import NumPad from '../components/NumPad';
import { useTranslation } from '../hooks/useTranslation';

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

const TaskDetailPageWhite = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [userProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());

  // UI State
  const [quantityModalVisible, setQuantityModalVisible] = useState(false);
  const [completeModalVisible, setCompleteModalVisible] = useState(false);
  
  const [selectedItem, setSelectedItem] = useState<TaskItem | null>(null);
  const [quantity, setQuantity] = useState<number>(0);
  const [closeItem, setCloseItem] = useState(false);
  const [reason, setReason] = useState<string | undefined>(undefined);
  const [note, setNote] = useState<string>('');
  const [confirmIncompleteChecked, setConfirmIncompleteChecked] = useState(false);

  // Smart input state for each item
  const [itemInputs, setItemInputs] = useState<Record<string, string>>({});
  const [lastInputTime, setLastInputTime] = useState<Record<string, number>>({});

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    const handleQueueChange = (state: OfflineQueueState) => setPendingSync(state.pending);

    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueueChange);

    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueueChange);
    };
  }, []);

  // Data Query
  const { data, isLoading } = useQuery({
    queryKey: ['worker', 'tasks', id],
    queryFn: () => fetchTaskDetail(id ?? ''),
    enabled: Boolean(id),
    refetchInterval: 30000,
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
      message.error(error?.response?.data?.detail || 'Greška pri unosu količine');
    },
  });

  const shortageItems = useMemo(() => {
    if (!data) return [];
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
    if (!data) return [];
    return data.stavke.filter(
      (item) =>
        item.discrepancy_status === 'none' &&
        item.picked_qty > 0 &&
        item.picked_qty < item.kolicina_trazena
    );
  }, [data]);

  const untouchedItems = useMemo(() => {
    if (!data) return [];
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
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks', id] });
      navigate('/tasks');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška pri završavanju');
    },
  });

  const handleQuantityClick = (item: TaskItem) => {
    setSelectedItem(item);
    const remainingQty = Math.max(0, item.kolicina_trazena - item.picked_qty);
    setQuantity(remainingQty);
    setCloseItem(false);
    setReason(undefined);
    setNote('');
    setQuantityModalVisible(true);
  };

  // Smart input handler - detects scan vs manual
  const handleSmartInput = (item: TaskItem, value: string) => {
    setItemInputs(prev => ({ ...prev, [item.id]: value }));
    setLastInputTime(prev => ({ ...prev, [item.id]: Date.now() }));
  };

  const handleSmartInputSubmit = (item: TaskItem) => {
    const inputValue = itemInputs[item.id] || '';
    const inputTime = lastInputTime[item.id] || 0;
    const timeSinceStart = Date.now() - inputTime;

    if (!inputValue.trim()) {
      message.warning('Unesite vrijednost');
      return;
    }

    // Detect if it's a scan (fast input, typically < 100ms) or manual entry
    const isScan = timeSinceStart < 150 && inputValue.length > 5;

    if (isScan && item.barkod) {
      // Barcode scan detected
      const barcodeMatches = item.barkod === inputValue || 
                            item.artikl_sifra === inputValue ||
                            item.naziv.toLowerCase().includes(inputValue.toLowerCase());

      if (barcodeMatches) {
        // Barcode matches - proceed to quantity entry
        setSelectedItem(item);
        const remainingQty = Math.max(0, item.kolicina_trazena - item.picked_qty);
        setQuantity(remainingQty);
        setCloseItem(false);
        setReason(undefined);
        setNote('');
        setQuantityModalVisible(true);
        // Clear input
        setItemInputs(prev => ({ ...prev, [item.id]: '' }));
      } else {
        // Barcode doesn't match
        message.error(`Barkod ne odgovara artiklu: ${item.naziv}`);
        setItemInputs(prev => ({ ...prev, [item.id]: '' }));
      }
    } else {
      // Manual quantity entry
      const qty = parseFloat(inputValue);
      if (isNaN(qty) || qty < 0) {
        message.error('Unesite validnu količinu');
        return;
      }

      // Direct quantity entry
      setSelectedItem(item);
      setQuantity(qty);
      setCloseItem(false);
      setReason(undefined);
      setNote('');
      setQuantityModalVisible(true);
      // Clear input
      setItemInputs(prev => ({ ...prev, [item.id]: '' }));
    }
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
    const hasValidReason = Boolean(reason && typeof reason === 'string' && reason.trim().length > 0);
    
    if (reasonRequired && !hasValidReason) {
      // Show reason input modal instead of error
      setQuantity(confirmedQuantity);
      message.warning('Potrebno je unijeti razlog za manju količinu');
      return;
    }

    const operationId = `manual-${selectedItem.id}-${Date.now()}`;

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
      message.warning('Postoje stavke bez potvrđenog unosa.');
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
      navigate('/tasks');
    }

    setConfirmIncompleteChecked(false);
    setCompleteModalVisible(false);
  };

  if (isLoading || !data) {
    return (
      <div style={{ minHeight: '100vh', background: whiteTheme.colors.background, padding: whiteTheme.spacing.xl }}>
        <div className="wms-loading">Učitavanje zadatka...</div>
      </div>
    );
  }

  const allItemsProcessed = itemsNeedingAction === 0;
  const documentStatusTag = data.status === 'done'
    ? { color: 'success', label: 'Završen' }
    : data.status === 'in_progress'
      ? { color: 'warning', label: 'U toku' }
      : { color: 'processing', label: 'Dodijeljen' };

  const totalRequested = data.stavke.reduce((sum, item) => sum + item.kolicina_trazena, 0);
  const totalEntered = data.stavke.reduce((sum, item) => sum + item.picked_qty, 0);
  const overallProgressPercent = totalRequested ? Math.round((totalEntered / totalRequested) * 100) : 0;

  const formatNumber = (val: number) =>
    Number.isInteger(val) ? val.toString() : val.toLocaleString('sr-Latn-ME', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    });

  const reasonIsRequired = selectedItem
    ? quantity < selectedItem.kolicina_trazena || (closeItem && quantity === 0)
    : false;

  const quantityExtras = selectedItem ? (
    <div style={{ display: 'flex', flexDirection: 'column', gap: whiteTheme.spacing.sm }}>
      <div
        style={{
          padding: whiteTheme.spacing.md,
          background: whiteTheme.colors.panelBackground,
          borderRadius: whiteTheme.borderRadius.md,
          border: `1px solid ${whiteTheme.colors.border}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <div style={{ color: whiteTheme.colors.text, fontWeight: 600, fontSize: whiteTheme.typography.sizes.sm }}>Zatvori stavku</div>
          <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.xs }}>
            Završi stavku čak i ako je količina manja
          </div>
        </div>
        <Switch checked={closeItem} onChange={setCloseItem} />
      </div>

      <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.xs }}>
        Maksimalno: {formatNumber(selectedItem.kolicina_trazena)}
      </div>

      {(reasonIsRequired || reason) && (
        <div
          style={{
            padding: whiteTheme.spacing.lg,
            background: 'linear-gradient(135deg, #FFF4E6 0%, #FFEBE6 100%)',
            border: `2px solid ${whiteTheme.colors.warning}`,
            borderRadius: whiteTheme.borderRadius.lg,
            display: 'flex',
            flexDirection: 'column',
            gap: whiteTheme.spacing.md,
            boxShadow: '0 4px 12px rgba(255, 193, 7, 0.2)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.sm, marginBottom: whiteTheme.spacing.xs }}>
            <AlertTriangle size={20} color={whiteTheme.colors.warning} />
            <div style={{ color: whiteTheme.colors.text, fontWeight: 700, fontSize: whiteTheme.typography.sizes.md }}>
              ⚠️ Razlog je obavezan!
            </div>
          </div>
          <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.sm, marginBottom: whiteTheme.spacing.sm }}>
            Unesena količina ({formatNumber(quantity)}) je manja od tražene ({formatNumber(selectedItem.kolicina_trazena)}). Molimo odaberite razlog:
          </div>
          
          <Select
            value={reason}
            onChange={setReason}
            placeholder="🔍 Odaberite razlog..."
            size="large"
            style={{ 
              width: '100%',
              fontSize: whiteTheme.typography.sizes.md,
              height: '48px',
            }}
            options={[
              { value: 'Nije na stanju', label: '📦 Nije na stanju' },
              { value: 'Nije pronađeno', label: '🔍 Nije pronađeno' },
              { value: 'Oštećeno', label: '⚠️ Oštećeno' },
              { value: 'Pogrešan navod u dokumentu', label: '📋 Pogrešan navod u dokumentu' },
              { value: 'Drugo', label: '📝 Drugo' },
            ]}
          />
          
          <Input.TextArea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="💬 Dodatna napomena (opciono)..."
            rows={3}
            style={{
              fontSize: whiteTheme.typography.sizes.sm,
              resize: 'vertical',
            }}
          />
          
          {reason && (
            <div style={{
              background: 'rgba(255, 255, 255, 0.8)',
              padding: whiteTheme.spacing.sm,
              borderRadius: whiteTheme.borderRadius.sm,
              fontSize: whiteTheme.typography.sizes.xs,
              color: whiteTheme.colors.textSecondary,
              border: `1px solid ${whiteTheme.colors.border}`,
            }}>
              ✅ Razlog odabran: {reason}
            </div>
          )}
        </div>
      )}
    </div>
  ) : undefined;

  return (
    <div
      style={{
        minHeight: '100vh',
        background: whiteTheme.colors.background,
        paddingBottom: '140px',
      }}
    >
      {/* Page Title */}
      <div
        style={{
          padding: `${whiteTheme.spacing.lg} ${whiteTheme.spacing.lg} 0`,
          marginBottom: whiteTheme.spacing.lg,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
          <button
            onClick={() => navigate('/tasks')}
            style={{
              background: whiteTheme.colors.panelBackground,
              border: `1px solid ${whiteTheme.colors.border}`,
              borderRadius: whiteTheme.borderRadius.md,
              padding: whiteTheme.spacing.sm,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              color: whiteTheme.colors.text,
            }}
          >
            <ArrowLeft size={20} />
          </button>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: whiteTheme.typography.sizes.xl, fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text, margin: 0 }}>
              {data.dokument_broj}
            </h1>
            <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, marginTop: '4px' }}>
              {data.lokacija_naziv}
            </div>
          </div>
          <Tag color={documentStatusTag.color}>{documentStatusTag.label}</Tag>
        </div>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        {/* Enhanced Summary Card with Circular Progress */}
        <div
          className="wms-card"
          style={{
            marginBottom: whiteTheme.spacing.lg,
            padding: whiteTheme.spacing.xl,
            background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            border: `2px solid ${whiteTheme.colors.border}`,
            borderRadius: whiteTheme.borderRadius.lg,
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
          }}
        >
          {/* Header with Circular Progress */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: whiteTheme.spacing.xl }}>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.sm }}>
                <Target size={24} color={whiteTheme.colors.accent} />
                <h2 style={{ 
                  fontSize: whiteTheme.typography.sizes.lg, 
                  fontWeight: whiteTheme.typography.weights.bold, 
                  color: whiteTheme.colors.text, 
                  margin: 0 
                }}>
                  Napredak dokumenta
                </h2>
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                {data.stavke_completed} od {data.stavke_total} stavki završeno
              </div>
            </div>
            
            {/* Circular Progress */}
            <div style={{ position: 'relative', width: '120px', height: '120px' }}>
              <svg width="120" height="120" style={{ transform: 'rotate(-90deg)' }}>
                {/* Background circle */}
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  stroke={whiteTheme.colors.divider}
                  strokeWidth="8"
                  fill="none"
                />
                {/* Progress circle */}
                <circle
                  cx="60"
                  cy="60"
                  r="50"
                  stroke={overallProgressPercent === 100 ? whiteTheme.colors.success : whiteTheme.colors.accent}
                  strokeWidth="8"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${2 * Math.PI * 50}`}
                  strokeDashoffset={`${2 * Math.PI * 50 * (1 - overallProgressPercent / 100)}`}
                  style={{ transition: 'stroke-dashoffset 0.5s ease-in-out' }}
                />
              </svg>
              {/* Center text */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
              }}>
                <div style={{ 
                  fontSize: whiteTheme.typography.sizes['2xl'], 
                  fontWeight: whiteTheme.typography.weights.bold, 
                  color: overallProgressPercent === 100 ? whiteTheme.colors.success : whiteTheme.colors.accent,
                  lineHeight: 1
                }}>
                  {overallProgressPercent}%
                </div>
                <div style={{ 
                  fontSize: whiteTheme.typography.sizes.xs, 
                  color: whiteTheme.colors.textSecondary,
                  marginTop: '2px'
                }}>
                  Završeno
                </div>
              </div>
            </div>
          </div>

          {/* Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: whiteTheme.spacing.lg, marginBottom: whiteTheme.spacing.lg }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', marginBottom: whiteTheme.spacing.xs, fontWeight: 600 }}>
                Traženo
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes['3xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>
                {formatNumber(totalRequested)}
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                kom
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', marginBottom: whiteTheme.spacing.xs, fontWeight: 600 }}>
                Uneseno
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes['3xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.accent }}>
                {formatNumber(totalEntered)}
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                kom
              </div>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', marginBottom: whiteTheme.spacing.xs, fontWeight: 600 }}>
                Razlika
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes['3xl'], fontWeight: whiteTheme.typography.weights.bold, color: totalShortageQty > 0 ? whiteTheme.colors.error : whiteTheme.colors.success }}>
                {totalShortageQty > 0 ? `-${formatNumber(totalShortageQty)}` : '0'}
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                kom
              </div>
            </div>
          </div>

          {/* Linear Progress Bar */}
          <div style={{ marginBottom: whiteTheme.spacing.md }}>
            <Progress
              percent={overallProgressPercent}
              strokeColor={overallProgressPercent === 100 ? whiteTheme.colors.success : whiteTheme.colors.accent}
              trailColor={whiteTheme.colors.divider}
              strokeWidth={16}
              showInfo={false}
              style={{ marginBottom: whiteTheme.spacing.sm }}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                Ukupni napredak
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                {formatNumber(totalEntered)} / {formatNumber(totalRequested)} kom
              </div>
            </div>
          </div>

          {/* Warnings */}
          {partialItems > 0 && (
            <div
              style={{
                background: 'linear-gradient(135deg, #FFF4E6 0%, #FFEBE6 100%)',
                border: `2px solid ${whiteTheme.colors.warning}`,
                borderRadius: whiteTheme.borderRadius.md,
                padding: whiteTheme.spacing.lg,
                display: 'flex',
                alignItems: 'center',
                gap: whiteTheme.spacing.md,
                boxShadow: '0 2px 8px rgba(255, 193, 7, 0.15)',
              }}
            >
              <div style={{
                background: whiteTheme.colors.warning,
                borderRadius: '50%',
                padding: whiteTheme.spacing.sm,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>
                <AlertTriangle size={20} color="white" />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ color: whiteTheme.colors.text, fontWeight: 600, fontSize: whiteTheme.typography.sizes.md, marginBottom: '4px' }}>
                  ⚠️ Djelimično završeno: {partialItems} stavki
                </div>
                <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.sm }}>
                  Nedostaje: {formatNumber(totalShortageQty)} kom • Potrebno potvrditi razloge
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Items List */}
        {data.stavke.map((item) => {
          const isComplete = item.picked_qty >= item.kolicina_trazena;
          const hasShortage = item.discrepancy_status !== 'none' && item.missing_qty > 0;
          const progressPercent = item.kolicina_trazena
            ? Math.min((item.picked_qty / item.kolicina_trazena) * 100, 100)
            : 0;

          let statusColor = whiteTheme.colors.badge.new;
          let statusLabel = 'Novo';
          if (item.discrepancy_status === 'short_pick') {
            statusColor = whiteTheme.colors.badge.inProgress;
            statusLabel = 'Djelimično';
          } else if (item.discrepancy_status === 'not_found') {
            statusColor = whiteTheme.colors.badge.partial;
            statusLabel = 'Nije pronađeno';
          } else if (isComplete) {
            statusColor = whiteTheme.colors.badge.done;
            statusLabel = 'Zatvoreno';
          } else if (item.picked_qty > 0) {
            statusColor = whiteTheme.colors.badge.inProgress;
            statusLabel = 'U toku';
          }

          return (
            <div
              key={item.id}
              className="wms-card"
              style={{
                marginBottom: whiteTheme.spacing.lg,
                padding: whiteTheme.spacing.lg,
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                border: `2px solid ${hasShortage ? whiteTheme.colors.error : whiteTheme.colors.border}`,
                borderRadius: whiteTheme.borderRadius.lg,
                boxShadow: hasShortage 
                  ? '0 4px 20px rgba(239, 68, 68, 0.15)' 
                  : '0 2px 12px rgba(0, 0, 0, 0.05)',
                borderLeft: hasShortage ? `6px solid ${whiteTheme.colors.error}` : `6px solid ${isComplete ? whiteTheme.colors.success : whiteTheme.colors.accent}`,
              }}
            >
              {/* Item Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: whiteTheme.spacing.sm }}>
                <div style={{ flex: 1 }}>
                  <div style={{ color: whiteTheme.colors.text, fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold }}>
                    {item.naziv}
                  </div>
                  <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.sm, marginTop: '4px' }}>
                    Šifra: {item.artikl_sifra}
                  </div>
                </div>
                <div
                  style={{
                    background: statusColor,
                    padding: `${whiteTheme.spacing.xs} ${whiteTheme.spacing.md}`,
                    borderRadius: whiteTheme.borderRadius.full,
                    fontSize: whiteTheme.typography.sizes.xs,
                    fontWeight: whiteTheme.typography.weights.semibold,
                  }}
                >
                  {statusLabel}
                </div>
              </div>

              {/* Enhanced Quantity Grid */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr 1fr',
                  gap: whiteTheme.spacing.lg,
                  marginBottom: whiteTheme.spacing.lg,
                  padding: whiteTheme.spacing.lg,
                  background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                  borderRadius: whiteTheme.borderRadius.lg,
                  border: `1px solid ${whiteTheme.colors.border}`,
                }}
              >
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', fontWeight: 600, marginBottom: whiteTheme.spacing.xs }}>
                    📋 Traženo
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.text }}>
                    {formatNumber(item.kolicina_trazena)}
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                    kom
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', fontWeight: 600, marginBottom: whiteTheme.spacing.xs }}>
                    ✅ Uneseno
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: whiteTheme.colors.accent }}>
                    {formatNumber(item.picked_qty)}
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                    kom
                  </div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textTransform: 'uppercase', fontWeight: 600, marginBottom: whiteTheme.spacing.xs }}>
                    ⚖️ Razlika
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes['2xl'], fontWeight: whiteTheme.typography.weights.bold, color: item.missing_qty > 0 ? whiteTheme.colors.error : whiteTheme.colors.success }}>
                    {item.missing_qty > 0 ? `-${formatNumber(item.missing_qty)}` : '0'}
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary }}>
                    kom
                  </div>
                </div>
              </div>

              {/* Enhanced Progress Bar */}
              <div style={{ marginBottom: whiteTheme.spacing.lg }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: whiteTheme.spacing.sm }}>
                  <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, fontWeight: 600 }}>
                    📊 Napredak stavke
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                    {Math.round(progressPercent)}%
                  </div>
                </div>
                <Progress
                  percent={Math.min(progressPercent, 100)}
                  strokeColor={hasShortage ? whiteTheme.colors.warning : isComplete ? whiteTheme.colors.success : whiteTheme.colors.accent}
                  trailColor={whiteTheme.colors.divider}
                  showInfo={false}
                  strokeWidth={12}
                  style={{ marginBottom: whiteTheme.spacing.xs }}
                />
                <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, textAlign: 'center' }}>
                  {formatNumber(item.picked_qty)} / {formatNumber(item.kolicina_trazena)} kom
                </div>
              </div>

              {/* Discrepancy Reason */}
              {hasShortage && item.discrepancy_reason && (
                <div
                  style={{
                    background: '#FFEBE6',
                    padding: whiteTheme.spacing.sm,
                    borderRadius: whiteTheme.borderRadius.sm,
                    marginBottom: whiteTheme.spacing.sm,
                    fontSize: whiteTheme.typography.sizes.xs,
                    color: whiteTheme.colors.error,
                    fontWeight: whiteTheme.typography.weights.medium,
                  }}
                >
                  Razlog: {item.discrepancy_reason}
                </div>
              )}

              {/* Enhanced Smart Input - Auto-detects Scan or Manual */}
              {(!isComplete || item.discrepancy_status !== 'none') && (
                <div style={{ 
                  background: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
                  padding: whiteTheme.spacing.lg,
                  borderRadius: whiteTheme.borderRadius.lg,
                  border: `2px solid ${whiteTheme.colors.border}`,
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.sm, marginBottom: whiteTheme.spacing.sm }}>
                    {item.barkod ? (
                      <ScanBarcode size={20} color={whiteTheme.colors.accent} />
                    ) : (
                      <Edit3 size={20} color={whiteTheme.colors.accent} />
                    )}
                    <div style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: 600, color: whiteTheme.colors.text }}>
                      {item.barkod ? '📷 Skeniraj barkod ili unesi količinu' : '✏️ Unesi količinu'}
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', gap: whiteTheme.spacing.sm, alignItems: 'stretch' }}>
                    <div style={{ flex: 1, position: 'relative' }}>
                      <Input
                        size="large"
                        placeholder={item.barkod ? "Skeniraj barkod ili unesi količinu" : "Unesi količinu"}
                        value={itemInputs[item.id] || ''}
                        onChange={(e) => handleSmartInput(item, e.target.value)}
                        onPressEnter={() => handleSmartInputSubmit(item)}
                        prefix={item.barkod ? <ScanBarcode size={18} color={whiteTheme.colors.textSecondary} /> : <Edit3 size={18} color={whiteTheme.colors.textSecondary} />}
                        style={{
                          fontSize: whiteTheme.typography.sizes.md,
                          height: '56px',
                          borderRadius: whiteTheme.borderRadius.md,
                        }}
                      />
                      <div style={{ 
                        position: 'absolute',
                        right: '12px',
                        top: '50%',
                        transform: 'translateY(-50%)',
                        fontSize: whiteTheme.typography.sizes.xs,
                        color: whiteTheme.colors.textMuted,
                        pointerEvents: 'none',
                        background: 'rgba(255, 255, 255, 0.8)',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: 600,
                      }}>
                        Enter ↵
                      </div>
                    </div>
                    <button
                      onClick={() => handleQuantityClick(item)}
                      className="wms-btn"
                      style={{
                        background: 'linear-gradient(135deg, #0066CC 0%, #004499 100%)',
                        color: 'white',
                        border: 'none',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: whiteTheme.spacing.xs,
                        padding: `0 ${whiteTheme.spacing.lg}`,
                        minWidth: '56px',
                        height: '56px',
                        borderRadius: whiteTheme.borderRadius.md,
                        fontWeight: 600,
                        boxShadow: '0 2px 8px rgba(0, 102, 204, 0.3)',
                        transition: 'all 0.2s ease',
                      }}
                      title={t.tasks.enterQuantity}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-1px)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 102, 204, 0.4)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(0, 102, 204, 0.3)';
                      }}
                    >
                      <Edit3 size={20} />
                    </button>
                  </div>
                  
                  <div style={{ 
                    fontSize: whiteTheme.typography.sizes.xs, 
                    color: whiteTheme.colors.textSecondary, 
                    marginTop: whiteTheme.spacing.sm,
                    textAlign: 'center',
                    fontStyle: 'italic',
                  }}>
                    💡 {item.barkod ? 'Hardware scanner ili kamera će automatski detektovati barkod' : 'Unesite broj količine direktno'}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Sticky Footer */}
      <div
        style={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          padding: whiteTheme.spacing.lg,
          background: whiteTheme.colors.cardBackground,
          borderTop: `1px solid ${whiteTheme.colors.border}`,
          boxShadow: whiteTheme.shadows.lg,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: whiteTheme.spacing.md,
        }}
      >
        <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
          Završeno: {data.stavke_completed}/{data.stavke_total}
        </div>
        <div style={{ display: 'flex', gap: whiteTheme.spacing.sm }}>
          <button
            onClick={() => navigate('/tasks')}
            className="wms-btn wms-btn-secondary"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: whiteTheme.spacing.xs,
            }}
          >
            <Save size={16} /> Sačuvaj i izađi
          </button>
          <button
            onClick={handleCompleteClick}
            className="wms-btn wms-btn-success"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: whiteTheme.spacing.xs,
              opacity: allItemsProcessed ? 1 : 0.7,
            }}
          >
            <CheckCircle size={16} /> Završi dokument
          </button>
        </div>
      </div>

      {/* NumPad Modal */}
      <NumPad
        visible={quantityModalVisible}
        title={
          selectedItem
            ? `${selectedItem.naziv} — ${selectedItem.artikl_sifra}`
            : 'Unesite količinu'
        }
        defaultValue={quantity}
        maxValue={selectedItem?.kolicina_trazena}
        allowDecimal={true}
        confirmLabel="Sačuvaj"
        cancelLabel={t.common.cancel}
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
      >
        <div style={{ marginBottom: whiteTheme.spacing.lg }}>
          <div style={{ color: whiteTheme.colors.warning, fontSize: whiteTheme.typography.sizes.md, fontWeight: 600, marginBottom: whiteTheme.spacing.sm, display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.xs }}>
            <AlertCircle size={20} /> Dokument sadrži djelimične stavke
          </div>
          <div style={{ color: whiteTheme.colors.text, marginBottom: whiteTheme.spacing.xs }}>
            {partialItems} linija sa razlikom
          </div>
          <div style={{ color: whiteTheme.colors.textSecondary, fontSize: whiteTheme.typography.sizes.sm }}>
            Ukupna razlika: {formatNumber(totalShortageQty)} kom
          </div>
        </div>
        <Checkbox
          checked={confirmIncompleteChecked}
          onChange={(event) => setConfirmIncompleteChecked(event.target.checked)}
          style={{ marginBottom: whiteTheme.spacing.md }}
        >
          Potvrđujem djelimično završavanje
        </Checkbox>
        <div style={{ display: 'flex', gap: whiteTheme.spacing.sm }}>
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
            disabled={!confirmIncompleteChecked}
            style={{ flex: 1 }}
          >
            Završi sada
          </Button>
        </div>
      </Modal>

    </div>
  );
};

export default TaskDetailPageWhite;

