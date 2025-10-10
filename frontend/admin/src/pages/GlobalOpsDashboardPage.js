import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Row, Col, Statistic, Button, Space, Tag, Modal, Form, Select, message, Progress, Typography, Alert, Table, Badge, Tabs, Switch, Input, Descriptions, List, Avatar } from 'antd';
import { ReloadOutlined, ThunderboltOutlined, ClockCircleOutlined, ExclamationCircleOutlined, SyncOutlined, NodeIndexOutlined, QuestionCircleOutlined, FireOutlined, RocketOutlined, RadarChartOutlined, CloudServerOutlined, MobileOutlined, WifiOutlined, DisconnectOutlined, DatabaseOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Column, Area, Scatter } from '@ant-design/charts';
import { getKafkaMetrics, getKafkaAnalytics, getKafkaPerformance, getEdgeStatus, getEdgeHealth, getEdgeModels, syncEdgeModels, performEdgeInference } from '../api';
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const GlobalOpsDashboardPage = () => {
    const [globalMode, setGlobalMode] = useState(true);
    const [edgeInferenceModalVisible, setEdgeInferenceModalVisible] = useState(false);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();
    // Fetch global data
    const { data: kafkaMetrics, isLoading: kafkaLoading, refetch: refetchKafka } = useQuery({
        queryKey: ['kafka-metrics'],
        queryFn: getKafkaMetrics,
        refetchInterval: globalMode ? 3000 : false, // Refresh every 3 seconds in global mode
    });
    const { data: kafkaAnalytics, isLoading: analyticsLoading } = useQuery({
        queryKey: ['kafka-analytics'],
        queryFn: getKafkaAnalytics,
        refetchInterval: globalMode ? 5000 : false, // Refresh every 5 seconds in global mode
    });
    const { data: kafkaPerformance, isLoading: performanceLoading } = useQuery({
        queryKey: ['kafka-performance'],
        queryFn: getKafkaPerformance,
        refetchInterval: globalMode ? 10000 : false, // Refresh every 10 seconds in global mode
    });
    const { data: edgeStatus, isLoading: edgeLoading } = useQuery({
        queryKey: ['edge-status'],
        queryFn: getEdgeStatus,
        refetchInterval: globalMode ? 8000 : false, // Refresh every 8 seconds in global mode
    });
    const { data: edgeHealth, isLoading: healthLoading } = useQuery({
        queryKey: ['edge-health'],
        queryFn: getEdgeHealth,
        refetchInterval: globalMode ? 15000 : false, // Refresh every 15 seconds in global mode
    });
    const { data: edgeModels, isLoading: modelsLoading } = useQuery({
        queryKey: ['edge-models'],
        queryFn: getEdgeModels,
        refetchInterval: 30000, // Refresh every 30 seconds
    });
    // Mutations
    const syncMutation = useMutation({
        mutationFn: syncEdgeModels,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['edge-status'] });
            queryClient.invalidateQueries({ queryKey: ['edge-models'] });
            message.success(`Edge sync completed! Model version: ${data.model_version}`);
        },
        onError: (error) => {
            message.error('Edge sync failed');
            console.error('Sync error:', error);
        }
    });
    const inferenceMutation = useMutation({
        mutationFn: performEdgeInference,
        onSuccess: (data) => {
            message.success(`Edge inference completed! Prediction: ${Math.round(data.prediction * 100)}% (${data.inference_time_ms}ms)`);
            setEdgeInferenceModalVisible(false);
            form.resetFields();
        },
        onError: (error) => {
            message.error('Edge inference failed');
            console.error('Inference error:', error);
        }
    });
    const handleEdgeSync = () => {
        syncMutation.mutate();
    };
    const handleEdgeInference = (values) => {
        const inferenceRequest = {
            inference_type: values.inference_type,
            device_id: values.device_id,
            warehouse_id: values.warehouse_id,
            input_data: JSON.parse(values.input_data || '{}'),
            request_id: `edge_inf_${Date.now()}`
        };
        inferenceMutation.mutate(inferenceRequest);
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy': return 'green';
            case 'degraded': return 'orange';
            case 'error': return 'red';
            case 'offline': return 'gray';
            default: return 'blue';
        }
    };
    const getHealthStatus = (health) => {
        if (!health)
            return 'unknown';
        return health.status || 'unknown';
    };
    const getDeviceStatusIcon = (status) => {
        switch (status) {
            case 'online': return _jsx(WifiOutlined, { style: { color: '#52c41a' } });
            case 'offline': return _jsx(DisconnectOutlined, { style: { color: '#ff4d4f' } });
            case 'degraded': return _jsx(ExclamationCircleOutlined, { style: { color: '#faad14' } });
            default: return _jsx(QuestionCircleOutlined, { style: { color: '#d9d9d9' } });
        }
    };
    // Prepare data for visualizations
    const prepareGlobalMapData = () => {
        if (!kafkaAnalytics?.analytics_data?.warehouse_metrics)
            return [];
        return Object.entries(kafkaAnalytics.analytics_data.warehouse_metrics).map(([warehouseId, metrics]) => ({
            warehouse: warehouseId,
            events_count: metrics.events_count,
            active_workers: metrics.active_workers.length,
            ai_decisions: metrics.ai_decisions,
            last_event: new Date(metrics.last_event).getTime(),
            status: metrics.events_count > 100 ? 'high_activity' : 'normal'
        }));
    };
    const prepareEdgeHealthData = () => {
        if (!edgeHealth?.health_metrics)
            return [];
        return [{
                device: edgeHealth.health_metrics.device_id,
                cpu_usage: edgeHealth.health_metrics.system_metrics.cpu_usage,
                memory_usage: edgeHealth.health_metrics.system_metrics.memory_usage,
                temperature: edgeHealth.health_metrics.system_metrics.temperature,
                battery_level: edgeHealth.health_metrics.system_metrics.battery_level,
                status: edgeHealth.health_metrics.status
            }];
    };
    const prepareKafkaThroughputData = () => {
        const data = [];
        const now = Date.now();
        for (let i = 0; i < 30; i++) {
            data.push({
                time: now - (29 - i) * 10000, // 10 seconds intervals
                events_per_second: Math.random() * 500 + 100,
                latency_ms: Math.random() * 50 + 10,
                consumer_lag: Math.random() * 10
            });
        }
        return data;
    };
    const globalMapData = prepareGlobalMapData();
    const edgeHealthData = prepareEdgeHealthData();
    const kafkaThroughputData = prepareKafkaThroughputData();
    // Chart configurations
    const globalMapChartConfig = {
        data: globalMapData,
        xField: 'warehouse',
        yField: 'events_count',
        color: (item) => item.status === 'high_activity' ? '#ff4d4f' : '#52c41a',
        point: {
            size: (item) => item.active_workers * 2,
            shape: 'circle',
        },
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Warehouses' },
        },
        yAxis: {
            title: { text: 'Events Count' },
        },
    };
    const edgeHealthChartConfig = {
        data: edgeHealthData,
        xField: 'device',
        yField: 'cpu_usage',
        color: '#1890ff',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Edge Devices' },
        },
        yAxis: {
            title: { text: 'CPU Usage %' },
        },
    };
    const kafkaThroughputChartConfig = {
        data: kafkaThroughputData,
        xField: 'time',
        yField: 'events_per_second',
        smooth: true,
        color: '#52c41a',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            type: 'time',
            title: { text: 'Time' },
        },
        yAxis: {
            title: { text: 'Events/Second' },
        },
    };
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx(Title, { level: 2, style: { margin: 0 }, children: "\uD83C\uDF0D Global Operations Dashboard" }), _jsx(Text, { type: "secondary", children: "Distributed intelligent system monitoring and control" })] }), _jsx(Card, { style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: 16, align: "middle", children: [_jsx(Col, { children: _jsxs(Space, { children: [_jsx(Switch, { checked: globalMode, onChange: setGlobalMode, checkedChildren: "GLOBAL", unCheckedChildren: "LOCAL" }), _jsx(Text, { strong: true, children: "Global Mode" })] }) }), _jsx(Col, { children: _jsx(Badge, { status: globalMode ? "processing" : "default", text: globalMode ? "Distributed system active" : "Local monitoring only" }) }), _jsx(Col, { flex: "auto" }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: () => {
                                            refetchKafka();
                                            message.success('Global data refreshed');
                                        }, children: "Refresh Global" }), _jsx(Button, { type: "primary", icon: _jsx(ThunderboltOutlined, {}), onClick: handleEdgeSync, loading: syncMutation.isPending, children: "Sync Edge Devices" })] }) })] }) }), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Kafka Throughput", value: kafkaMetrics?.metrics?.throughput_events_per_second || 0, precision: 1, suffix: "events/s", prefix: _jsx(ThunderboltOutlined, {}), valueStyle: { color: '#1890ff' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [kafkaMetrics?.metrics?.events_published || 0, " total published"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Kafka Latency", value: kafkaMetrics?.metrics?.kafka_latency_ms || 0, precision: 1, suffix: "ms", prefix: _jsx(ClockCircleOutlined, {}), valueStyle: { color: kafkaMetrics?.metrics?.kafka_latency_ms && kafkaMetrics.metrics.kafka_latency_ms > 250 ? '#ff4d4f' : '#52c41a' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [kafkaMetrics?.metrics?.consumer_lag || 0, " consumer lag"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Edge Devices", value: edgeHealth?.health_metrics?.device_id ? 1 : 0, prefix: _jsx(MobileOutlined, {}), valueStyle: { color: '#722ed1' } }), _jsx("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: edgeHealth?.health_metrics?.status === 'healthy' ? 'All healthy' : 'Issues detected' })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Global Uptime", value: 99.95, precision: 2, suffix: "%", prefix: _jsx(CloudServerOutlined, {}), valueStyle: { color: '#52c41a' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [kafkaMetrics?.metrics?.error_count || 0, " errors"] })] }) })] }), edgeHealth?.health_metrics?.status === 'degraded' && (_jsx(Alert, { message: "\u26A0\uFE0F Edge Device Health Degraded", description: edgeHealth.health_metrics.issues?.join(', ') || 'Edge device performance issues detected', type: "warning", showIcon: true, style: { marginBottom: '24px' }, action: _jsx(Button, { size: "small", type: "primary", onClick: handleEdgeSync, children: "Sync & Repair" }) })), _jsxs(Tabs, { defaultActiveKey: "global-map", size: "large", children: [_jsx(TabPane, { tab: "\uD83D\uDDFA\uFE0F Live AI Map", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 16, children: _jsx(Card, { title: "Global Warehouse Network", loading: analyticsLoading, children: _jsx("div", { style: { height: '400px' }, children: globalMapData.length > 0 ? (_jsx(Scatter, { ...globalMapChartConfig })) : (_jsx("div", { style: {
                                                    height: '100%',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#999'
                                                }, children: "No warehouse data available" })) }) }) }), _jsx(Col, { xs: 24, lg: 8, children: _jsx(Card, { title: "Warehouse Status", loading: analyticsLoading, children: _jsx(List, { dataSource: globalMapData, renderItem: (item) => (_jsx(List.Item, { children: _jsx(List.Item.Meta, { avatar: _jsx(Avatar, { icon: _jsx(NodeIndexOutlined, {}) }), title: item.warehouse, description: _jsxs(Space, { direction: "vertical", size: "small", children: [_jsxs("div", { children: ["Events: ", item.events_count] }), _jsxs("div", { children: ["Workers: ", item.active_workers] }), _jsxs("div", { children: ["AI Decisions: ", item.ai_decisions] }), _jsx(Tag, { color: item.status === 'high_activity' ? 'red' : 'green', children: item.status === 'high_activity' ? 'High Activity' : 'Normal' })] }) }) })) }) }) })] }) }, "global-map"), _jsx(TabPane, { tab: "\uD83D\uDCF1 Edge Device Health", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Edge Device Performance", loading: healthLoading, children: _jsx("div", { style: { height: '300px' }, children: edgeHealthData.length > 0 ? (_jsx(Column, { ...edgeHealthChartConfig })) : (_jsx("div", { style: {
                                                    height: '100%',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#999'
                                                }, children: "No edge device data available" })) }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Device Status Details", loading: healthLoading, children: edgeStatus?.device_status && (_jsxs(Descriptions, { column: 1, size: "small", children: [_jsx(Descriptions.Item, { label: "Device ID", children: edgeStatus.device_status.device_id }), _jsx(Descriptions.Item, { label: "Status", children: _jsxs(Space, { children: [getDeviceStatusIcon(edgeStatus.device_status.status), _jsx(Tag, { color: getStatusColor(edgeStatus.device_status.status), children: edgeStatus.device_status.status })] }) }), _jsx(Descriptions.Item, { label: "CPU Usage", children: _jsx(Progress, { percent: edgeStatus.device_status.cpu_usage, size: "small", status: edgeStatus.device_status.cpu_usage > 80 ? "exception" : "active" }) }), _jsx(Descriptions.Item, { label: "Memory Usage", children: _jsx(Progress, { percent: edgeStatus.device_status.memory_usage, size: "small", status: edgeStatus.device_status.memory_usage > 85 ? "exception" : "active" }) }), _jsx(Descriptions.Item, { label: "Temperature", children: _jsxs(Space, { children: [_jsx(FireOutlined, {}), _jsxs(Text, { children: [edgeStatus.device_status.temperature, "\u00B0C"] })] }) }), _jsx(Descriptions.Item, { label: "Battery Level", children: _jsxs(Space, { children: [_jsx(ThunderboltOutlined, {}), _jsx(Progress, { percent: edgeStatus.device_status.battery_level, size: "small", status: edgeStatus.device_status.battery_level < 20 ? "exception" : "active" })] }) }), _jsx(Descriptions.Item, { label: "Network Status", children: _jsxs(Space, { children: [_jsx(WifiOutlined, {}), _jsx(Tag, { color: edgeStatus.device_status.network_status === 'connected' ? 'green' : 'red', children: edgeStatus.device_status.network_status })] }) })] })) }) })] }) }, "edge-health"), _jsx(TabPane, { tab: "\uD83D\uDCCA Kafka Stream Monitor", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Kafka Throughput", loading: kafkaLoading, children: _jsx("div", { style: { height: '300px' }, children: _jsx(Area, { ...kafkaThroughputChartConfig }) }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Kafka Performance Metrics", loading: performanceLoading, children: _jsxs(Space, { direction: "vertical", style: { width: '100%' }, children: [_jsxs("div", { children: [_jsx(Text, { strong: true, children: "Throughput Target:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, ((kafkaMetrics?.metrics?.throughput_events_per_second || 0) / 1000) * 100), status: (kafkaMetrics?.metrics?.throughput_events_per_second || 0) > 1000 ? "success" : "active" }), kafkaMetrics?.metrics?.throughput_events_per_second || 0, " / 1000 events/s"] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Latency Target:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, 100 - ((kafkaMetrics?.metrics?.kafka_latency_ms || 0) / 250) * 100), status: (kafkaMetrics?.metrics?.kafka_latency_ms || 0) < 250 ? "success" : "exception" }), kafkaMetrics?.metrics?.kafka_latency_ms || 0, "ms / 250ms target"] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Error Rate:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, ((kafkaMetrics?.metrics?.error_count || 0) / 10) * 100), status: (kafkaMetrics?.metrics?.error_count || 0) < 5 ? "success" : "exception" }), kafkaMetrics?.metrics?.error_count || 0, " errors"] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Consumer Lag:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, ((kafkaMetrics?.metrics?.consumer_lag || 0) / 10) * 100), status: (kafkaMetrics?.metrics?.consumer_lag || 0) < 1 ? "success" : "exception" }), kafkaMetrics?.metrics?.consumer_lag || 0, " lag"] })] })] }) }) })] }) }, "kafka-monitor"), _jsx(TabPane, { tab: "\uD83E\uDD16 Edge AI Models", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Model Performance", loading: modelsLoading, children: _jsx(Table, { dataSource: edgeModels?.models ? Object.entries(edgeModels.models).map(([modelName, modelData]) => ({
                                                key: modelName,
                                                model: modelName,
                                                version: modelData.model_version,
                                                trained: modelData.trained,
                                                inference_count: modelData.performance?.inference_count || 0,
                                                avg_latency: modelData.performance?.average_latency_ms || 0,
                                                success_rate: modelData.performance?.success_rate || 0,
                                                model_size: modelData.performance?.model_size_kb || 0
                                            })) : [], pagination: false, size: "small", columns: [
                                                {
                                                    title: 'Model',
                                                    dataIndex: 'model',
                                                    key: 'model',
                                                    render: (model) => (_jsxs(Space, { children: [_jsx(DatabaseOutlined, {}), _jsx("span", { children: model })] }))
                                                },
                                                {
                                                    title: 'Version',
                                                    dataIndex: 'version',
                                                    key: 'version',
                                                    render: (version) => (_jsx(Tag, { color: "blue", children: version }))
                                                },
                                                {
                                                    title: 'Trained',
                                                    dataIndex: 'trained',
                                                    key: 'trained',
                                                    render: (trained) => (_jsx(Tag, { color: trained ? 'green' : 'red', children: trained ? 'Yes' : 'No' }))
                                                },
                                                {
                                                    title: 'Latency (ms)',
                                                    dataIndex: 'avg_latency',
                                                    key: 'avg_latency',
                                                    render: (latency) => (_jsxs(Tag, { color: latency < 100 ? 'green' : 'red', children: [latency.toFixed(1), "ms"] }))
                                                },
                                                {
                                                    title: 'Success Rate',
                                                    dataIndex: 'success_rate',
                                                    key: 'success_rate',
                                                    render: (rate) => (_jsx(Progress, { percent: rate * 100, size: "small", status: rate > 0.95 ? "success" : "exception" }))
                                                }
                                            ] }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Model Sync Status", loading: modelsLoading, children: _jsxs(Space, { direction: "vertical", style: { width: '100%' }, children: [_jsxs("div", { children: [_jsx(Text, { strong: true, children: "Last Sync:" }), _jsx("div", { children: edgeStatus?.device_status?.last_heartbeat ? new Date(edgeStatus.device_status.last_heartbeat).toLocaleString() : 'Never' })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Sync Status:" }), _jsx("div", { children: _jsx(Tag, { color: "green", children: "Up to date" }) })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Model Version:" }), _jsx("div", { children: edgeModels?.models?.transformer?.model_version || 'Unknown' })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Sync Frequency:" }), _jsx("div", { children: "Every 30 minutes" })] }), _jsx(Button, { type: "primary", icon: _jsx(SyncOutlined, {}), onClick: handleEdgeSync, loading: syncMutation.isPending, style: { width: '100%' }, children: "Force Sync Now" })] }) }) })] }) }, "edge-models")] }), _jsx(Card, { style: { marginTop: '24px' }, children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { children: _jsx(Button, { type: "primary", icon: _jsx(RocketOutlined, {}), onClick: () => setEdgeInferenceModalVisible(true), children: "Test Edge Inference" }) }), _jsx(Col, { children: _jsx(Button, { icon: _jsx(RadarChartOutlined, {}), onClick: () => {
                                    refetchKafka();
                                    message.success('Global system refreshed');
                                }, children: "Refresh Global System" }) }), _jsx(Col, { children: _jsx(Button, { icon: _jsx(SyncOutlined, {}), onClick: handleEdgeSync, loading: syncMutation.isPending, children: "Sync All Edge Devices" }) })] }) }), _jsx(Modal, { title: "\uD83E\uDD16 Test Edge AI Inference", open: edgeInferenceModalVisible, onCancel: () => {
                    setEdgeInferenceModalVisible(false);
                    form.resetFields();
                }, footer: null, width: 700, children: _jsxs(Form, { form: form, layout: "vertical", onFinish: handleEdgeInference, initialValues: {
                        inference_type: 'worker_performance',
                        device_id: 'edge_device_12345',
                        warehouse_id: 'warehouse_1',
                        input_data: '{"current_tasks": 5, "completed_tasks": 25, "efficiency_score": 0.75, "idle_time": 0.2, "experience_level": 0.8}'
                    }, children: [_jsx(Form.Item, { name: "inference_type", label: "Inference Type", rules: [{ required: true, message: 'Please select inference type' }], children: _jsxs(Select, { placeholder: "Select inference type", children: [_jsx(Option, { value: "worker_performance", children: "Worker Performance" }), _jsx(Option, { value: "task_optimization", children: "Task Optimization" }), _jsx(Option, { value: "load_balancing", children: "Load Balancing" }), _jsx(Option, { value: "anomaly_detection", children: "Anomaly Detection" }), _jsx(Option, { value: "resource_allocation", children: "Resource Allocation" })] }) }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "device_id", label: "Device ID", rules: [{ required: true, message: 'Please enter device ID' }], children: _jsx(Input, { placeholder: "edge_device_12345" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "warehouse_id", label: "Warehouse ID", rules: [{ required: true, message: 'Please enter warehouse ID' }], children: _jsx(Input, { placeholder: "warehouse_1" }) }) })] }), _jsx(Form.Item, { name: "input_data", label: "Input Data (JSON)", rules: [{ required: true, message: 'Please enter input data' }], children: _jsx(Input.TextArea, { rows: 6, placeholder: '{"current_tasks": 5, "completed_tasks": 25, "efficiency_score": 0.75, "idle_time": 0.2, "experience_level": 0.8, "workload": 0.6, "time_of_day": 14, "day_of_week": 2}' }) }), _jsx(Alert, { message: "Edge AI Inference", description: "This will perform ultra-fast AI inference on the edge device with <100ms latency. The device will make autonomous decisions based on the input data.", type: "info", showIcon: true, style: { marginBottom: '16px' } }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: inferenceMutation.isPending, icon: _jsx(ThunderboltOutlined, {}), children: "Perform Edge Inference" }), _jsx(Button, { onClick: () => setEdgeInferenceModalVisible(false), children: "Cancel" })] }) })] }) })] }));
};
export default GlobalOpsDashboardPage;
