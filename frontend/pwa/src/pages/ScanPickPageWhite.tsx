/**
 * ScanPickPage - White Enterprise Theme
 * Barcode scanning for picking tasks
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Button, message, Modal, Input, Tag, Progress } from 'antd';
import { ArrowLeft, ScanBarcode, CheckCircle, Package, AlertCircle } from 'lucide-react';
import { whiteTheme } from '../theme-white';
import BarcodeScanner from '../components/BarcodeScanner';
import NumPad from '../components/NumPad';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';
import { useTranslation } from '../hooks/useTranslation';

interface TaskItem {
  id: string;
  naziv: string;
  artikl_sifra: string;
  kolicina_trazena: number;
  picked_qty: number;
  missing_qty: number;
  discrepancy_status: string;
  barkod?: string;
}

interface TaskSummary {
  id: string;
  dokument: string;
  lokacija: string;
  stavke_total: number;
  stavke_completed: number;
  status: string;
}

const fetchMyTasks = async (): Promise<TaskSummary[]> => {
  const { data } = await client.get('/worker/tasks');
  return data;
};

const fetchTaskDetail = async (taskId: string) => {
  const { data } = await client.get(`/worker/tasks/${taskId}`);
  return data;
};

const ScanPickPageWhite: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const t = useTranslation('sr');
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);

  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [scannerVisible, setScannerVisible] = useState(false);
  const [scannedBarcode, setScannedBarcode] = useState<string | null>(null);
  const [matchedItems, setMatchedItems] = useState<TaskItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<TaskItem | null>(null);
  const [numPadVisible, setNumPadVisible] = useState(false);
  const [quantity, setQuantity] = useState<number>(0);

  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    const handleQueue = (state: OfflineQueueState) => setPendingSync(state.pending);
    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueue);
    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueue);
    };
  }, []);

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['worker', 'tasks'],
    queryFn: fetchMyTasks,
    refetchInterval: isOnline ? 30000 : false,
  });

  const { data: taskDetail } = useQuery({
    queryKey: ['worker', 'tasks', selectedTaskId],
    queryFn: () => fetchTaskDetail(selectedTaskId!),
    enabled: !!selectedTaskId,
  });

  const manualEntryMutation = useMutation({
    mutationFn: async (payload: any) => {
      return client.post(`/worker/tasks/${payload.stavkaId}/manual-entry`, payload);
    },
    onSuccess: () => {
      message.success('Quantity entered!');
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      setNumPadVisible(false);
      setSelectedItem(null);
      setScannerVisible(true);
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Error');
    },
  });

  const handleScan = (barcode: string) => {
    setScannerVisible(false);
    setScannedBarcode(barcode);

    if (!taskDetail || !taskDetail.stavke) {
      message.error('No task selected');
      return;
    }

    const matches = taskDetail.stavke.filter(
      (item: TaskItem) =>
        item.barkod === barcode ||
        item.artikl_sifra === barcode ||
        item.naziv.toLowerCase().includes(barcode.toLowerCase())
    );

    if (matches.length === 0) {
      Modal.warning({
        title: 'Not in Document',
        content: `Barcode ${barcode} not found in current task.`,
        okText: 'Lookup',
        cancelText: 'Scan Again',
        onOk: () => navigate(`/lookup?barcode=${barcode}`),
        onCancel: () => setScannerVisible(true),
      });
      return;
    }

    if (matches.length === 1) {
      handleItemSelected(matches[0]);
    } else {
      setMatchedItems(matches);
    }
  };

  const handleItemSelected = (item: TaskItem) => {
    setSelectedItem(item);
    setMatchedItems([]);
    setQuantity(Math.max(0, item.kolicina_trazena - item.picked_qty));
    setNumPadVisible(true);
  };

  const handleQuantityConfirm = (confirmedQty: number) => {
    if (!selectedItem) return;

    const operationId = `scan-${selectedItem.id}-${Date.now()}`;
    const payload = {
      stavkaId: selectedItem.id,
      quantity: confirmedQty,
      close_item: confirmedQty >= selectedItem.kolicina_trazena,
      operation_id: operationId,
    };

    if (networkManager.isConnected()) {
      manualEntryMutation.mutate(payload);
    } else {
      offlineQueue.addAction('manual-entry', selectedItem.id, payload);
      message.info('Offline - queued');
      setNumPadVisible(false);
      setScannerVisible(true);
    }
  };

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
          Scan & Pick
        </h1>
      </div>

      <div style={{ padding: whiteTheme.spacing.lg }}>
        {!selectedTaskId ? (
          <div>
            <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
                <ScanBarcode size={24} color={whiteTheme.colors.accent} />
                <div>
                  <h2 style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                    Select Task to Scan
                  </h2>
                  <p style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, margin: 0 }}>
                    Choose a task to start barcode scanning
                  </p>
                </div>
              </div>
            </div>

            {tasksLoading ? (
              <div className="wms-loading">Loading tasks...</div>
            ) : !tasks || tasks.length === 0 ? (
              <div className="wms-empty">
                <div className="wms-empty-icon"><Package size={48} /></div>
                <div className="wms-empty-text">No tasks available</div>
                <div className="wms-empty-description">All tasks are completed or no tasks assigned</div>
              </div>
            ) : (
              tasks.filter((task) => task.status !== 'done').map((task) => (
                <div
                  key={task.id}
                  onClick={() => {
                    setSelectedTaskId(task.id);
                    setTimeout(() => setScannerVisible(true), 300);
                  }}
                  className="wms-card"
                  style={{
                    marginBottom: whiteTheme.spacing.md,
                    cursor: 'pointer',
                    border: `2px solid ${whiteTheme.colors.border}`,
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <div style={{ fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                        {task.dokument}
                      </div>
                      <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                        {task.lokacija}
                      </div>
                    </div>
                    <div
                      style={{
                        background: whiteTheme.colors.primaryLight,
                        color: whiteTheme.colors.primary,
                        padding: `${whiteTheme.spacing.xs} ${whiteTheme.spacing.md}`,
                        borderRadius: whiteTheme.borderRadius.full,
                        fontSize: whiteTheme.typography.sizes.xs,
                        fontWeight: whiteTheme.typography.weights.semibold,
                      }}
                    >
                      {task.stavke_completed}/{task.stavke_total}
                    </div>
                  </div>
                  <div style={{ marginTop: whiteTheme.spacing.sm }}>
                    <Progress
                      percent={Math.round((task.stavke_completed / task.stavke_total) * 100)}
                      strokeColor={whiteTheme.colors.accent}
                      trailColor={whiteTheme.colors.divider}
                      showInfo={false}
                      strokeWidth={8}
                    />
                  </div>
                </div>
              ))
            )}
          </div>
        ) : (
          <div>
            {taskDetail && (
              <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: whiteTheme.spacing.md }}>
                  <div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.lg, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text }}>
                      {taskDetail.dokument_broj}
                    </div>
                    <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                      {taskDetail.lokacija_naziv}
                    </div>
                  </div>
                  <Tag color="processing">{taskDetail.status}</Tag>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                    Progress: {taskDetail.stavke_completed}/{taskDetail.stavke_total} items
                  </div>
                  <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                    {Math.round((taskDetail.stavke_completed / taskDetail.stavke_total) * 100)}% complete
                  </div>
                </div>
              </div>
            )}

            <div className="wms-card" style={{ marginBottom: whiteTheme.spacing.lg }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
                <ScanBarcode size={24} color={whiteTheme.colors.accent} />
                <div>
                  <h3 style={{ fontSize: whiteTheme.typography.sizes.md, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                    Ready to Scan
                  </h3>
                  <p style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary, margin: 0 }}>
                    Scan item barcodes to pick quantities
                  </p>
                </div>
              </div>
              
              <Button
                type="primary"
                size="large"
                icon={<ScanBarcode size={20} />}
                block
                onClick={() => setScannerVisible(true)}
                style={{ marginBottom: whiteTheme.spacing.md }}
              >
                Start Scanning
              </Button>

              <Button size="large" block onClick={() => setSelectedTaskId(null)}>
                Change Task
              </Button>
            </div>

            {/* Instructions */}
            <div className="wms-card">
              <div style={{ display: 'flex', alignItems: 'center', gap: whiteTheme.spacing.md, marginBottom: whiteTheme.spacing.md }}>
                <AlertCircle size={20} color={whiteTheme.colors.info} />
                <h4 style={{ fontSize: whiteTheme.typography.sizes.sm, fontWeight: whiteTheme.typography.weights.semibold, color: whiteTheme.colors.text, margin: 0 }}>
                  How to Use Scan & Pick
                </h4>
              </div>
              <div style={{ fontSize: whiteTheme.typography.sizes.xs, color: whiteTheme.colors.textSecondary, lineHeight: 1.6 }}>
                <p>1. <strong>Scan barcode</strong> of item you want to pick</p>
                <p>2. <strong>Enter quantity</strong> found/available</p>
                <p>3. <strong>Confirm</strong> to update task progress</p>
                <p>4. <strong>Repeat</strong> for all items in task</p>
                <p>5. <strong>Complete task</strong> when finished</p>
              </div>
            </div>
          </div>
        )}

        <Modal
          open={matchedItems.length > 1}
          title="Multiple Matches"
          onCancel={() => {
            setMatchedItems([]);
            setScannerVisible(true);
          }}
          footer={null}
        >
          <div style={{ marginBottom: whiteTheme.spacing.md }}>
            Barcode <strong>{scannedBarcode}</strong> matches multiple items:
          </div>
          {matchedItems.map((item) => (
            <div
              key={item.id}
              onClick={() => handleItemSelected(item)}
              className="wms-card"
              style={{
                marginBottom: whiteTheme.spacing.sm,
                cursor: 'pointer',
              }}
            >
              <div style={{ fontWeight: 600 }}>{item.naziv}</div>
              <div style={{ fontSize: whiteTheme.typography.sizes.sm, color: whiteTheme.colors.textSecondary }}>
                {item.artikl_sifra} • Requested: {item.kolicina_trazena}
              </div>
            </div>
          ))}
        </Modal>

        <BarcodeScanner
          visible={scannerVisible}
          onScan={handleScan}
          onCancel={() => setScannerVisible(false)}
          title="Scan Item Barcode"
        />

        <NumPad
          visible={numPadVisible}
          title={selectedItem ? `${selectedItem.naziv} - ${selectedItem.artikl_sifra}` : 'Enter Quantity'}
          defaultValue={quantity}
          maxValue={selectedItem?.kolicina_trazena}
          allowDecimal={true}
          confirmLabel="Confirm"
          cancelLabel="Cancel"
          confirmLoading={manualEntryMutation.isPending}
          onCancel={() => {
            setNumPadVisible(false);
            setScannerVisible(true);
          }}
          onValueChange={(val) => setQuantity(val)}
          onConfirm={handleQuantityConfirm}
        />
      </div>
    </div>
  );
};

export default ScanPickPageWhite;