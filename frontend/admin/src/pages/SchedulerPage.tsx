import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Card,
  Drawer,
  Form,
  message,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Alert,
  Divider
} from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import client, { getSchedulerSuggestion, cancelSchedulerSuggestion } from "../api";

const { Title, Text } = Typography;

type TrebovanjeListItem = {
  id: string;
  dokument_broj: string;
  datum: string;
  magacin: string;
  radnja: string;
  status: string;
  broj_stavki: number;
  ukupno_trazena: number;
  ukupno_uradjena: number;
};

type TrebovanjeListResponse = {
  items: TrebovanjeListItem[];
  total: number;
  page: number;
  page_size: number;
};

type SchedulerSuggestion = {
  log_id: string;
  trebovanje_id: string;
  magacioner_id: string;
  score: number;
  reason: string;
  lock_expires_at: string | null;
  cached: boolean;
};

type ZaduznicaItemPayload = {
  trebovanje_stavka_id: string;
  quantity: number;
};

type ZaduznicaAssignmentPayload = {
  magacioner_id: string;
  priority: string;
  due_at: string | null;
  items: ZaduznicaItemPayload[];
};

type ZaduznicaCreatePayload = {
  trebovanje_id: string;
  assignments: ZaduznicaAssignmentPayload[];
};

const statusColor: Record<string, string> = {
  new: "blue",
  assigned: "purple",
  in_progress: "orange",
  done: "green",
  failed: "red"
};

// MAGACIONERI will be fetched dynamically from API

const PRIORITIES = [
  { value: "low", label: "Nizak" },
  { value: "normal", label: "Normalan" },
  { value: "high", label: "Visok" }
];

const fetchTrebovanja = async (): Promise<TrebovanjeListResponse> => {
  const response = await client.get("/trebovanja");
  return response.data;
};

const fetchTrebovanjeDetail = async (id: string) => {
  const response = await client.get(`/trebovanja/${id}`);
  return response.data;
};

const SchedulerPage = () => {
  const queryClient = useQueryClient();
  const [selectedTrebovanjeId, setSelectedTrebovanjeId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [suggestion, setSuggestion] = useState<SchedulerSuggestion | null>(null);
  const [overrideMode, setOverrideMode] = useState(false);

  const { data, isLoading } = useQuery<TrebovanjeListResponse>({
    queryKey: ["trebovanja"],
    queryFn: fetchTrebovanja,
    refetchInterval: 15000, // Refetch every 15 seconds to see worker updates
  });

  // Fetch selected trebovanje details
  const { data: trebovanjeDetail, isFetching: isLoadingDetail } = useQuery({
    queryKey: ["trebovanje", selectedTrebovanjeId],
    queryFn: () => fetchTrebovanjeDetail(selectedTrebovanjeId!),
    enabled: !!selectedTrebovanjeId
  });

  // Fetch magacioneri dynamically
  const { data: usersData } = useQuery({
    queryKey: ["users", "magacioner"],
    queryFn: async () => {
      const response = await client.get("/admin/users?role_filter=magacioner&active_filter=true&per_page=100");
      console.log("🔍 Scheduler Page - Fetched users:", response.data);
      return response.data;
    },
    staleTime: 0, // Always refetch
    gcTime: 0 // Don't cache
  });

  const MAGACIONERI = useMemo(() => {
    if (!usersData?.users) return [];
    const result = usersData.users.map((user: any) => ({
      value: user.id,
      label: `${user.first_name} ${user.last_name}`
    }));
    console.log("🔍 Scheduler Page - MAGACIONERI list:", result);
    return result;
  }, [usersData]);

  const suggestionMutation = useMutation({
    mutationFn: getSchedulerSuggestion,
    onSuccess: (data: SchedulerSuggestion) => {
      setSuggestion(data);
      setOverrideMode(false);
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška prilikom dobijanja predloga");
    }
  });

  const assignMutation = useMutation({
    mutationFn: async (payload: ZaduznicaCreatePayload) => {
      const response = await client.post("/zaduznice", payload);
      return response.data;
    },
    onSuccess: () => {
      message.success("Zadužnice kreirane");
      queryClient.invalidateQueries({ queryKey: ["trebovanja"] });
      setDrawerOpen(false);
      setSuggestion(null);
      setOverrideMode(false);
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška prilikom kreiranja zadužnica");
    }
  });

  const cancelSuggestionMutation = useMutation({
    mutationFn: cancelSchedulerSuggestion,
    onSuccess: () => {
      message.success("Zadužnica poništena");
      setSuggestion(null);
      setOverrideMode(false);
      queryClient.invalidateQueries({ queryKey: ["trebovanja"] });
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška prilikom poništavanja zadužnice");
    }
  });

  const handleGetSuggestion = async () => {
    if (!selectedTrebovanjeId) return;
    await suggestionMutation.mutateAsync(selectedTrebovanjeId);
  };

  const handleCancelSuggestion = async () => {
    if (!selectedTrebovanjeId) return;
    await cancelSuggestionMutation.mutateAsync(selectedTrebovanjeId);
  };

  const handleAcceptSuggestion = async () => {
    if (!suggestion || !selectedTrebovanjeId || !trebovanjeDetail) return;

    // Collect all items with remaining quantity
    const items = trebovanjeDetail.stavke
      .filter((item: any) => item.kolicina_trazena > item.kolicina_uradjena)
      .map((item: any) => ({
        trebovanje_stavka_id: item.id,
        quantity: item.kolicina_trazena - item.kolicina_uradjena
      }));

    if (items.length === 0) {
      message.error("Nema preostalih stavki za dodjelu");
      return;
    }

    const payload: ZaduznicaCreatePayload = {
      trebovanje_id: selectedTrebovanjeId,
      assignments: [
        {
          magacioner_id: suggestion.magacioner_id,
          priority: "normal",
          due_at: null,
          items
        }
      ]
    };

    await assignMutation.mutateAsync(payload);
  };

  const handleOverrideAssignment = async (values: any) => {
    if (!selectedTrebovanjeId || !trebovanjeDetail) return;

    // Collect all items with remaining quantity
    const items = trebovanjeDetail.stavke
      .filter((item: any) => item.kolicina_trazena > item.kolicina_uradjena)
      .map((item: any) => ({
        trebovanje_stavka_id: item.id,
        quantity: item.kolicina_trazena - item.kolicina_uradjena
      }));

    if (items.length === 0) {
      message.error("Nema preostalih stavki za dodjelu");
      return;
    }

    const dueAtValue = values.dueAt;
    let dueAtIso: string | null = null;

    if (dueAtValue) {
      if (typeof dueAtValue === "string") {
        const durationHours: Record<string, number> = {
          "1h": 1,
          "2h": 2,
          "4h": 4,
          "8h": 8
        };
        const hours = durationHours[dueAtValue];
        dueAtIso = hours ? dayjs().add(hours, "hour").toISOString() : null;
      } else if (dayjs.isDayjs(dueAtValue)) {
        dueAtIso = dueAtValue.toISOString();
      } else if (dueAtValue instanceof Date) {
        dueAtIso = dueAtValue.toISOString();
      }
    }

    const payload: ZaduznicaCreatePayload = {
      trebovanje_id: selectedTrebovanjeId,
      assignments: [
        {
          magacioner_id: values.magacionerId,
          priority: values.priority,
          due_at: dueAtIso,
          items
        }
      ]
    };

    await assignMutation.mutateAsync(payload);
  };

  const columns: ColumnsType<TrebovanjeListItem> = [
    {
      title: "Dokument",
      dataIndex: "dokument_broj"
    },
    {
      title: "Datum",
      dataIndex: "datum"
    },
    {
      title: "Magacin",
      dataIndex: "magacin"
    },
    {
      title: "Radnja",
      dataIndex: "radnja"
    },
    {
      title: "Status",
      dataIndex: "status",
      render: (value: string) => <Tag color={statusColor[value] || "default"}>{value}</Tag>
    },
    {
      title: "Akcije",
      dataIndex: "id",
      render: (value: string) => (
        <Button
          type="link"
          onClick={() => {
            setSelectedTrebovanjeId(value);
            setDrawerOpen(true);
            setSuggestion(null);
            setOverrideMode(false);
          }}
        >
          Otvori
        </Button>
      )
    }
  ];

  const selectedTrebovanje = useMemo(() => {
    if (!data || !selectedTrebovanjeId) return null;
    return data.items.find(item => item.id === selectedTrebovanjeId);
  }, [data, selectedTrebovanjeId]);

  return (
    <Card title="Scheduler - Prihvati/Prepiši" extra={<Button onClick={() => queryClient.invalidateQueries({ queryKey: ["trebovanja"] })}>Osvježi</Button>}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isLoading}
        pagination={{ total: data?.total ?? 0, pageSize: data?.page_size ?? 20 }}
      />

      <Drawer
        title={`Scheduler - ${selectedTrebovanje?.dokument_broj ?? ""}`}
        width={600}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedTrebovanjeId(null);
          setSuggestion(null);
          setOverrideMode(false);
        }}
        destroyOnClose
      >
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          {selectedTrebovanje && (
            <Card size="small">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Text><strong>Dokument:</strong> {selectedTrebovanje.dokument_broj}</Text>
                <Text><strong>Magacin:</strong> {selectedTrebovanje.magacin}</Text>
                <Text><strong>Radnja:</strong> {selectedTrebovanje.radnja}</Text>
                <Text><strong>Status:</strong> <Tag color={statusColor[selectedTrebovanje.status] || "default"}>{selectedTrebovanje.status}</Tag></Text>
              </Space>
            </Card>
          )}

          {!suggestion && !overrideMode && (
            <Space>
              <Button 
                type="primary" 
                onClick={handleGetSuggestion}
                loading={suggestionMutation.isPending}
              >
                Dobij predlog od scheduler-a
              </Button>
              <Button onClick={() => setOverrideMode(true)}>
                Ručno dodeli
              </Button>
              <Button
                danger
                onClick={handleCancelSuggestion}
                loading={cancelSuggestionMutation.isPending}
                disabled={!selectedTrebovanjeId}
              >
                Poništi zadužnicu
              </Button>
            </Space>
          )}

          {suggestion && !overrideMode && (
            <Card title="Predlog scheduler-a" size="small">
              <Space direction="vertical" style={{ width: "100%" }}>
                <Alert
                  message={`Predloženi magacioner: ${MAGACIONERI.find(m => m.value === suggestion.magacioner_id)?.label || suggestion.magacioner_id}`}
                  description={`Score: ${suggestion.score.toFixed(2)} | Razlog: ${suggestion.reason}`}
                  type="info"
                  showIcon
                />
                {suggestion.cached && (
                  <Alert
                    message="Predlog je iz cache-a"
                    type="warning"
                    showIcon
                  />
                )}
                {suggestion.lock_expires_at && (
                  <Alert
                    message={`Lock ističe: ${new Date(suggestion.lock_expires_at).toLocaleString()}`}
                    type="warning"
                    showIcon
                  />
                )}
                <Divider />
                <Space>
                  <Button 
                    type="primary" 
                    onClick={handleAcceptSuggestion}
                    loading={assignMutation.isPending}
                  >
                    Prihvati predlog
                  </Button>
                  <Button onClick={() => setOverrideMode(true)}>
                    Prepiši ručno
                  </Button>
                  <Button
                    danger
                    onClick={handleCancelSuggestion}
                    loading={cancelSuggestionMutation.isPending}
                  >
                    Poništi zadužnicu
                  </Button>
                  <Button
                    onClick={async () => {
                      await handleCancelSuggestion();
                      await handleGetSuggestion();
                    }}
                    loading={suggestionMutation.isPending || cancelSuggestionMutation.isPending}
                  >
                    Novi predlog
                  </Button>
                </Space>
              </Space>
            </Card>
          )}

          {overrideMode && (
            <Card title="Ručno dodeljivanje" size="small">
              <Form
                layout="vertical"
                onFinish={handleOverrideAssignment}
                initialValues={{ priority: "normal" }}
              >
                <Form.Item
                  label="Magacioner"
                  name="magacionerId"
                  rules={[{ required: true, message: "Odaberite magacionera" }]}
                >
                  <Select options={MAGACIONERI} placeholder="Izaberite magacionera" />
                </Form.Item>
                <Form.Item label="Prioritet" name="priority">
                  <Select options={PRIORITIES} />
                </Form.Item>
                <Form.Item label="Rok" name="dueAt">
                  <Select placeholder="Ostavite prazno za bez roka">
                    <Select.Option value={null}>Bez roka</Select.Option>
                    <Select.Option value="1h">1 sat</Select.Option>
                    <Select.Option value="2h">2 sata</Select.Option>
                    <Select.Option value="4h">4 sata</Select.Option>
                    <Select.Option value="8h">8 sati</Select.Option>
                  </Select>
                </Form.Item>
                <Space>
                  <Button type="primary" htmlType="submit" loading={assignMutation.isPending}>
                    Kreiraj zadužnicu
                  </Button>
                  <Button onClick={() => setOverrideMode(false)}>
                    Nazad
                  </Button>
                </Space>
              </Form>
            </Card>
          )}
        </Space>
      </Drawer>
    </Card>
  );
};

export default SchedulerPage;
