import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Button, Card, Drawer, Form, Input, message, Select, Space, Table, Tag, Typography, Switch, Tooltip } from "antd";
import { EditOutlined, DeleteOutlined, PlusOutlined, SearchOutlined } from "@ant-design/icons";
import { useState } from "react";
import client from "../api";
const { Title, Text } = Typography;
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
const fetchCatalogArticles = async (search, page = 1, size = 25) => {
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
const updateCatalogArticle = async (articleId, payload) => {
    const response = await client.patch(`/catalog/articles/${articleId}`, payload);
    return response.data;
};
const CatalogPage = () => {
    const queryClient = useQueryClient();
    const [selectedArticle, setSelectedArticle] = useState(null);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [searchText, setSearchText] = useState("");
    const [currentPage, setCurrentPage] = useState(1);
    const [form] = Form.useForm();
    const { data, isLoading } = useQuery({
        queryKey: ["catalog", "articles", searchText, currentPage],
        queryFn: () => fetchCatalogArticles(searchText, currentPage, 25)
    });
    const updateMutation = useMutation({
        mutationFn: ({ articleId, payload }) => updateCatalogArticle(articleId, payload),
        onSuccess: () => {
            message.success("Artikal uspešno ažuriran");
            queryClient.invalidateQueries({ queryKey: ["catalog", "articles"] });
            setDrawerOpen(false);
            setSelectedArticle(null);
            form.resetFields();
        },
        onError: (error) => {
            message.error(error?.response?.data?.detail ?? "Greška prilikom ažuriranja");
        }
    });
    const handleEdit = (article) => {
        setSelectedArticle(article);
        form.setFieldsValue({
            naziv: article.naziv,
            jedinica_mjere: article.jedinica_mjere,
            aktivan: article.aktivan,
            barkodovi: article.barkodovi
        });
        setDrawerOpen(true);
    };
    const handleSubmit = async (values) => {
        if (!selectedArticle)
            return;
        await updateMutation.mutateAsync({
            articleId: selectedArticle.id,
            payload: values
        });
    };
    const handleSearch = (value) => {
        setSearchText(value);
        setCurrentPage(1);
    };
    const columns = [
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
            render: (aktivan) => (_jsx(Tag, { color: aktivan ? "green" : "red", children: aktivan ? "Aktivan" : "Neaktivan" }))
        },
        {
            title: "Barkodovi",
            dataIndex: "barkodovi",
            key: "barkodovi",
            width: 150,
            render: (barkodovi) => (_jsx("div", { children: barkodovi.length > 0 ? (_jsx(Tooltip, { title: barkodovi.map((b) => b.value).join(", "), children: _jsxs(Tag, { color: "blue", children: [barkodovi.length, " barkod", barkodovi.length === 1 ? "" : "a"] }) })) : (_jsx(Tag, { color: "default", children: "Nema barkodova" })) }))
        },
        {
            title: "Akcije",
            key: "actions",
            width: 100,
            render: (_, record) => (_jsx(Space, { children: _jsx(Button, { type: "link", icon: _jsx(EditOutlined, {}), onClick: () => handleEdit(record), size: "small", children: "Uredi" }) }))
        }
    ];
    return (_jsxs(Card, { title: "Katalog artikala", extra: _jsxs(Space, { children: [_jsx(Input.Search, { placeholder: "Pretra\u017Ei artikle...", allowClear: true, onSearch: handleSearch, style: { width: 300 }, enterButton: _jsx(SearchOutlined, {}) }), _jsx(Button, { type: "primary", icon: _jsx(PlusOutlined, {}), onClick: () => queryClient.invalidateQueries({ queryKey: ["catalog", "articles"] }), children: "Osvje\u017Ei" })] }), children: [_jsx(Table, { rowKey: "id", columns: columns, dataSource: data?.items ?? [], loading: isLoading, pagination: {
                    current: currentPage,
                    total: data?.total ?? 0,
                    pageSize: 25,
                    showSizeChanger: false,
                    showQuickJumper: true,
                    showTotal: (total, range) => `${range[0]}-${range[1]} od ${total} artikala`,
                    onChange: (page) => setCurrentPage(page)
                }, scroll: { x: 800 } }), _jsx(Drawer, { title: `Uredi artikal: ${selectedArticle?.sifra}`, width: 600, open: drawerOpen, onClose: () => {
                    setDrawerOpen(false);
                    setSelectedArticle(null);
                    form.resetFields();
                }, destroyOnClose: true, children: selectedArticle && (_jsxs(Form, { layout: "vertical", form: form, onFinish: handleSubmit, initialValues: {
                        naziv: selectedArticle.naziv,
                        jedinica_mjere: selectedArticle.jedinica_mjere,
                        aktivan: selectedArticle.aktivan,
                        barkodovi: selectedArticle.barkodovi
                    }, children: [_jsx(Form.Item, { label: "\u0160ifra artikla", children: _jsx(Input, { value: selectedArticle.sifra, disabled: true }) }), _jsx(Form.Item, { label: "Naziv", name: "naziv", rules: [{ required: true, message: "Naziv je obavezan" }], children: _jsx(Input, { placeholder: "Unesite naziv artikla" }) }), _jsx(Form.Item, { label: "Jedinica mjere", name: "jedinica_mjere", rules: [{ required: true, message: "Jedinica mjere je obavezna" }], children: _jsx(Select, { options: JEDINICE_MJERE, placeholder: "Izaberite jedinicu mjere", showSearch: true, filterOption: (input, option) => (option?.label ?? '').toLowerCase().includes(input.toLowerCase()) }) }), _jsx(Form.Item, { label: "Status", name: "aktivan", valuePropName: "checked", children: _jsx(Switch, { checkedChildren: "Aktivan", unCheckedChildren: "Neaktivan" }) }), _jsx(Form.Item, { label: "Barkodovi", children: _jsx(Form.List, { name: "barkodovi", children: (fields, { add, remove }) => (_jsxs(_Fragment, { children: [fields.map(({ key, name, ...restField }) => (_jsxs(Space, { style: { display: 'flex', marginBottom: 8 }, align: "baseline", children: [_jsx(Form.Item, { ...restField, name: [name, 'value'], rules: [{ required: true, message: 'Barkod je obavezan' }], children: _jsx(Input, { placeholder: "Barkod" }) }), _jsx(Form.Item, { ...restField, name: [name, 'is_primary'], valuePropName: "checked", children: _jsx(Switch, { checkedChildren: "Primarni", unCheckedChildren: "Sekundarni" }) }), _jsx(Button, { type: "text", danger: true, icon: _jsx(DeleteOutlined, {}), onClick: () => remove(name) })] }, key))), _jsx(Form.Item, { children: _jsx(Button, { type: "dashed", onClick: () => add(), block: true, icon: _jsx(PlusOutlined, {}), children: "Dodaj barkod" }) })] })) }) }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: updateMutation.isPending, children: "Sa\u010Duvaj izmene" }), _jsx(Button, { onClick: () => {
                                            setDrawerOpen(false);
                                            setSelectedArticle(null);
                                            form.resetFields();
                                        }, children: "Otka\u017Ei" })] }) })] })) })] }));
};
export default CatalogPage;
