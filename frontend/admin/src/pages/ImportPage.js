import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button, Card, Upload, message, Typography, Alert, Space, Progress, List, Tag } from "antd";
import { InboxOutlined, UploadOutlined, FileExcelOutlined, FileTextOutlined } from "@ant-design/icons";
import client from "../api";
const { Title, Text, Paragraph } = Typography;
const { Dragger } = Upload;
const uploadFile = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await client.post('/import/upload', formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data;
};
const ImportPage = () => {
    const [fileList, setFileList] = useState([]);
    const [uploadHistory, setUploadHistory] = useState([]);
    const uploadMutation = useMutation({
        mutationFn: uploadFile,
        onSuccess: (data, variables) => {
            message.success(`Fajl ${variables.name} uspešno poslat za obradu`);
            setUploadHistory(prev => [{
                    id: Date.now().toString(),
                    filename: variables.name,
                    status: 'success',
                    message: 'Fajl je u redu za obradu',
                    timestamp: new Date()
                }, ...prev]);
            setFileList([]);
        },
        onError: (error, variables) => {
            const errorMessage = error?.response?.data?.detail || 'Greška prilikom učitavanja fajla';
            message.error(`Greška: ${errorMessage}`);
            setUploadHistory(prev => [{
                    id: Date.now().toString(),
                    filename: variables.name,
                    status: 'error',
                    message: errorMessage,
                    timestamp: new Date()
                }, ...prev]);
        }
    });
    const uploadProps = {
        name: 'file',
        multiple: false,
        fileList,
        beforeUpload: (file) => {
            const isValidType = file.type === 'text/csv' ||
                file.type === 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
                file.type === 'application/vnd.ms-excel.sheet.macroEnabled.12';
            if (!isValidType) {
                message.error('Podržani su samo CSV i Excel fajlovi (.csv, .xlsx, .xlsm)');
                return false;
            }
            const isLt10M = file.size / 1024 / 1024 < 10;
            if (!isLt10M) {
                message.error('Fajl mora biti manji od 10MB');
                return false;
            }
            return false; // Prevent auto upload
        },
        onChange: (info) => {
            setFileList(info.fileList);
        },
        onRemove: () => {
            setFileList([]);
        }
    };
    const handleUpload = () => {
        if (fileList.length === 0) {
            message.warning('Molimo odaberite fajl za učitavanje');
            return;
        }
        const file = fileList[0].originFileObj;
        if (file) {
            uploadMutation.mutate(file);
        }
    };
    const getFileIcon = (filename) => {
        const extension = filename.toLowerCase().split('.').pop();
        switch (extension) {
            case 'csv':
                return _jsx(FileTextOutlined, { style: { color: '#52c41a' } });
            case 'xlsx':
            case 'xlsm':
                return _jsx(FileExcelOutlined, { style: { color: '#1890ff' } });
            default:
                return _jsx(FileTextOutlined, {});
        }
    };
    return (_jsxs("div", { style: { maxWidth: 800, margin: '0 auto' }, children: [_jsxs(Card, { children: [_jsx(Title, { level: 2, children: "Uvoz trebovanja" }), _jsx(Paragraph, { children: "U\u010Ditajte CSV ili Excel fajl sa trebovanjima. Fajl \u0107e biti poslat na obradu i trebovanja \u0107e biti kreirana automatski." }), _jsx(Alert, { message: "Format fajla", description: _jsxs("div", { children: [_jsx("p", { children: "Fajl mora sadr\u017Eavati slede\u0107e kolone:" }), _jsxs("ul", { children: [_jsxs("li", { children: [_jsx("strong", { children: "dokument_broj" }), " - Broj dokumenta (obavezno)"] }), _jsxs("li", { children: [_jsx("strong", { children: "datum" }), " - Datum trebovanja (YYYY-MM-DD)"] }), _jsxs("li", { children: [_jsx("strong", { children: "magacin" }), " - Naziv magacina"] }), _jsxs("li", { children: [_jsx("strong", { children: "radnja" }), " - Naziv radnje"] }), _jsxs("li", { children: [_jsx("strong", { children: "artikl_sifra" }), " - \u0160ifra artikla"] }), _jsxs("li", { children: [_jsx("strong", { children: "naziv" }), " - Naziv artikla"] }), _jsxs("li", { children: [_jsx("strong", { children: "kolicina_trazena" }), " - Tra\u017Eena koli\u010Dina"] }), _jsxs("li", { children: [_jsx("strong", { children: "barkod" }), " - Barkod artikla (opciono)"] })] })] }), type: "info", showIcon: true, style: { marginBottom: 24 } }), _jsxs(Dragger, { ...uploadProps, style: { marginBottom: 16 }, children: [_jsx("p", { className: "ant-upload-drag-icon", children: _jsx(InboxOutlined, {}) }), _jsx("p", { className: "ant-upload-text", children: "Kliknite ili prevucite fajl ovde" }), _jsx("p", { className: "ant-upload-hint", children: "Podr\u017Eani su CSV i Excel fajlovi (.csv, .xlsx, .xlsm). Maksimalna veli\u010Dina: 10MB" })] }), fileList.length > 0 && (_jsxs("div", { style: { marginBottom: 16 }, children: [_jsx(Text, { strong: true, children: "Odabrani fajl:" }), _jsx("div", { style: { marginTop: 8, padding: 12, background: '#f5f5f5', borderRadius: 6 }, children: _jsxs(Space, { children: [getFileIcon(fileList[0].name), _jsx(Text, { children: fileList[0].name }), _jsxs(Text, { type: "secondary", children: ["(", (fileList[0].size / 1024 / 1024).toFixed(2), " MB)"] })] }) })] })), _jsxs(Space, { children: [_jsx(Button, { type: "primary", icon: _jsx(UploadOutlined, {}), onClick: handleUpload, loading: uploadMutation.isPending, disabled: fileList.length === 0, size: "large", children: uploadMutation.isPending ? 'Učitavam...' : 'Učitaj fajl' }), _jsx(Button, { onClick: () => setFileList([]), disabled: fileList.length === 0, children: "Obri\u0161i" })] }), uploadMutation.isPending && (_jsxs("div", { style: { marginTop: 16 }, children: [_jsx(Progress, { percent: 50, status: "active", showInfo: false }), _jsx(Text, { type: "secondary", children: "Obra\u0111ujem fajl..." })] }))] }), uploadHistory.length > 0 && (_jsx(Card, { title: "Istorija u\u010Ditavanja", style: { marginTop: 24 }, children: _jsx(List, { dataSource: uploadHistory, renderItem: (item) => (_jsx(List.Item, { children: _jsx(List.Item.Meta, { avatar: getFileIcon(item.filename), title: _jsxs(Space, { children: [_jsx(Text, { strong: true, children: item.filename }), _jsx(Tag, { color: item.status === 'success' ? 'green' : 'red', children: item.status === 'success' ? 'Uspešno' : 'Greška' })] }), description: _jsxs("div", { children: [_jsx(Text, { type: "secondary", children: item.message }), _jsx("br", {}), _jsx(Text, { type: "secondary", style: { fontSize: '12px' }, children: item.timestamp.toLocaleString() })] }) }) })) }) }))] }));
};
export default ImportPage;
