import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Table, Button, Space, Tag, Modal, Form, Input, Select, Switch, TimePicker, message, Popconfirm, Tooltip, Row, Col, Statistic, Typography } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined, PauseCircleOutlined, MailOutlined, SlackOutlined, ClockCircleOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getReportSchedules, createReportSchedule, updateReportSchedule, deleteReportSchedule, runReportNow } from '../api';
const { Option } = Select;
const { TextArea } = Input;
const { Title, Text } = Typography;
const ReportsPage = () => {
    const [modalVisible, setModalVisible] = useState(false);
    const [editingSchedule, setEditingSchedule] = useState(null);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();
    // Fetch report schedules
    const { data: schedules = [], isLoading } = useQuery({
        queryKey: ['report-schedules'],
        queryFn: getReportSchedules,
    });
    // Mutations
    const createMutation = useMutation({
        mutationFn: createReportSchedule,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
            setModalVisible(false);
            form.resetFields();
            message.success('Raspored izvještaja kreiran uspešno!');
        },
        onError: (error) => {
            message.error('Greška pri kreiranju rasporeda');
            console.error('Create error:', error);
        }
    });
    const updateMutation = useMutation({
        mutationFn: ({ id, data }) => updateReportSchedule(id, data),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
            setModalVisible(false);
            setEditingSchedule(null);
            form.resetFields();
            message.success('Raspored izvještaja ažuriran uspešno!');
        },
        onError: (error) => {
            message.error('Greška pri ažuriranju rasporeda');
            console.error('Update error:', error);
        }
    });
    const deleteMutation = useMutation({
        mutationFn: deleteReportSchedule,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['report-schedules'] });
            message.success('Raspored izvještaja obrisan uspešno!');
        },
        onError: (error) => {
            message.error('Greška pri brisanju rasporeda');
            console.error('Delete error:', error);
        }
    });
    const runNowMutation = useMutation({
        mutationFn: runReportNow,
        onSuccess: () => {
            message.success('Izvještaj je poslat odmah!');
        },
        onError: (error) => {
            message.error('Greška pri slanju izvještaja');
            console.error('Run now error:', error);
        }
    });
    const handleCreate = () => {
        setEditingSchedule(null);
        form.resetFields();
        setModalVisible(true);
    };
    const handleEdit = (schedule) => {
        setEditingSchedule(schedule);
        form.setFieldsValue({
            ...schedule,
            time: dayjs().hour(schedule.time_hour).minute(schedule.time_minute)
        });
        setModalVisible(true);
    };
    const handleDelete = (id) => {
        deleteMutation.mutate(id);
    };
    const handleRunNow = (id) => {
        runNowMutation.mutate(id);
    };
    const handleToggleEnabled = (schedule) => {
        updateMutation.mutate({
            id: schedule.id,
            data: { enabled: !schedule.enabled }
        });
    };
    const handleSubmit = async (values) => {
        const { time, ...otherValues } = values;
        const scheduleData = {
            ...otherValues,
            time_hour: time.hour(),
            time_minute: time.minute()
        };
        if (editingSchedule) {
            updateMutation.mutate({ id: editingSchedule.id, data: scheduleData });
        }
        else {
            createMutation.mutate(scheduleData);
        }
    };
    const getChannelIcon = (channel) => {
        switch (channel) {
            case 'email': return _jsx(MailOutlined, { style: { color: '#1890ff' } });
            case 'slack': return _jsx(SlackOutlined, { style: { color: '#e91e63' } });
            case 'both': return _jsxs(_Fragment, { children: [_jsx(MailOutlined, { style: { color: '#1890ff' } }), " ", _jsx(SlackOutlined, { style: { color: '#e91e63' } })] });
            default: return null;
        }
    };
    const getFrequencyText = (frequency) => {
        switch (frequency) {
            case 'daily': return 'Dnevno';
            case 'weekly': return 'Nedeljno';
            case 'monthly': return 'Mesečno';
            default: return frequency;
        }
    };
    const getStatusTag = (schedule) => {
        if (schedule.enabled) {
            return _jsx(Tag, { color: "green", icon: _jsx(CheckCircleOutlined, {}), children: "Aktivan" });
        }
        else {
            return _jsx(Tag, { color: "red", icon: _jsx(PauseCircleOutlined, {}), children: "Neaktivan" });
        }
    };
    const columns = [
        {
            title: 'Naziv',
            dataIndex: 'name',
            key: 'name',
            render: (text, record) => (_jsxs("div", { children: [_jsx("div", { style: { fontWeight: 500 }, children: text }), record.description && (_jsx("div", { style: { fontSize: '12px', color: '#666' }, children: record.description }))] })),
        },
        {
            title: 'Kanal',
            dataIndex: 'channel',
            key: 'channel',
            render: (channel) => (_jsxs(Space, { children: [getChannelIcon(channel), _jsx("span", { children: channel.toUpperCase() })] })),
        },
        {
            title: 'Frekvencija',
            dataIndex: 'frequency',
            key: 'frequency',
            render: (frequency) => getFrequencyText(frequency),
        },
        {
            title: 'Vreme slanja',
            key: 'time',
            render: (record) => (_jsxs(Space, { children: [_jsx(ClockCircleOutlined, {}), _jsxs("span", { children: [record.time_hour.toString().padStart(2, '0'), ":", record.time_minute.toString().padStart(2, '0')] })] })),
        },
        {
            title: 'Status',
            key: 'status',
            render: (record) => getStatusTag(record),
        },
        {
            title: 'Statistike',
            key: 'stats',
            render: (record) => (_jsxs("div", { children: [_jsxs("div", { children: ["Poslano: ", record.total_sent] }), _jsxs("div", { style: { color: record.total_failed > 0 ? '#ff4d4f' : '#52c41a' }, children: ["Neuspe\u0161no: ", record.total_failed] })] })),
        },
        {
            title: 'Akcije',
            key: 'actions',
            render: (record) => (_jsxs(Space, { children: [_jsx(Tooltip, { title: "Pokreni odmah", children: _jsx(Button, { type: "primary", size: "small", icon: _jsx(PlayCircleOutlined, {}), onClick: () => handleRunNow(record.id), loading: runNowMutation.isPending }) }), _jsx(Tooltip, { title: "Uredi", children: _jsx(Button, { size: "small", icon: _jsx(EditOutlined, {}), onClick: () => handleEdit(record) }) }), _jsx(Tooltip, { title: record.enabled ? 'Deaktiviraj' : 'Aktiviraj', children: _jsx(Button, { size: "small", icon: record.enabled ? _jsx(PauseCircleOutlined, {}) : _jsx(PlayCircleOutlined, {}), onClick: () => handleToggleEnabled(record), loading: updateMutation.isPending }) }), _jsx(Popconfirm, { title: "Obri\u0161i raspored", description: "Da li ste sigurni da \u017Eelite da obri\u0161ete ovaj raspored?", onConfirm: () => handleDelete(record.id), okText: "Da", cancelText: "Ne", children: _jsx(Tooltip, { title: "Obri\u0161i", children: _jsx(Button, { size: "small", danger: true, icon: _jsx(DeleteOutlined, {}), loading: deleteMutation.isPending }) }) })] })),
        },
    ];
    // Calculate statistics
    const totalSchedules = schedules.length;
    const activeSchedules = schedules.filter(s => s.enabled).length;
    const totalSent = schedules.reduce((sum, s) => sum + s.total_sent, 0);
    const totalFailed = schedules.reduce((sum, s) => sum + s.total_failed, 0);
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx(Title, { level: 2, style: { margin: 0 }, children: "Automatski Izvje\u0161taji" }), _jsx(Text, { type: "secondary", children: "Upravljanje rasporedima za automatsko slanje KPI izvje\u0161taja" })] }), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Ukupno rasporeda", value: totalSchedules, valueStyle: { color: '#1890ff' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Aktivni rasporedi", value: activeSchedules, valueStyle: { color: '#52c41a' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Ukupno poslano", value: totalSent, valueStyle: { color: '#722ed1' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Neuspe\u0161no", value: totalFailed, valueStyle: { color: totalFailed > 0 ? '#ff4d4f' : '#52c41a' } }) }) })] }), _jsx(Card, { title: "Rasporedi Izvje\u0161taja", extra: _jsx(Button, { type: "primary", icon: _jsx(PlusOutlined, {}), onClick: handleCreate, children: "Novi Raspored" }), children: _jsx(Table, { columns: columns, dataSource: schedules, rowKey: "id", loading: isLoading, pagination: {
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `${range[0]}-${range[1]} od ${total} rasporeda`
                    } }) }), _jsx(Modal, { title: editingSchedule ? 'Uredi Raspored' : 'Novi Raspored', open: modalVisible, onCancel: () => {
                    setModalVisible(false);
                    setEditingSchedule(null);
                    form.resetFields();
                }, footer: null, width: 600, children: _jsxs(Form, { form: form, layout: "vertical", onFinish: handleSubmit, initialValues: {
                        channel: 'email',
                        frequency: 'daily',
                        enabled: true,
                        time_hour: 7,
                        time_minute: 0,
                        recipients: [],
                        filters: {}
                    }, children: [_jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "name", label: "Naziv", rules: [{ required: true, message: 'Molimo unesite naziv' }], children: _jsx(Input, { placeholder: "Naziv rasporeda" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "channel", label: "Kanal", rules: [{ required: true, message: 'Molimo odaberite kanal' }], children: _jsxs(Select, { placeholder: "Odaberite kanal", children: [_jsx(Option, { value: "email", children: "Email" }), _jsx(Option, { value: "slack", children: "Slack" }), _jsx(Option, { value: "both", children: "Email + Slack" })] }) }) })] }), _jsx(Form.Item, { name: "description", label: "Opis", children: _jsx(TextArea, { rows: 2, placeholder: "Opis rasporeda (opciono)" }) }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "frequency", label: "Frekvencija", rules: [{ required: true, message: 'Molimo odaberite frekvenciju' }], children: _jsxs(Select, { placeholder: "Odaberite frekvenciju", children: [_jsx(Option, { value: "daily", children: "Dnevno" }), _jsx(Option, { value: "weekly", children: "Nedeljno" }), _jsx(Option, { value: "monthly", children: "Mese\u010Dno" })] }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "time", label: "Vreme slanja", rules: [{ required: true, message: 'Molimo odaberite vreme' }], children: _jsx(TimePicker, { format: "HH:mm", style: { width: '100%' }, placeholder: "Odaberite vreme" }) }) })] }), _jsx(Form.Item, { name: "recipients", label: "Primaoci", rules: [{ required: true, message: 'Molimo unesite primaoce' }], children: _jsx(Select, { mode: "tags", placeholder: "Unesite email adrese ili Slack kanale", style: { width: '100%' } }) }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "filters.radnja", label: "Radnja", children: _jsxs(Select, { placeholder: "Sve radnje", allowClear: true, children: [_jsx(Option, { value: "pantheon", children: "Pantheon" }), _jsx(Option, { value: "maxi", children: "Maxi" }), _jsx(Option, { value: "idea", children: "Idea" })] }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "filters.period", label: "Period", children: _jsxs(Select, { placeholder: "7 dana", allowClear: true, children: [_jsx(Option, { value: "1d", children: "1 dan" }), _jsx(Option, { value: "7d", children: "7 dana" }), _jsx(Option, { value: "30d", children: "30 dana" }), _jsx(Option, { value: "90d", children: "90 dana" })] }) }) })] }), _jsx(Form.Item, { name: "enabled", label: "Status", valuePropName: "checked", children: _jsx(Switch, { checkedChildren: "Aktivan", unCheckedChildren: "Neaktivan" }) }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: createMutation.isPending || updateMutation.isPending, children: editingSchedule ? 'Ažuriraj' : 'Kreiraj' }), _jsx(Button, { onClick: () => setModalVisible(false), children: "Otka\u017Ei" })] }) })] }) })] }));
};
export default ReportsPage;
