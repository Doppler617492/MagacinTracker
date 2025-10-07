import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, message, Space, Tag } from "antd";
import { useParams } from "react-router-dom";
import client from "../api";
import { offlineQueue, networkManager } from "../lib/offlineQueue";

interface TaskItem {
  id: string;
  naziv: string;
  trazena_kolicina: number;
  obradjena_kolicina: number;
  status: string;
  needs_barcode: boolean;
}

interface TaskDetail {
  id: string;
  dokument: string;
  lokacija: string;
  stavke_total: number;
  progress: number;
  status: string;
  due_at?: string;
  stavke: TaskItem[];
}

const statusColor: Record<string, string> = {
  assigned: "blue",
  in_progress: "orange",
  done: "green"
};

const fetchTaskDetail = async (taskId: string): Promise<TaskDetail> => {
  const { data } = await client.get(`/worker/tasks/${taskId}`);
  return data;
};

const TaskDetailPage = () => {
  const { id } = useParams();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["worker", "tasks", id],
    queryFn: () => fetchTaskDetail(id ?? ""),
    enabled: Boolean(id)
  });

  const scanMutation = useMutation({
    mutationFn: async (payload: { taskItemId: string; barcode: string; quantity: number }) => {
      return client.post(`/worker/tasks/${payload.taskItemId}/scan`, {
        barcode: payload.barcode,
        quantity: payload.quantity
      });
    },
    onSuccess: () => {
      message.success("Skeniranje zabilježeno");
      queryClient.invalidateQueries({ queryKey: ["worker", "tasks", id] });
      queryClient.invalidateQueries({ queryKey: ["worker", "tasks"] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška pri skeniranju");
    }
  });

  const manualMutation = useMutation({
    mutationFn: async (payload: { taskItemId: string; quantity: number; reason: string }) => {
      return client.post(`/worker/tasks/${payload.taskItemId}/complete-manual`, {
        quantity: payload.quantity,
        reason: payload.reason
      });
    },
    onSuccess: () => {
      message.success("Ručno kompletiranje zabilježeno");
      queryClient.invalidateQueries({ queryKey: ["worker", "tasks", id] });
      queryClient.invalidateQueries({ queryKey: ["worker", "tasks"] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška pri ručnom kompletiranju");
    }
  });

  if (isLoading || !data) {
    return <p>Učitavanje zadatka...</p>;
  }

  const handleScan = (taskItemId: string) => {
    const barcode = window.prompt("Unesi bar-kod (ili ostavi prazno za test)", "test-barcode");
    if (barcode === null) return;
    const quantityInput = window.prompt("Unesi količinu", "1");
    if (!quantityInput) return;
    const quantity = Number(quantityInput);
    if (Number.isNaN(quantity) || quantity <= 0) {
      message.warning("Neispravna količina");
      return;
    }

    const payload = { barcode: barcode || "manual-scan", quantity };
    
    if (networkManager.isConnected()) {
      scanMutation.mutate({ taskItemId, ...payload });
    } else {
      offlineQueue.addAction('scan', taskItemId, payload);
      message.info("Offline - akcija dodana u queue");
    }
  };

  const handleManual = (taskItemId: string) => {
    const quantityInput = window.prompt("Unesi količinu za ručno potvrđivanje", "1");
    if (!quantityInput) return;
    const quantity = Number(quantityInput);
    if (Number.isNaN(quantity) || quantity <= 0) {
      message.warning("Neispravna količina");
      return;
    }
    const reason = window.prompt("Navedi razlog", "Oštećen barkod");
    if (!reason) {
      message.warning("Razlog je obavezan");
      return;
    }

    const payload = { quantity, reason };
    
    if (networkManager.isConnected()) {
      manualMutation.mutate({ taskItemId, ...payload });
    } else {
      offlineQueue.addAction('manual', taskItemId, payload);
      message.info("Offline - akcija dodana u queue");
    }
  };

  return (
    <div>
      <h1>{data.dokument}</h1>
      <p>
        <strong>Lokacija:</strong> {data.lokacija}
      </p>
      <p>
        <strong>Status:</strong> <Tag color={statusColor[data.status] || "default"}>{data.status}</Tag>
      </p>
      <p>
        <strong>Napredak:</strong> {Math.round(data.progress)}%
      </p>

      <div className="card">
        {data.stavke.map((item) => (
          <div key={item.id} style={{ marginBottom: 16, padding: 12, border: "1px solid #f0f0f0", borderRadius: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
              <strong>{item.naziv}</strong>
              {item.needs_barcode && (
                <Tag color="orange" style={{ fontSize: "10px" }}>
                  Potreban barkod
                </Tag>
              )}
            </div>
            <div>
              {item.obradjena_kolicina} / {item.trazena_kolicina}
            </div>
            <div style={{ marginTop: 8 }}>
              <Space>
                <Button 
                  size="small" 
                  type="primary" 
                  onClick={() => handleScan(item.id)} 
                  loading={scanMutation.isPending}
                  disabled={item.needs_barcode}
                >
                  Skeniraj bar-kod
                </Button>
                <Button
                  size="small"
                  onClick={() => handleManual(item.id)}
                  loading={manualMutation.isPending}
                >
                  Ručno potvrdi
                </Button>
              </Space>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TaskDetailPage;
