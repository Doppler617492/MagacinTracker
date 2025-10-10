/**
 * TaskDetailPage - Worker task detail view with shortage tracking
 * 
 * Features:
 * - Barcode/SKU scanning
 * - NumPad for quantity entry
 * - Short-pick recording
 * - Not-found marking
 * - Document completion with shortage confirmation
 */

import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button, message, Space, Tag, Modal, Input, Select, Progress, Divider } from 'antd';
import {
  BarcodeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  EditOutlined,
  ExclamationCircleOutlined,
  ScanOutlined,
  WarningOutlined,
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api';
import NumPad from '../components/NumPad';
import { theme } from '../theme';
import { offlineQueue, networkManager } from '../lib/offlineQueue';

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
  lokacija_naziv: string;
  stavke_total: number;
  stavke_completed: number;
  progress: number;
  status: string;
  due_at?: string;
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

  // UI State
  const [scanModalVisible, setScanModalVisible] = useState(false);
  const [numPadVisible, setNumPadVisible] = useState(false);
  const [shortageModalVisible, setShortageModalVisible] = useState(false);
  const [completeModalVisible, setCompleteModalVisible] = useState(false);
  
  const [selectedItem, setSelectedItem] = useState<TaskItem | null>(null);
  const [scanCode, setScanCode] = useState('');
  const [shortageReason, setShortageReason] = useState<string>('');
  const [shortageType, setShortageType] = useState<'short_pick' | 'not_found'>('short_pick');

  // Data Query
  const { data, isLoading } = useQuery({
    queryKey: ['worker', 'tasks', id],
    queryFn: () => fetchTaskDetail(id ?? ''),
    enabled: Boolean(id),
    refetchInterval: 30000, // Refetch every 30s
  });

  // Pick by Code Mutation
  const pickByCodeMutation = useMutation({
    mutationFn: async (payload: { stavkaId: string; code: string; quantity: number; operationId: string }) => {
      return client.post(`/worker/tasks/${payload.stavkaId}/pick-by-code`, {
        code: payload.code,
        quantity: payload.quantity,
        operation_id: payload.operationId,
      });
    },
    onSuccess: () => {
      message.success('Stavka uspješno skenirana!');
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks', id] });
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      setScanModalVisible(false);
      setScanCode('');
    },
    onError: (error: any) => {
      const errorMsg = error?.response?.data?.detail || 'Greška pri skeniranju';
      message.error(errorMsg);
    },
  });

  // Short Pick Mutation
  const shortPickMutation = useMutation({
    mutationFn: async (payload: { stavkaId: string; actualQty: number; reason?: string; operationId: string }) => {
      return client.post(`/worker/tasks/${payload.stavkaId}/short-pick`, {
        actual_qty: payload.actualQty,
        reason: payload.reason,
        operation_id: payload.operationId,
      });
    },
    onSuccess: () => {
      message.success('Manjak evidentiran');
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks', id] });
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      setShortageModalVisible(false);
      setShortageReason('');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška');
    },
  });

  // Not Found Mutation
  const notFoundMutation = useMutation({
    mutationFn: async (payload: { stavkaId: string; reason?: string; operationId: string }) => {
      return client.post(`/worker/tasks/${payload.stavkaId}/not-found`, {
        reason: payload.reason,
        operation_id: payload.operationId,
      });
    },
    onSuccess: () => {
      message.success('Stavka označena kao nedostupna');
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks', id] });
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      setShortageModalVisible(false);
      setShortageReason('');
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Greška');
    },
  });

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
  const handleScanClick = (item: TaskItem) => {
    setSelectedItem(item);
    setScanModalVisible(true);
  };

  const handleScanSubmit = () => {
    if (!selectedItem || !scanCode.trim()) {
      message.warning('Unesite kod');
      return;
    }

    // Open NumPad for quantity
    setScanModalVisible(false);
    setNumPadVisible(true);
  };

  const handleQuantityConfirm = (quantity: number) => {
    if (!selectedItem) return;

    const operationId = `pick-${selectedItem.id}-${Date.now()}`;
    
    if (networkManager.isConnected()) {
      pickByCodeMutation.mutate({
        stavkaId: selectedItem.id,
        code: scanCode,
        quantity,
        operationId,
      });
    } else {
      offlineQueue.addAction('pick-by-code', selectedItem.id, { code: scanCode, quantity, operation_id: operationId });
      message.info('Offline - akcija dodana u red');
      setScanCode('');
    }

    setNumPadVisible(false);
  };

  const handleShortageClick = (item: TaskItem) => {
    setSelectedItem(item);
    setShortageType('short_pick');
    setShortageModalVisible(true);
  };

  const handleNotFoundClick = (item: TaskItem) => {
    setSelectedItem(item);
    setShortageType('not_found');
    setShortageModalVisible(true);
  };

  const handleShortageConfirm = (quantity?: number) => {
    if (!selectedItem) return;

    const operationId = `shortage-${selectedItem.id}-${Date.now()}`;

    if (shortageType === 'not_found') {
      if (networkManager.isConnected()) {
        notFoundMutation.mutate({
          stavkaId: selectedItem.id,
          reason: shortageReason || undefined,
          operationId,
        });
      } else {
        offlineQueue.addAction('not-found', selectedItem.id, { reason: shortageReason, operation_id: operationId });
        message.info('Offline - akcija dodana u red');
        setShortageModalVisible(false);
      }
    } else if (quantity !== undefined) {
      if (networkManager.isConnected()) {
        shortPickMutation.mutate({
          stavkaId: selectedItem.id,
          actualQty: quantity,
          reason: shortageReason || undefined,
          operationId,
        });
      } else {
        offlineQueue.addAction('short-pick', selectedItem.id, {
          actual_qty: quantity,
          reason: shortageReason,
          operation_id: operationId,
        });
        message.info('Offline - akcija dodana u red');
        setShortageModalVisible(false);
      }
    }
  };

  const handleCompleteClick = () => {
    if (!data) return;

    const itemsWithShortages = data.stavke.filter(
      item => item.discrepancy_status !== 'none' || item.missing_qty > 0
    ).length;

    if (itemsWithShortages > 0) {
      setCompleteModalVisible(true);
    } else {
      handleCompleteConfirm(false);
    }
  };

  const handleCompleteConfirm = (confirmIncomplete: boolean) => {
    if (!data) return;

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

    setCompleteModalVisible(false);
  };

  if (isLoading || !data) {
    return (
      <div style={{ padding: theme.spacing.lg, textAlign: 'center' }}>
        <p style={{ color: theme.colors.text }}>Učitavanje zadatka...</p>
      </div>
    );
  }

  const itemsWithShortages = data.stavke.filter(
    item => item.discrepancy_status !== 'none' || item.missing_qty > 0
  ).length;

  const allItemsProcessed = data.stavke.every(
    item => item.picked_qty >= item.kolicina_trazena || item.discrepancy_status !== 'none'
  );

  return (
    <div style={{ padding: theme.spacing.md, paddingBottom: '100px' }}>
      {/* Header */}
      <div style={{ marginBottom: theme.spacing.lg }}>
        <h1 style={{ color: theme.colors.text, fontSize: theme.typography.sizes.xl, margin: 0 }}>
          {data.dokument_broj}
        </h1>
        <p style={{ color: theme.colors.textSecondary, margin: `${theme.spacing.xs} 0` }}>
          <strong>Lokacija:</strong> {data.lokacija_naziv}
        </p>
        <Tag color={data.status === 'done' ? 'green' : data.status === 'in_progress' ? 'orange' : 'blue'}>
          {data.status === 'assigned' && 'Dodijeljen'}
          {data.status === 'in_progress' && 'U toku'}
          {data.status === 'done' && 'Završen'}
        </Tag>
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
          <span style={{ color: theme.colors.text, fontSize: theme.typography.sizes.sm, fontWeight: 600 }}>
            {data.stavke_completed} / {data.stavke_total} stavki
          </span>
        </div>
        <Progress
          percent={Math.round(data.progress)}
          strokeColor={theme.colors.accent}
          trailColor={theme.colors.neutral}
          strokeWidth={12}
        />
      </div>

      {/* Shortage Warning */}
      {itemsWithShortages > 0 && (
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
              {itemsWithShortages} {itemsWithShortages === 1 ? 'stavka' : 'stavke'} sa manjkom
            </div>
            <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
              Dokumentuj razlog prije završetka
            </div>
          </div>
        </div>
      )}

      {/* Items List */}
      <div style={{ marginBottom: theme.spacing.lg }}>
        {data.stavke.map((item, index) => {
          const isComplete = item.picked_qty >= item.kolicina_trazena;
          const hasShortage = item.discrepancy_status !== 'none' || item.missing_qty > 0;
          const progressPercent = (item.picked_qty / item.kolicina_trazena) * 100;

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
                    SKU: {item.artikl_sifra}
                  </div>
                </div>
                <div>
                  {isComplete && <CheckCircleOutlined style={{ color: theme.colors.success, fontSize: '24px' }} />}
                  {hasShortage && !isComplete && <ExclamationCircleOutlined style={{ color: theme.colors.warning, fontSize: '24px' }} />}
                </div>
              </div>

              {/* Progress Bar */}
              <div style={{ marginBottom: theme.spacing.sm }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: theme.typography.sizes.sm, marginBottom: '4px' }}>
                  <span style={{ color: theme.colors.textSecondary }}>Prikupljeno</span>
                  <span style={{ color: theme.colors.text, fontWeight: 600 }}>
                    {item.picked_qty} / {item.kolicina_trazena}
                  </span>
                </div>
                <Progress
                  percent={Math.min(progressPercent, 100)}
                  strokeColor={hasShortage ? theme.colors.warning : theme.colors.accent}
                  trailColor={theme.colors.neutral}
                  showInfo={false}
                  strokeWidth={8}
                />
              </div>

              {/* Discrepancy Info */}
              {hasShortage && (
                <div
                  style={{
                    background: theme.colors.background,
                    padding: theme.spacing.sm,
                    borderRadius: theme.borderRadius.sm,
                    marginBottom: theme.spacing.sm,
                  }}
                >
                  <div style={{ color: theme.colors.warning, fontSize: theme.typography.sizes.sm, fontWeight: 600 }}>
                    Status: {item.discrepancy_status === 'short_pick' && 'Djelimično prikupljeno'}
                    {item.discrepancy_status === 'not_found' && 'Nije pronađeno'}
                    {item.discrepancy_status === 'damaged' && 'Oštećeno'}
                  </div>
                  {item.discrepancy_reason && (
                    <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs, marginTop: '2px' }}>
                      Razlog: {item.discrepancy_reason}
                    </div>
                  )}
                  {item.missing_qty > 0 && (
                    <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.xs, marginTop: '2px' }}>
                      Nedostaje: {item.missing_qty}
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              {!isComplete && item.discrepancy_status === 'none' && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: theme.spacing.sm }}>
                  <button
                    onClick={() => handleScanClick(item)}
                    style={{
                      background: theme.colors.primary,
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: theme.borderRadius.sm,
                      padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                      fontSize: theme.typography.sizes.sm,
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: theme.spacing.xs,
                    }}
                  >
                    <BarcodeOutlined /> Skeniraj
                  </button>
                  <button
                    onClick={() => handleShortageClick(item)}
                    style={{
                      background: theme.colors.neutral,
                      color: theme.colors.text,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: theme.borderRadius.sm,
                      padding: `${theme.spacing.sm} ${theme.spacing.md}`,
                      fontSize: theme.typography.sizes.sm,
                      fontWeight: 600,
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: theme.spacing.xs,
                    }}
                  >
                    <EditOutlined /> Djelimično
                  </button>
                </div>
              )}
              {!isComplete && item.discrepancy_status === 'none' && (
                <button
                  onClick={() => handleNotFoundClick(item)}
                  style={{
                    width: '100%',
                    background: theme.colors.background,
                    color: theme.colors.textSecondary,
                    border: `1px solid ${theme.colors.border}`,
                    borderRadius: theme.borderRadius.sm,
                    padding: `${theme.spacing.xs} ${theme.spacing.md}`,
                    fontSize: theme.typography.sizes.sm,
                    cursor: 'pointer',
                    marginTop: theme.spacing.sm,
                  }}
                >
                  <CloseCircleOutlined /> Nije pronađeno
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Complete Button */}
      <div
        style={{
          position: 'fixed',
          bottom: '70px',
          left: 0,
          right: 0,
          padding: theme.spacing.md,
          background: theme.colors.background,
          borderTop: `1px solid ${theme.colors.border}`,
        }}
      >
        <button
          onClick={handleCompleteClick}
          disabled={!allItemsProcessed}
          style={{
            width: '100%',
            background: allItemsProcessed ? theme.colors.success : theme.colors.neutral,
            color: allItemsProcessed ? '#ffffff' : theme.colors.textSecondary,
            border: 'none',
            borderRadius: theme.borderRadius.sm,
            padding: `${theme.spacing.md} ${theme.spacing.lg}`,
            fontSize: theme.typography.sizes.md,
            fontWeight: 600,
            cursor: allItemsProcessed ? 'pointer' : 'not-allowed',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: theme.spacing.sm,
          }}
        >
          <CheckCircleOutlined /> Završi dokument
        </button>
      </div>

      {/* Scan Modal */}
      <Modal
        open={scanModalVisible}
        title="Skeniraj barkod ili unesi SKU"
        onCancel={() => {
          setScanModalVisible(false);
          setScanCode('');
        }}
        footer={null}
        styles={{ body: { background: theme.colors.background } }}
      >
        <div style={{ marginBottom: theme.spacing.md }}>
          <div style={{ color: theme.colors.text, marginBottom: theme.spacing.sm }}>
            Artikal: <strong>{selectedItem?.naziv}</strong>
          </div>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            SKU: {selectedItem?.artikl_sifra}
          </div>
        </div>
        <Input
          placeholder="Skeniraj barkod ili unesi SKU"
          value={scanCode}
          onChange={(e) => setScanCode(e.target.value)}
          onPressEnter={handleScanSubmit}
          prefix={<ScanOutlined />}
          size="large"
          autoFocus
        />
        <Button
          type="primary"
          block
          size="large"
          onClick={handleScanSubmit}
          style={{ marginTop: theme.spacing.md }}
        >
          Nastavi
        </Button>
      </Modal>

      {/* NumPad Modal */}
      <NumPad
        visible={numPadVisible}
        title={`Količina za: ${selectedItem?.naziv}`}
        defaultValue={selectedItem ? selectedItem.kolicina_trazena - selectedItem.picked_qty : 1}
        maxValue={selectedItem ? selectedItem.kolicina_trazena - selectedItem.picked_qty : undefined}
        onConfirm={handleQuantityConfirm}
        onCancel={() => {
          setNumPadVisible(false);
          setScanModalVisible(true);
        }}
      />

      {/* Shortage Modal */}
      <Modal
        open={shortageModalVisible}
        title={shortageType === 'not_found' ? 'Označi kao nije pronađeno' : 'Djelimično prikupljanje'}
        onCancel={() => {
          setShortageModalVisible(false);
          setShortageReason('');
        }}
        footer={null}
        styles={{ body: { background: theme.colors.background } }}
      >
        <div style={{ marginBottom: theme.spacing.md }}>
          <div style={{ color: theme.colors.text, marginBottom: theme.spacing.sm }}>
            Artikal: <strong>{selectedItem?.naziv}</strong>
          </div>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Traženo: {selectedItem?.kolicina_trazena}
          </div>
        </div>

        {shortageType === 'short_pick' && (
          <Button
            block
            size="large"
            onClick={() => {
              setShortageModalVisible(false);
              setNumPadVisible(true);
            }}
            style={{ marginBottom: theme.spacing.md }}
          >
            Unesi prikupljenu količinu
          </Button>
        )}

        <Select
          placeholder="Odaberi razlog (opciono)"
          value={shortageReason || undefined}
          onChange={setShortageReason}
          style={{ width: '100%', marginBottom: theme.spacing.md }}
          size="large"
          options={[
            { value: 'Nema na lokaciji', label: 'Nema na lokaciji' },
            { value: 'Oštećeno', label: 'Oštećeno' },
            { value: 'Pogrešna lokacija', label: 'Pogrešna lokacija' },
            { value: 'Nedovoljno zaliha', label: 'Nedovoljno zaliha' },
            { value: 'Ostalo', label: 'Ostalo' },
          ]}
        />

        {shortageType === 'not_found' && (
          <Button
            type="primary"
            danger
            block
            size="large"
            onClick={() => handleShortageConfirm()}
            loading={notFoundMutation.isPending}
          >
            Potvrdi - nije pronađeno
          </Button>
        )}
      </Modal>

      {/* Complete Confirmation Modal */}
      <Modal
        open={completeModalVisible}
        title="Potvrdi završetak"
        onCancel={() => setCompleteModalVisible(false)}
        footer={null}
        styles={{ body: { background: theme.colors.background } }}
      >
        <div style={{ marginBottom: theme.spacing.lg }}>
          <div style={{ color: theme.colors.warning, fontSize: theme.typography.sizes.md, fontWeight: 600, marginBottom: theme.spacing.sm }}>
            <ExclamationCircleOutlined /> Dokument ima {itemsWithShortages} {itemsWithShortages === 1 ? 'stavku' : 'stavke'} sa manjkom
          </div>
          <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
            Da li želite završiti dokument sa evidentiranim manjkovima?
          </div>
        </div>
        <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
          <Button onClick={() => setCompleteModalVisible(false)}>Otkaži</Button>
          <Button
            type="primary"
            onClick={() => handleCompleteConfirm(true)}
            loading={completeMutation.isPending}
          >
            Potvrdi završetak
          </Button>
        </Space>
      </Modal>
    </div>
  );
};

export default TaskDetailPage;
