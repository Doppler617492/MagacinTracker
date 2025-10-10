import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Row, Col, Statistic, Button, Space, Tag, Modal, Form, Select, message, Progress, Typography, Alert, Table, Badge, Tabs, Switch, Input } from 'antd';
import { ReloadOutlined, ThunderboltOutlined, BarChartOutlined, ExclamationCircleOutlined, NodeIndexOutlined, EyeOutlined, FireOutlined, RocketOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Line, Column, Area } from '@ant-design/charts';
import { getStreamMetrics, getThroughputMetrics, getPerformanceMetrics, getHealthMetrics, getRecentEvents, getWorkerActivity, getWarehouseLoad, simulateEvents, publishEvent, getTransformerStatus, predictTransformer } from '../api';
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const LiveOpsDashboardPage = () => {
    const [liveMode, setLiveMode] = useState(true);
    const [eventModalVisible, setEventModalVisible] = useState(false);
    const [predictionModalVisible, setPredictionModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [predictionForm] = Form.useForm();
    const queryClient = useQueryClient();
    // Fetch real-time data
    const { data: streamMetrics, isLoading: metricsLoading, refetch: refetchMetrics } = useQuery({
        queryKey: ['stream-metrics'],
        queryFn: getStreamMetrics,
        refetchInterval: liveMode ? 2000 : false, // Refresh every 2 seconds in live mode
    });
    const { data: throughputMetrics, isLoading: throughputLoading } = useQuery({
        queryKey: ['throughput-metrics'],
        queryFn: getThroughputMetrics,
        refetchInterval: liveMode ? 5000 : false, // Refresh every 5 seconds in live mode
    });
    const { data: performanceMetrics, isLoading: performanceLoading } = useQuery({
        queryKey: ['performance-metrics'],
        queryFn: getPerformanceMetrics,
        refetchInterval: liveMode ? 10000 : false, // Refresh every 10 seconds in live mode
    });
    const { data: healthMetrics, isLoading: healthLoading } = useQuery({
        queryKey: ['health-metrics'],
        queryFn: getHealthMetrics,
        refetchInterval: liveMode ? 15000 : false, // Refresh every 15 seconds in live mode
    });
    const { data: recentEvents, isLoading: eventsLoading, refetch: refetchEvents } = useQuery({
        queryKey: ['recent-events'],
        queryFn: () => getRecentEvents(50),
        refetchInterval: liveMode ? 3000 : false, // Refresh every 3 seconds in live mode
    });
    const { data: workerActivity, isLoading: workerLoading } = useQuery({
        queryKey: ['worker-activity'],
        queryFn: getWorkerActivity,
        refetchInterval: liveMode ? 8000 : false, // Refresh every 8 seconds in live mode
    });
    const { data: warehouseLoad, isLoading: warehouseLoading } = useQuery({
        queryKey: ['warehouse-load'],
        queryFn: getWarehouseLoad,
        refetchInterval: liveMode ? 12000 : false, // Refresh every 12 seconds in live mode
    });
    const { data: transformerStatus, isLoading: transformerLoading } = useQuery({
        queryKey: ['transformer-status'],
        queryFn: getTransformerStatus,
        refetchInterval: 30000, // Refresh every 30 seconds
    });
    // Mutations
    const simulateMutation = useMutation({
        mutationFn: simulateEvents,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['recent-events'] });
            queryClient.invalidateQueries({ queryKey: ['stream-metrics'] });
            message.success(`Simulated ${data.event_count} events successfully!`);
        },
        onError: (error) => {
            message.error('Event simulation failed');
            console.error('Simulation error:', error);
        }
    });
    const publishMutation = useMutation({
        mutationFn: publishEvent,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['recent-events'] });
            message.success(`Event ${data.event_id} published successfully!`);
            setEventModalVisible(false);
            form.resetFields();
        },
        onError: (error) => {
            message.error('Event publish failed');
            console.error('Publish error:', error);
        }
    });
    const predictionMutation = useMutation({
        mutationFn: predictTransformer,
        onSuccess: (data) => {
            message.success(`Pattern analysis completed! Processing time: ${data.processing_time_ms}ms`);
            setPredictionModalVisible(false);
            predictionForm.resetFields();
        },
        onError: (error) => {
            message.error('Pattern prediction failed');
            console.error('Prediction error:', error);
        }
    });
    const handleSimulateEvents = (warehouseId, eventCount) => {
        simulateMutation.mutate({ warehouseId, eventCount });
    };
    const handlePublishEvent = (values) => {
        const eventRequest = {
            event_type: values.event_type,
            warehouse_id: values.warehouse_id,
            data: JSON.parse(values.event_data || '{}'),
            correlation_id: values.correlation_id
        };
        publishMutation.mutate(eventRequest);
    };
    const handlePredictPattern = (values) => {
        const sequences = values.sequences.split('\n').filter((seq) => seq.trim());
        const predictionRequest = {
            sequences: sequences.map((seq) => seq.split(',').map((s) => s.trim()))
        };
        predictionMutation.mutate(predictionRequest);
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy': return 'green';
            case 'degraded': return 'orange';
            case 'error': return 'red';
            default: return 'blue';
        }
    };
    const getEventTypeColor = (eventType) => {
        switch (eventType) {
            case 'task_created': return 'blue';
            case 'task_completed': return 'green';
            case 'task_assigned': return 'purple';
            case 'worker_login': return 'cyan';
            case 'worker_logout': return 'orange';
            case 'scan_event': return 'geekblue';
            case 'ai_prediction': return 'magenta';
            case 'ai_action': return 'red';
            case 'system_alert': return 'volcano';
            default: return 'default';
        }
    };
    // Prepare data for visualizations
    const prepareEventTimelineData = () => {
        if (!recentEvents?.events)
            return [];
        return recentEvents.events.slice(0, 20).map((event, index) => ({
            time: new Date(event.timestamp).getTime(),
            event_type: event.event_type,
            warehouse_id: event.warehouse_id,
            processed: event.processed,
            index
        }));
    };
    const prepareThroughputData = () => {
        const data = [];
        const now = Date.now();
        for (let i = 0; i < 30; i++) {
            data.push({
                time: now - (29 - i) * 10000, // 10 seconds intervals
                events_per_second: Math.random() * 200 + 50,
                queue_size: Math.random() * 100,
                processing_time: Math.random() * 50 + 10
            });
        }
        return data;
    };
    const prepareWorkerActivityData = () => {
        if (!workerActivity?.worker_activity)
            return [];
        return Object.entries(workerActivity.worker_activity).map(([workerId, activity]) => ({
            worker: workerId,
            event_count: activity.event_count,
            last_activity: new Date(activity.last_activity).getTime(),
            warehouse: activity.warehouse_id
        }));
    };
    const eventTimelineData = prepareEventTimelineData();
    const throughputData = prepareThroughputData();
    const workerActivityData = prepareWorkerActivityData();
    // Chart configurations
    const eventTimelineChartConfig = {
        data: eventTimelineData,
        xField: 'time',
        yField: 'index',
        color: (item) => getEventTypeColor(item.event_type),
        point: {
            size: 5,
            shape: 'circle',
        },
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
            title: { text: 'Event Index' },
        },
    };
    const throughputChartConfig = {
        data: throughputData,
        xField: 'time',
        yField: 'events_per_second',
        smooth: true,
        color: '#1890ff',
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
    const workerActivityChartConfig = {
        data: workerActivityData,
        xField: 'worker',
        yField: 'event_count',
        color: '#52c41a',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Workers' },
        },
        yAxis: {
            title: { text: 'Event Count' },
        },
    };
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx(Title, { level: 2, style: { margin: 0 }, children: "\u26A1 Live Operations Dashboard" }), _jsx(Text, { type: "secondary", children: "Real-time monitoring and control of warehouse operations" })] }), _jsx(Card, { style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: 16, align: "middle", children: [_jsx(Col, { children: _jsxs(Space, { children: [_jsx(Switch, { checked: liveMode, onChange: setLiveMode, checkedChildren: "LIVE", unCheckedChildren: "PAUSED" }), _jsx(Text, { strong: true, children: "Live Mode" })] }) }), _jsx(Col, { children: _jsx(Badge, { status: liveMode ? "processing" : "default", text: liveMode ? "Real-time updates active" : "Updates paused" }) }), _jsx(Col, { flex: "auto" }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: () => {
                                            refetchMetrics();
                                            refetchEvents();
                                            message.success('All data refreshed');
                                        }, children: "Refresh All" }), _jsx(Button, { type: "primary", icon: _jsx(ThunderboltOutlined, {}), onClick: () => handleSimulateEvents("warehouse_1", 20), loading: simulateMutation.isPending, children: "Simulate Events" })] }) })] }) }), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Events/Second", value: streamMetrics?.metrics?.events_per_second || 0, precision: 1, prefix: _jsx(ThunderboltOutlined, {}), valueStyle: { color: '#1890ff' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [streamMetrics?.metrics?.events_processed || 0, " total processed"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Queue Size", value: streamMetrics?.metrics?.queue_size || 0, prefix: _jsx(BarChartOutlined, {}), valueStyle: { color: streamMetrics?.metrics?.queue_size > 100 ? '#ff4d4f' : '#52c41a' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [streamMetrics?.metrics?.average_processing_time ? (streamMetrics.metrics.average_processing_time * 1000).toFixed(1) : 0, "ms avg"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Active Workers", value: streamMetrics?.metrics?.active_workers || 0, prefix: _jsx(NodeIndexOutlined, {}), valueStyle: { color: '#722ed1' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [streamMetrics?.metrics?.active_warehouses || 0, " warehouses"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Error Rate", value: streamMetrics?.metrics?.processing_errors || 0, prefix: _jsx(ExclamationCircleOutlined, {}), valueStyle: { color: streamMetrics?.metrics?.processing_errors > 0 ? '#ff4d4f' : '#52c41a' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [streamMetrics?.metrics?.event_history_size || 0, " in history"] })] }) })] }), healthMetrics?.health_metrics?.status === 'degraded' && (_jsx(Alert, { message: "\u26A0\uFE0F System Health Degraded", description: healthMetrics.health_metrics.issues?.join(', ') || 'System performance issues detected', type: "warning", showIcon: true, style: { marginBottom: '24px' }, action: _jsx(Button, { size: "small", type: "primary", children: "View Details" }) })), _jsxs(Tabs, { defaultActiveKey: "events", size: "large", children: [_jsx(TabPane, { tab: "\uD83D\uDCCA Real-time Events", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 16, children: _jsx(Card, { title: "Event Timeline", loading: eventsLoading, children: _jsx("div", { style: { height: '400px' }, children: eventTimelineData.length > 0 ? (_jsx(Line, { ...eventTimelineChartConfig })) : (_jsx("div", { style: {
                                                    height: '100%',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#999'
                                                }, children: "No events available" })) }) }) }), _jsx(Col, { xs: 24, lg: 8, children: _jsx(Card, { title: "Recent Events", loading: eventsLoading, children: _jsx("div", { style: { maxHeight: '400px', overflowY: 'auto' }, children: recentEvents?.events?.slice(0, 10).map((event, index) => (_jsxs("div", { style: {
                                                    padding: '8px 0',
                                                    borderBottom: index < 9 ? '1px solid #f0f0f0' : 'none',
                                                    display: 'flex',
                                                    justifyContent: 'space-between',
                                                    alignItems: 'center'
                                                }, children: [_jsxs("div", { children: [_jsx(Tag, { color: getEventTypeColor(event.event_type), children: event.event_type }), _jsx("div", { style: { fontSize: '12px', color: '#666' }, children: event.warehouse_id })] }), _jsxs("div", { style: { textAlign: 'right' }, children: [_jsx("div", { style: { fontSize: '12px' }, children: new Date(event.timestamp).toLocaleTimeString() }), _jsx(Badge, { status: event.processed ? "success" : "processing", text: event.processed ? "Processed" : "Processing" })] })] }, event.event_id))) }) }) })] }) }, "events"), _jsx(TabPane, { tab: "\uD83D\uDCC8 Throughput Analytics", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Events Per Second", loading: throughputLoading, children: _jsx("div", { style: { height: '300px' }, children: _jsx(Area, { ...throughputChartConfig }) }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Performance Metrics", loading: performanceLoading, children: _jsxs(Space, { direction: "vertical", style: { width: '100%' }, children: [_jsxs("div", { children: [_jsx(Text, { strong: true, children: "Throughput Target:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, (throughputMetrics?.throughput_metrics?.events_per_second || 0) / 2), status: throughputMetrics?.throughput_metrics?.events_per_second > 100 ? "success" : "active" }), throughputMetrics?.throughput_metrics?.events_per_second || 0, " / 100 events/s"] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Latency Target:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, 100 - (throughputMetrics?.throughput_metrics?.average_processing_time || 0) * 1000), status: throughputMetrics?.throughput_metrics?.average_processing_time < 0.1 ? "success" : "exception" }), (throughputMetrics?.throughput_metrics?.average_processing_time || 0) * 1000, "ms / 100ms target"] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Error Rate:" }), _jsxs("div", { children: [_jsx(Progress, { percent: Math.min(100, throughputMetrics?.throughput_metrics?.processing_errors || 0), status: throughputMetrics?.throughput_metrics?.processing_errors < 5 ? "success" : "exception" }), throughputMetrics?.throughput_metrics?.processing_errors || 0, "% / 5% target"] })] })] }) }) })] }) }, "throughput"), _jsx(TabPane, { tab: "\uD83D\uDC65 Worker Activity", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Worker Event Activity", loading: workerLoading, children: _jsx("div", { style: { height: '300px' }, children: workerActivityData.length > 0 ? (_jsx(Column, { ...workerActivityChartConfig })) : (_jsx("div", { style: {
                                                    height: '100%',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#999'
                                                }, children: "No worker activity data available" })) }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Worker Status", loading: workerLoading, children: _jsx(Table, { dataSource: workerActivityData, pagination: false, size: "small", columns: [
                                                {
                                                    title: 'Worker',
                                                    dataIndex: 'worker',
                                                    key: 'worker',
                                                },
                                                {
                                                    title: 'Events',
                                                    dataIndex: 'event_count',
                                                    key: 'event_count',
                                                    render: (count) => (_jsx(Tag, { color: "blue", children: count }))
                                                },
                                                {
                                                    title: 'Warehouse',
                                                    dataIndex: 'warehouse',
                                                    key: 'warehouse',
                                                },
                                                {
                                                    title: 'Last Activity',
                                                    dataIndex: 'last_activity',
                                                    key: 'last_activity',
                                                    render: (time) => (_jsx(Text, { type: "secondary", children: new Date(time).toLocaleTimeString() }))
                                                }
                                            ] }) }) })] }) }, "workers"), _jsx(TabPane, { tab: "\uD83C\uDFED Warehouse Load", children: _jsx(Row, { gutter: 16, children: _jsx(Col, { xs: 24, children: _jsx(Card, { title: "Warehouse Load Distribution", loading: warehouseLoading, children: _jsx(Table, { dataSource: Object.entries(warehouseLoad?.warehouse_load || {}).map(([warehouseId, load]) => ({
                                            key: warehouseId,
                                            warehouse: warehouseId,
                                            event_count: load.event_count,
                                            active_workers: load.active_workers.length,
                                            last_event: load.last_event
                                        })), pagination: false, columns: [
                                            {
                                                title: 'Warehouse',
                                                dataIndex: 'warehouse',
                                                key: 'warehouse',
                                            },
                                            {
                                                title: 'Event Count',
                                                dataIndex: 'event_count',
                                                key: 'event_count',
                                                render: (count) => (_jsx(Progress, { percent: Math.min(100, count / 10), size: "small", status: count > 100 ? "exception" : "active" }))
                                            },
                                            {
                                                title: 'Active Workers',
                                                dataIndex: 'active_workers',
                                                key: 'active_workers',
                                                render: (count) => (_jsx(Tag, { color: "green", children: count }))
                                            },
                                            {
                                                title: 'Last Event',
                                                dataIndex: 'last_event',
                                                key: 'last_event',
                                                render: (time) => (_jsx(Text, { type: "secondary", children: new Date(time).toLocaleTimeString() }))
                                            }
                                        ] }) }) }) }) }, "warehouses")] }), _jsx(Card, { style: { marginTop: '24px' }, children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { children: _jsx(Button, { type: "primary", icon: _jsx(RocketOutlined, {}), onClick: () => setEventModalVisible(true), children: "Publish Event" }) }), _jsx(Col, { children: _jsx(Button, { icon: _jsx(EyeOutlined, {}), onClick: () => setPredictionModalVisible(true), children: "Analyze Pattern" }) }), _jsx(Col, { children: _jsx(Button, { icon: _jsx(FireOutlined, {}), onClick: () => handleSimulateEvents("warehouse_1", 50), loading: simulateMutation.isPending, children: "Stress Test" }) })] }) }), _jsx(Modal, { title: "\uD83D\uDE80 Publish Event", open: eventModalVisible, onCancel: () => {
                    setEventModalVisible(false);
                    form.resetFields();
                }, footer: null, width: 600, children: _jsxs(Form, { form: form, layout: "vertical", onFinish: handlePublishEvent, initialValues: {
                        event_type: 'task_created',
                        warehouse_id: 'warehouse_1',
                        event_data: '{"task_id": "task_123", "priority": "high"}',
                        correlation_id: `corr_${Date.now()}`
                    }, children: [_jsx(Form.Item, { name: "event_type", label: "Event Type", rules: [{ required: true, message: 'Please select event type' }], children: _jsxs(Select, { placeholder: "Select event type", children: [_jsx(Option, { value: "task_created", children: "Task Created" }), _jsx(Option, { value: "task_completed", children: "Task Completed" }), _jsx(Option, { value: "task_assigned", children: "Task Assigned" }), _jsx(Option, { value: "worker_login", children: "Worker Login" }), _jsx(Option, { value: "worker_logout", children: "Worker Logout" }), _jsx(Option, { value: "scan_event", children: "Scan Event" }), _jsx(Option, { value: "ai_prediction", children: "AI Prediction" }), _jsx(Option, { value: "ai_action", children: "AI Action" }), _jsx(Option, { value: "system_alert", children: "System Alert" })] }) }), _jsx(Form.Item, { name: "warehouse_id", label: "Warehouse ID", rules: [{ required: true, message: 'Please enter warehouse ID' }], children: _jsx(Input, { placeholder: "warehouse_1" }) }), _jsx(Form.Item, { name: "event_data", label: "Event Data (JSON)", rules: [{ required: true, message: 'Please enter event data' }], children: _jsx(Input.TextArea, { rows: 4, placeholder: '{"task_id": "task_123", "priority": "high", "worker_id": "worker_1"}' }) }), _jsx(Form.Item, { name: "correlation_id", label: "Correlation ID", children: _jsx(Input, { placeholder: "Optional correlation ID" }) }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: publishMutation.isPending, icon: _jsx(RocketOutlined, {}), children: "Publish Event" }), _jsx(Button, { onClick: () => setEventModalVisible(false), children: "Cancel" })] }) })] }) }), _jsx(Modal, { title: "\uD83D\uDD0D Pattern Analysis", open: predictionModalVisible, onCancel: () => {
                    setPredictionModalVisible(false);
                    predictionForm.resetFields();
                }, footer: null, width: 800, children: _jsxs(Form, { form: predictionForm, layout: "vertical", onFinish: handlePredictPattern, initialValues: {
                        sequences: `task_created,worker_login,scan_event,task_completed
task_created,task_assigned,scan_event,worker_logout
worker_login,task_created,scan_event,task_completed,worker_logout`
                    }, children: [_jsx(Alert, { message: "Pattern Analysis", description: "Enter event sequences (one per line, comma-separated) to analyze patterns like 'warehouse overload' or 'worker performance decline'.", type: "info", showIcon: true, style: { marginBottom: '16px' } }), _jsx(Form.Item, { name: "sequences", label: "Event Sequences", rules: [{ required: true, message: 'Please enter event sequences' }], children: _jsx(Input.TextArea, { rows: 8, placeholder: "task_created,worker_login,scan_event,task_completed\ntask_created,task_assigned,scan_event,worker_logout\nworker_login,task_created,scan_event,task_completed,worker_logout" }) }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: predictionMutation.isPending, icon: _jsx(EyeOutlined, {}), children: "Analyze Patterns" }), _jsx(Button, { onClick: () => setPredictionModalVisible(false), children: "Cancel" })] }) })] }) })] }));
};
export default LiveOpsDashboardPage;
