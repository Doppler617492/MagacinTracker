import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Card,
  DatePicker,
  Drawer,
  Form,
  message,
  Select,
  Space,
  Table,
  Tag
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type { TableRowSelection } from "antd/es/table/interface";
import dayjs from "dayjs";
import { useMemo, useState } from "react";
import client from "../api";

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

type TrebovanjeItemDetail = {
  id: string;
  artikl_sifra: string;
  naziv: string;
  kolicina_trazena: number;
  kolicina_uradjena: number;
  status: string;
};

type TrebovanjeDetail = {
  id: string;
  dokument_broj: string;
  datum: string;
  status: string;
  magacin: string;
  radnja: string;
  broj_stavki: number;
  stavke: TrebovanjeItemDetail[];
};

type AssignFormValues = {
  magacionerId: string;
  priority: string;
  dueAt?: dayjs.Dayjs;
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

const MAGACIONERI = [
  {
    value: "33333333-3333-3333-3333-333333333333",
    label: "Luka Magacioner"
  },
  {
    value: "44444444-4444-4444-4444-444444444444",
    label: "Miloš Magacioner"
  },
  {
    value: "55555555-5555-5555-5555-555555555555",
    label: "Jelena Magacioner"
  }
];

const PRIORITIES = [
  { value: "low", label: "Nizak" },
  { value: "normal", label: "Normalan" },
  { value: "high", label: "Visok" }
];

const fetchTrebovanja = async (): Promise<TrebovanjeListResponse> => {
  const response = await client.get("/trebovanja");
  return response.data;
};

const fetchTrebovanjeDetail = async (id: string): Promise<TrebovanjeDetail> => {
  const response = await client.get(`/trebovanja/${id}`);
  return response.data;
};

const TrebovanjaPage = () => {
  const queryClient = useQueryClient();
  const [selectedTrebovanjeId, setSelectedTrebovanjeId] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);
  const [form] = Form.useForm<AssignFormValues>();

  const { data, isLoading } = useQuery<TrebovanjeListResponse>({
    queryKey: ["trebovanja"],
    queryFn: fetchTrebovanja
  });

  const { data: detail, isFetching: isDetailLoading } = useQuery(
    {
      queryKey: ["trebovanje", selectedTrebovanjeId],
      queryFn: () => fetchTrebovanjeDetail(selectedTrebovanjeId as string),
      enabled: Boolean(selectedTrebovanjeId)
    }
  );

  const assignMutation = useMutation({
    mutationFn: async (payload: ZaduznicaCreatePayload) => {
      const response = await client.post("/zaduznice", payload);
      return response.data;
    },
    onSuccess: () => {
      message.success("Zadužnice kreirane");
      queryClient.invalidateQueries({ queryKey: ["trebovanje", selectedTrebovanjeId] });
      queryClient.invalidateQueries({ queryKey: ["trebovanja"] });
      setSelectedRowKeys([]);
      setDrawerOpen(false);
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška prilikom dodjele");
    }
  });

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
            setSelectedRowKeys([]);
          }}
        >
          Otvori
        </Button>
      )
    }
  ];

  const detailColumns: ColumnsType<TrebovanjeItemDetail & { remaining: number }> = [
    {
      title: "Šifra",
      dataIndex: "artikl_sifra"
    },
    {
      title: "Naziv",
      dataIndex: "naziv"
    },
    {
      title: "Traženo",
      dataIndex: "kolicina_trazena"
    },
    {
      title: "Obrađeno",
      dataIndex: "kolicina_uradjena"
    },
    {
      title: "Preostalo",
      dataIndex: "remaining"
    },
    {
      title: "Status",
      dataIndex: "status",
      render: (value: string) => <Tag color={statusColor[value] || "default"}>{value}</Tag>
    }
  ];

  const selectableItems = useMemo(() => {
    if (!detail) return [];
    return detail.stavke.map((item) => ({
      ...item,
      remaining: Math.max(item.kolicina_trazena - item.kolicina_uradjena, 0)
    }));
  }, [detail]);

  const rowSelection: TableRowSelection<any> = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    getCheckboxProps: (record) => ({ disabled: record.remaining <= 0 })
  };

  const handleAssign = async (values: AssignFormValues) => {
    if (!detail) return;
    if (selectedRowKeys.length === 0) {
      message.warning("Odaberite barem jednu stavku");
      return;
    }

    const items = selectableItems
      .filter((item) => selectedRowKeys.includes(item.id))
      .map((item) => ({
        trebovanje_stavka_id: item.id,
        quantity: item.remaining
      }));

    const payload = {
      trebovanje_id: detail.id,
      assignments: [
        {
          magacioner_id: values.magacionerId,
          priority: values.priority,
          due_at: values.dueAt ? values.dueAt.toISOString() : null,
          items
        }
      ]
    };

    await assignMutation.mutateAsync(payload);
    form.resetFields();
  };

  return (
    <Card title="Trebovanja" extra={<Button onClick={() => queryClient.invalidateQueries({ queryKey: ["trebovanja"] })}>Osvježi</Button>}>
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isLoading}
        pagination={{ total: data?.total ?? 0, pageSize: data?.page_size ?? 20 }}
      />

      <Drawer
        title={`Trebovanje ${detail?.dokument_broj ?? ""}`}
        width={700}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedTrebovanjeId(null);
          setSelectedRowKeys([]);
        }}
        destroyOnClose
      >
        <Space direction="vertical" style={{ width: "100%" }} size="large">
          <Table
            rowKey="id"
            columns={detailColumns}
            dataSource={selectableItems}
            loading={isDetailLoading}
            rowSelection={rowSelection}
            pagination={false}
            size="small"
          />

          <Form layout="vertical" form={form} onFinish={handleAssign}>
            <Form.Item
              label="Magacioner"
              name="magacionerId"
              rules={[{ required: true, message: "Odaberite magacionera" }]}
            >
              <Select options={MAGACIONERI} placeholder="Izaberite magacionera" />
            </Form.Item>
            <Form.Item label="Prioritet" name="priority" initialValue="normal">
              <Select options={PRIORITIES} />
            </Form.Item>
            <Form.Item label="Rok" name="dueAt">
              <DatePicker showTime format="YYYY-MM-DD HH:mm" style={{ width: "100%" }} />
            </Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={assignMutation.isPending} disabled={selectedRowKeys.length === 0}>
                Kreiraj zadužnicu
              </Button>
              <Button onClick={() => setSelectedRowKeys([])} disabled={selectedRowKeys.length === 0}>
                Poništi odabir
              </Button>
            </Space>
          </Form>
        </Space>
      </Drawer>
    </Card>
  );
};

export default TrebovanjaPage;
