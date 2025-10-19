/**
 * ScanPickPage - Hybrid Barcode Scanning + Manual Entry for Tasks
 * 
 * Features:
 * - Optional barcode scanning (camera-based)
 * - Fallback to manual entry
 * - Match scanned barcode to task lines
 * - Disambiguation for multiple matches
 * - Offline queue support
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient, useMutation } from '@tanstack/react-query';
import { Button, message, Tag, Modal, Select } from 'antd';
import { ArrowLeftOutlined, ScanOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { theme } from '../theme';
import { t } from '../i18n/translations';
import HeaderStatusBar from '../components/HeaderStatusBar';
import BarcodeScanner from '../components/BarcodeScanner';
import NumPad from '../components/NumPad';
import client, { getStoredUserProfile, StoredUserProfile } from '../api';
import { offlineQueue, networkManager } from '../lib/offlineQueue';
import type { OfflineQueueState } from '../lib/offlineQueue';

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

const ScanPickPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isOnline, setIsOnline] = useState(networkManager.isConnected());
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? 'Warehouse'
  );

  // State
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [scannerVisible, setScannerVisible] = useState(false);
  const [scannedBarcode, setScannedBarcode] = useState<string | null>(null);
  const [matchedItems, setMatchedItems] = useState<TaskItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<TaskItem | null>(null);
  const [numPadVisible, setNumPadVisible] = useState(false);
  const [quantity, setQuantity] = useState<number>(0);

  // Network monitoring
  useEffect(() => {
    const handleNetworkChange = (online: boolean) => setIsOnline(online);
    const handleQueue = (state: OfflineQueueState) => {
      setPendingSync(state.pending);
      setLastSyncedAt(state.lastSyncedAt);
    };
    networkManager.addListener(handleNetworkChange);
    offlineQueue.addListener(handleQueue);
    return () => {
      networkManager.removeListener(handleNetworkChange);
      offlineQueue.removeListener(handleQueue);
    };
  }, []);

  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

  // Fetch tasks
  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['worker', 'tasks'],
    queryFn: fetchMyTasks,
    refetchInterval: isOnline ? 30000 : false,
  });

  // Fetch selected task detail
  const { data: taskDetail } = useQuery({
    queryKey: ['worker', 'tasks', selectedTaskId],
    queryFn: () => fetchTaskDetail(selectedTaskId!),
    enabled: !!selectedTaskId,
  });

  // Manual entry mutation
  const manualEntryMutation = useMutation({
    mutationFn: async (payload: {
      stavkaId: string;
      quantity: number;
      closeItem: boolean;
      operationId: string;
    }) => {
      return client.post(`/worker/tasks/${payload.stavkaId}/manual-entry`, {
        quantity: payload.quantity,
        close_item: payload.closeItem,
        operation_id: payload.operationId,
      });
    },
    onSuccess: () => {
      message.success('Quantity entered successfully!');
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks', selectedTaskId] });
      queryClient.invalidateQueries({ queryKey: ['worker', 'tasks'] });
      setNumPadVisible(false);
      setSelectedItem(null);
      setScannedBarcode(null);
      setMatchedItems([]);
      setScannerVisible(true); // Re-open scanner for next item
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail || 'Error entering quantity');
    },
  });

  const handleScan = (barcode: string) => {
    setScannerVisible(false);
    setScannedBarcode(barcode);

    if (!taskDetail || !taskDetail.stavke) {
      message.error('No active task selected');
      return;
    }

    // Match barcode to task items
    const matches = taskDetail.stavke.filter(
      (item: TaskItem) =>
        item.barkod === barcode ||
        item.artikl_sifra === barcode ||
        item.naziv.toLowerCase().includes(barcode.toLowerCase())
    );

    if (matches.length === 0) {
      // No match - show "Not in document" banner
      Modal.warning({
        title: 'Not in Document',
        content: (
          <div>
            <p>
              Barcode <strong>{barcode}</strong> does not match any item in the current task.
            </p>
            <p>Would you like to look it up in the catalog?</p>
          </div>
        ),
        okText: 'Lookup',
        cancelText: 'Scan Again',
        onOk: () => {
          navigate(`/lookup?barcode=${barcode}`);
        },
        onCancel: () => {
          setScannerVisible(true);
        },
      });
      return;
    }

    if (matches.length === 1) {
      // Single match - proceed to quantity entry
      handleItemSelected(matches[0]);
    } else {
      // Multiple matches - show disambiguation
      setMatchedItems(matches);
    }
  };

  const handleItemSelected = (item: TaskItem) => {
    setSelectedItem(item);
    setMatchedItems([]);
    const remaining = Math.max(0, item.kolicina_trazena - item.picked_qty);
    setQuantity(remaining);
    setNumPadVisible(true);
  };

  const handleQuantityConfirm = (confirmedQty: number) => {
    if (!selectedItem) return;

    const operationId = `scan-${selectedItem.id}-${Date.now()}`;

    if (networkManager.isConnected()) {
      manualEntryMutation.mutate({
        stavkaId: selectedItem.id,
        quantity: confirmedQty,
        closeItem: confirmedQty >= selectedItem.kolicina_trazena,
        operationId,
      });
    } else {
      offlineQueue.addAction('manual-entry', selectedItem.id, {
        quantity: confirmedQty,
        close_item: confirmedQty >= selectedItem.kolicina_trazena,
        operation_id: operationId,
      });
      message.info('Offline - action queued');
      setNumPadVisible(false);
      setSelectedItem(null);
      setScannerVisible(true);
    }
  };

  const displayRole = userProfile?.role
    ? userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)
    : 'Worker';

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

      <div style={{ flex: 1, padding: theme.spacing.lg }}>
        <div style={{ marginBottom: theme.spacing.lg }}>
          <button
            onClick={() => navigate('/')}
            style={{
              background: 'transparent',
              border: 'none',
              color: theme.colors.accent,
              fontSize: theme.typography.sizes.base,
              cursor: 'pointer',
              padding: theme.spacing.sm,
              display: 'flex',
              alignItems: 'center',
              gap: theme.spacing.xs,
            }}
          >
            <ArrowLeftOutlined /> Back
          </button>
        </div>

        <h1 style={{ color: theme.colors.text, fontSize: theme.typography.sizes['2xl'], margin: 0 }}>
          {t('home.scanPick')}
        </h1>

        {/* Task Selection */}
        {!selectedTaskId && (
          <div style={{ marginTop: theme.spacing.xl }}>
            <div
              style={{
                color: theme.colors.text,
                fontSize: theme.typography.sizes.lg,
                fontWeight: theme.typography.weights.semibold,
                marginBottom: theme.spacing.md,
              }}
            >
              Select a task to start scanning:
            </div>

            {tasksLoading ? (
              <div style={{ color: theme.colors.textSecondary, padding: theme.spacing.xl }}>
                {t('common.loading')}
              </div>
            ) : !tasks || tasks.length === 0 ? (
              <div
                style={{
                  textAlign: 'center',
                  padding: theme.spacing.xl,
                  color: theme.colors.textSecondary,
                  border: `1px dashed ${theme.colors.border}`,
                  borderRadius: theme.borderRadius.lg,
                }}
              >
                {t('common.noData')}
              </div>
            ) : (
              tasks
                .filter((task) => task.status !== 'done')
                .map((task) => (
                  <div
                    key={task.id}
                    onClick={() => {
                      setSelectedTaskId(task.id);
                      setTimeout(() => setScannerVisible(true), 300);
                    }}
                    style={{
                      background: theme.colors.cardBackground,
                      border: `1px solid ${theme.colors.border}`,
                      borderRadius: theme.borderRadius.lg,
                      padding: theme.spacing.md,
                      marginBottom: theme.spacing.md,
                      cursor: 'pointer',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                      }}
                    >
                      <div>
                        <div
                          style={{
                            color: theme.colors.text,
                            fontSize: theme.typography.sizes.md,
                            fontWeight: theme.typography.weights.semibold,
                          }}
                        >
                          {task.dokument}
                        </div>
                        <div
                          style={{
                            color: theme.colors.textSecondary,
                            fontSize: theme.typography.sizes.sm,
                            marginTop: theme.spacing.xs,
                          }}
                        >
                          {task.lokacija}
                        </div>
                      </div>
                      <Tag color={task.status === 'in_progress' ? 'orange' : 'blue'}>
                        {task.stavke_completed}/{task.stavke_total} items
                      </Tag>
                    </div>
                  </div>
                ))
            )}
          </div>
        )}

        {/* Active Scanning Session */}
        {selectedTaskId && taskDetail && (
          <div style={{ marginTop: theme.spacing.xl }}>
            <div
              style={{
                background: theme.colors.cardBackground,
                padding: theme.spacing.lg,
                borderRadius: theme.borderRadius.lg,
                border: `1px solid ${theme.colors.border}`,
                marginBottom: theme.spacing.lg,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <div>
                  <div
                    style={{
                      color: theme.colors.text,
                      fontSize: theme.typography.sizes.lg,
                      fontWeight: theme.typography.weights.semibold,
                    }}
                  >
                    {taskDetail.dokument_broj}
                  </div>
                  <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
                    {taskDetail.lokacija_naziv}
                  </div>
                </div>
                <Tag color="green">
                  {taskDetail.stavke_completed}/{taskDetail.stavke_total} items
                </Tag>
              </div>
            </div>

            <Button
              type="primary"
              size="large"
              icon={<ScanOutlined />}
              block
              onClick={() => setScannerVisible(true)}
              style={{ marginBottom: theme.spacing.lg }}
            >
              Start Scanning
            </Button>

            <Button
              size="large"
              block
              onClick={() => {
                setSelectedTaskId(null);
                setScannedBarcode(null);
                setMatchedItems([]);
              }}
            >
              Change Task
            </Button>
          </div>
        )}

        {/* Disambiguation Modal */}
        <Modal
          open={matchedItems.length > 1}
          title="Multiple Matches"
          onCancel={() => {
            setMatchedItems([]);
            setScannerVisible(true);
          }}
          footer={null}
          styles={{ body: { background: theme.colors.background } }}
        >
          <div style={{ marginBottom: theme.spacing.md }}>
            <div style={{ color: theme.colors.text, marginBottom: theme.spacing.sm }}>
              Barcode <strong>{scannedBarcode}</strong> matches multiple items. Select one:
            </div>
          </div>

          {matchedItems.map((item) => (
            <div
              key={item.id}
              onClick={() => handleItemSelected(item)}
              style={{
                background: theme.colors.cardBackground,
                padding: theme.spacing.md,
                borderRadius: theme.borderRadius.md,
                border: `1px solid ${theme.colors.border}`,
                marginBottom: theme.spacing.sm,
                cursor: 'pointer',
              }}
            >
              <div style={{ color: theme.colors.text, fontWeight: 600 }}>{item.naziv}</div>
              <div style={{ color: theme.colors.textSecondary, fontSize: theme.typography.sizes.sm }}>
                {item.artikl_sifra} • Requested: {item.kolicina_trazena}
              </div>
            </div>
          ))}
        </Modal>

        {/* Barcode Scanner */}
        <BarcodeScanner
          visible={scannerVisible}
          onScan={handleScan}
          onCancel={() => setScannerVisible(false)}
          title="Scan Item Barcode"
        />

        {/* Quantity Entry */}
        <NumPad
          visible={numPadVisible}
          title={selectedItem ? `${selectedItem.naziv} - ${selectedItem.artikl_sifra}` : 'Enter Quantity'}
          defaultValue={quantity}
          maxValue={selectedItem?.kolicina_trazena}
          allowDecimal={true}
          confirmLabel={t('common.confirm')}
          cancelLabel={t('common.cancel')}
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

export default ScanPickPage;

