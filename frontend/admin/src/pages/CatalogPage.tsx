import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Button,
  Card,
  Drawer,
  Form,
  Input,
  message,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  Switch,
  Popconfirm,
  Tooltip
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { EditOutlined, DeleteOutlined, PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { useMemo, useState } from "react";
import client from "../api";

const { Title, Text } = Typography;

interface CatalogBarcode {
  value: string;
  is_primary?: boolean;
}

interface CatalogArticle {
  id: string;
  sifra: string;
  naziv: string;
  jedinica_mjere: string;
  aktivan: boolean;
  barkodovi: CatalogBarcode[];
}

interface CatalogListResponse {
  items: CatalogArticle[];
  total: number;
  page: number;
  page_size: number;
}

interface CatalogUpdatePayload {
  naziv?: string;
  jedinica_mjere?: string;
  aktivan?: boolean;
  barkodovi?: CatalogBarcode[];
}

const JEDINICE_MJERE = [
  { value: "kom", label: "Komad" },
  { value: "kg", label: "Kilogram" },
  { value: "l", label: "Litar" },
  { value: "m", label: "Metar" },
  { value: "m2", label: "Kvadratni metar" },
  { value: "m3", label: "Kubni metar" },
  { value: "pak", label: "Pakovanje" },
  { value: "set", label: "Set" }
];

const fetchCatalogArticles = async (search?: string, page = 1, size = 25): Promise<CatalogListResponse> => {
  const params = new URLSearchParams({
    page: page.toString(),
    size: size.toString()
  });
  if (search) {
    params.append('search', search);
  }
  
  const response = await client.get(`/catalog/articles?${params.toString()}`);
  return response.data;
};

const updateCatalogArticle = async (articleId: string, payload: CatalogUpdatePayload) => {
  const response = await client.patch(`/catalog/articles/${articleId}`, payload);
  return response.data;
};

const CatalogPage = () => {
  const queryClient = useQueryClient();
  const [selectedArticle, setSelectedArticle] = useState<CatalogArticle | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [searchText, setSearchText] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [form] = Form.useForm<CatalogUpdatePayload>();

  const { data, isLoading } = useQuery<CatalogListResponse>({
    queryKey: ["catalog", "articles", searchText, currentPage],
    queryFn: () => fetchCatalogArticles(searchText, currentPage, 25)
  });

  const updateMutation = useMutation({
    mutationFn: ({ articleId, payload }: { articleId: string; payload: CatalogUpdatePayload }) =>
      updateCatalogArticle(articleId, payload),
    onSuccess: () => {
      message.success("Artikal uspešno ažuriran");
      queryClient.invalidateQueries({ queryKey: ["catalog", "articles"] });
      setDrawerOpen(false);
      setSelectedArticle(null);
      form.resetFields();
    },
    onError: (error: any) => {
      message.error(error?.response?.data?.detail ?? "Greška prilikom ažuriranja");
    }
  });

  const handleEdit = (article: CatalogArticle) => {
    setSelectedArticle(article);
    form.setFieldsValue({
      naziv: article.naziv,
      jedinica_mjere: article.jedinica_mjere,
      aktivan: article.aktivan,
      barkodovi: article.barkodovi
    });
    setDrawerOpen(true);
  };

  const handleSubmit = async (values: CatalogUpdatePayload) => {
    if (!selectedArticle) return;
    
    await updateMutation.mutateAsync({
      articleId: selectedArticle.id,
      payload: values
    });
  };

  const handleSearch = (value: string) => {
    setSearchText(value);
    setCurrentPage(1);
  };

  const columns: ColumnsType<CatalogArticle> = [
    {
      title: "Šifra",
      dataIndex: "sifra",
      key: "sifra",
      width: 120,
      fixed: "left"
    },
    {
      title: "Naziv",
      dataIndex: "naziv",
      key: "naziv",
      ellipsis: true
    },
    {
      title: "Jedinica mjere",
      dataIndex: "jedinica_mjere",
      key: "jedinica_mjere",
      width: 120
    },
    {
      title: "Status",
      dataIndex: "aktivan",
      key: "aktivan",
      width: 100,
      render: (aktivan: boolean) => (
        <Tag color={aktivan ? "green" : "red"}>
          {aktivan ? "Aktivan" : "Neaktivan"}
        </Tag>
      )
    },
    {
      title: "Barkodovi",
      dataIndex: "barkodovi",
      key: "barkodovi",
      width: 150,
      render: (barkodovi: CatalogBarcode[]) => (
        <div>
          {barkodovi.length > 0 ? (
            <Tooltip title={barkodovi.map((b) => b.value).join(", ")}>
              <Tag color="blue">
                {barkodovi.length} barkod
                {barkodovi.length === 1 ? "" : "a"}
              </Tag>
            </Tooltip>
          ) : (
            <Tag color="default">Nema barkodova</Tag>
          )}
        </div>
      )
    },
    {
      title: "Akcije",
      key: "actions",
      width: 100,
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            Uredi
          </Button>
        </Space>
      )
    }
  ];

  return (
    <Card 
      title="Katalog artikala" 
      extra={
        <Space>
          <Input.Search
            placeholder="Pretraži artikle..."
            allowClear
            onSearch={handleSearch}
            style={{ width: 300 }}
            enterButton={<SearchOutlined />}
          />
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => queryClient.invalidateQueries({ queryKey: ["catalog", "articles"] })}
          >
            Osvježi
          </Button>
        </Space>
      }
    >
      <Table
        rowKey="id"
        columns={columns}
        dataSource={data?.items ?? []}
        loading={isLoading}
        pagination={{
          current: currentPage,
          total: data?.total ?? 0,
          pageSize: 25,
          showSizeChanger: false,
          showQuickJumper: true,
          showTotal: (total, range) => `${range[0]}-${range[1]} od ${total} artikala`,
          onChange: (page) => setCurrentPage(page)
        }}
        scroll={{ x: 800 }}
      />

      <Drawer
        title={`Uredi artikal: ${selectedArticle?.sifra}`}
        width={600}
        open={drawerOpen}
        onClose={() => {
          setDrawerOpen(false);
          setSelectedArticle(null);
          form.resetFields();
        }}
        destroyOnClose
      >
        {selectedArticle && (
          <Form
            layout="vertical"
            form={form}
            onFinish={handleSubmit}
            initialValues={{
              naziv: selectedArticle.naziv,
              jedinica_mjere: selectedArticle.jedinica_mjere,
              aktivan: selectedArticle.aktivan,
              barkodovi: selectedArticle.barkodovi
            }}
          >
            <Form.Item label="Šifra artikla">
              <Input value={selectedArticle.sifra} disabled />
            </Form.Item>

            <Form.Item
              label="Naziv"
              name="naziv"
              rules={[{ required: true, message: "Naziv je obavezan" }]}
            >
              <Input placeholder="Unesite naziv artikla" />
            </Form.Item>

            <Form.Item
              label="Jedinica mjere"
              name="jedinica_mjere"
              rules={[{ required: true, message: "Jedinica mjere je obavezna" }]}
            >
              <Select 
                options={JEDINICE_MJERE} 
                placeholder="Izaberite jedinicu mjere"
                showSearch
                filterOption={(input, option) =>
                  (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
                }
              />
            </Form.Item>

            <Form.Item
              label="Status"
              name="aktivan"
              valuePropName="checked"
            >
              <Switch 
                checkedChildren="Aktivan" 
                unCheckedChildren="Neaktivan"
              />
            </Form.Item>

            <Form.Item label="Barkodovi">
              <Form.List name="barkodovi">
                {(fields, { add, remove }) => (
                  <>
                    {fields.map(({ key, name, ...restField }) => (
                      <Space key={key} style={{ display: 'flex', marginBottom: 8 }} align="baseline">
                        <Form.Item
                          {...restField}
                          name={[name, 'value']}
                          rules={[{ required: true, message: 'Barkod je obavezan' }]}
                        >
                          <Input placeholder="Barkod" />
                        </Form.Item>
                        <Form.Item
                          {...restField}
                          name={[name, 'is_primary']}
                          valuePropName="checked"
                        >
                          <Switch checkedChildren="Primarni" unCheckedChildren="Sekundarni" />
                        </Form.Item>
                        <Button 
                          type="text" 
                          danger 
                          icon={<DeleteOutlined />} 
                          onClick={() => remove(name)}
                        />
                      </Space>
                    ))}
                    <Form.Item>
                      <Button 
                        type="dashed" 
                        onClick={() => add()} 
                        block 
                        icon={<PlusOutlined />}
                      >
                        Dodaj barkod
                      </Button>
                    </Form.Item>
                  </>
                )}
              </Form.List>
            </Form.Item>

            <Form.Item>
              <Space>
                <Button 
                  type="primary" 
                  htmlType="submit" 
                  loading={updateMutation.isPending}
                >
                  Sačuvaj izmene
                </Button>
                <Button onClick={() => {
                  setDrawerOpen(false);
                  setSelectedArticle(null);
                  form.resetFields();
                }}>
                  Otkaži
                </Button>
              </Space>
            </Form.Item>
          </Form>
        )}
      </Drawer>
    </Card>
  );
};

export default CatalogPage;
