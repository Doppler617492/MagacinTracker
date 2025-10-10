import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Row, Col, Statistic, Button, Space, Tag, Modal, Form, InputNumber, Select, message, Progress, Typography, Alert, Table, Tabs } from 'antd';
import { ReloadOutlined, BulbOutlined, SyncOutlined, GlobalOutlined, NodeIndexOutlined, ThunderboltOutlined, EyeOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Column, Heatmap } from '@ant-design/charts';
import { getFederatedSystemStatus, aggregateFederatedModels, getEdgeSystemStatus, syncEdgeModels, getDNNStatus, trainDNNModel, predictDNN } from '../api';
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { TabPane } = Tabs;
const GlobalAIHubPage = () => {
    const [predictionModalVisible, setPredictionModalVisible] = useState(false);
    const [explainModalVisible, setExplainModalVisible] = useState(false);
    const [form] = Form.useForm();
    const [predictionForm] = Form.useForm();
    const queryClient = useQueryClient();
    // Fetch system statuses
    const { data: federatedStatus, isLoading: federatedLoading, refetch: refetchFederated } = useQuery({
        queryKey: ['federated-system-status'],
        queryFn: getFederatedSystemStatus,
        refetchInterval: 30000, // Refresh every 30 seconds
    });
    const { data: edgeStatus, isLoading: edgeLoading, refetch: refetchEdge } = useQuery({
        queryKey: ['edge-system-status'],
        queryFn: getEdgeSystemStatus,
        refetchInterval: 30000, // Refresh every 30 seconds
    });
    const { data: dnnStatus, isLoading: dnnLoading, refetch: refetchDNN } = useQuery({
        queryKey: ['dnn-status'],
        queryFn: getDNNStatus,
        refetchInterval: 60000, // Refresh every minute
    });
    // Mutations
    const aggregationMutation = useMutation({
        mutationFn: aggregateFederatedModels,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['federated-system-status'] });
            message.success(`Federated aggregation completed! ${data.nodes_participated} nodes participated`);
        },
        onError: (error) => {
            message.error('Federated aggregation failed');
            console.error('Aggregation error:', error);
        }
    });
    const syncMutation = useMutation({
        mutationFn: syncEdgeModels,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['edge-system-status'] });
            message.success(`Edge sync completed! ${data.models_updated} models updated`);
        },
        onError: (error) => {
            message.error('Edge sync failed');
            console.error('Sync error:', error);
        }
    });
    const dnnTrainingMutation = useMutation({
        mutationFn: trainDNNModel,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['dnn-status'] });
            message.success(`DNN training completed! Accuracy: ${Math.round(data.final_accuracy * 100)}%`);
        },
        onError: (error) => {
            message.error('DNN training failed');
            console.error('DNN training error:', error);
        }
    });
    const predictionMutation = useMutation({
        mutationFn: predictDNN,
        onSuccess: (data) => {
            setExplainModalVisible(true);
            message.success(`Prediction completed! Performance: ${Math.round(data.prediction * 100)}%`);
        },
        onError: (error) => {
            message.error('Prediction failed');
            console.error('Prediction error:', error);
        }
    });
    const handleAggregateNow = () => {
        aggregationMutation.mutate();
    };
    const handleSyncNow = () => {
        syncMutation.mutate();
    };
    const handleDNNTraining = (values) => {
        const trainingRequest = {
            epochs: values.epochs,
            learning_rate: values.learning_rate,
            batch_size: values.batch_size,
            validation_split: values.validation_split
        };
        dnnTrainingMutation.mutate(trainingRequest);
    };
    const handlePrediction = (values) => {
        const predictionRequest = {
            features: [
                values.current_tasks / 15.0,
                values.completed_tasks / 60.0,
                values.avg_completion_time / 15.0,
                values.efficiency_score,
                values.idle_time_percentage,
                values.day_of_week / 7.0,
                values.hour_of_day / 24.0,
                values.store_load_index,
                values.seasonality_factor,
                values.product_complexity,
                values.worker_experience,
                values.team_size / 10.0
            ],
            include_feature_importance: true
        };
        predictionMutation.mutate(predictionRequest);
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'healthy': return 'green';
            case 'syncing': return 'blue';
            case 'error': return 'red';
            case 'offline': return 'gray';
            default: return 'blue';
        }
    };
    const getNodeStatusColor = (node) => {
        if (!node.is_initialized)
            return 'red';
        if (node.is_syncing)
            return 'blue';
        if (node.should_sync)
            return 'orange';
        return 'green';
    };
    // Prepare data for visualizations
    const prepareFederatedSyncData = () => {
        if (!federatedStatus?.nodes)
            return [];
        return Object.entries(federatedStatus.nodes).map(([nodeId, node]) => ({
            node: nodeId,
            last_sync: node.last_sync ? new Date(node.last_sync).getTime() : 0,
            training_samples: node.training_samples,
            status: node.is_initialized ? 'active' : 'inactive'
        }));
    };
    const prepareEdgePerformanceData = () => {
        if (!edgeStatus?.models)
            return [];
        return Object.entries(edgeStatus.models).map(([modelId, model]) => ({
            model: modelId,
            avg_inference_time: model.performance_stats?.avg_inference_time_ms || 0,
            total_inferences: model.performance_stats?.total_inferences || 0,
            performance_target_met: model.performance_stats?.performance_target_met || false
        }));
    };
    const prepareModelAccuracyData = () => {
        const data = [];
        const locations = ['Podgorica DC', 'Nikšić Store', 'Bar Store', 'Ulcinj Store', 'Pljevlja Store'];
        for (let i = 0; i < 30; i++) {
            const date = new Date();
            date.setDate(date.getDate() - (29 - i));
            locations.forEach(location => {
                data.push({
                    date: date.toISOString().split('T')[0],
                    location,
                    accuracy: 0.75 + Math.random() * 0.2 + (Math.sin(i / 5) * 0.1)
                });
            });
        }
        return data;
    };
    const federatedSyncData = prepareFederatedSyncData();
    const edgePerformanceData = prepareEdgePerformanceData();
    const modelAccuracyData = prepareModelAccuracyData();
    // Chart configurations
    const federatedSyncChartConfig = {
        data: federatedSyncData,
        xField: 'node',
        yField: 'training_samples',
        color: (item) => item.status === 'active' ? '#52c41a' : '#ff4d4f',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Federated Nodes' },
        },
        yAxis: {
            title: { text: 'Training Samples' },
        },
    };
    const edgePerformanceChartConfig = {
        data: edgePerformanceData,
        xField: 'model',
        yField: 'avg_inference_time',
        color: (item) => item.performance_target_met ? '#52c41a' : '#ff4d4f',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Edge Models' },
        },
        yAxis: {
            title: { text: 'Inference Time (ms)' },
        },
    };
    const modelAccuracyHeatmapConfig = {
        data: modelAccuracyData,
        xField: 'date',
        yField: 'location',
        colorField: 'accuracy',
        color: ['#ff4d4f', '#faad14', '#52c41a'],
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
    };
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx(Title, { level: 2, style: { margin: 0 }, children: "\uD83C\uDF0D Global AI Hub" }), _jsx(Text, { type: "secondary", children: "Centralized AI management across all warehouses and locations" })] }), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Federated Nodes", value: federatedStatus?.aggregation_status?.total_nodes || 0, prefix: _jsx(NodeIndexOutlined, {}), valueStyle: { color: '#1890ff' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [federatedStatus?.aggregation_status?.trained_nodes || 0, " trained"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Edge Models", value: edgeStatus?.total_models || 0, prefix: _jsx(ThunderboltOutlined, {}), valueStyle: { color: '#52c41a' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [edgeStatus?.initialized_models || 0, " initialized"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Global Model Version", value: federatedStatus?.global_model?.version || 0, prefix: _jsx(GlobalOutlined, {}), valueStyle: { color: '#722ed1' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [federatedStatus?.global_model?.total_samples || 0, " samples"] })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Edge Predictions", value: edgeStatus?.total_predictions || 0, prefix: _jsx(BulbOutlined, {}), valueStyle: { color: '#faad14' } }), _jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: [edgeStatus?.sync_errors || 0, " sync errors"] })] }) })] }), _jsx(Card, { style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { children: _jsx(Button, { type: "primary", size: "large", icon: _jsx(SyncOutlined, {}), onClick: handleAggregateNow, loading: aggregationMutation.isPending, children: "Aggregate Now" }) }), _jsx(Col, { children: _jsx(Button, { size: "large", icon: _jsx(ReloadOutlined, {}), onClick: handleSyncNow, loading: syncMutation.isPending, children: "Sync Edge Models" }) }), _jsx(Col, { children: _jsx(Button, { size: "large", icon: _jsx(EyeOutlined, {}), onClick: () => setPredictionModalVisible(true), children: "Test Prediction" }) }), _jsx(Col, { children: _jsx(Button, { size: "large", icon: _jsx(ReloadOutlined, {}), onClick: () => {
                                    refetchFederated();
                                    refetchEdge();
                                    refetchDNN();
                                    message.success('All systems refreshed');
                                }, children: "Refresh All" }) })] }) }), _jsxs(Tabs, { defaultActiveKey: "federated", size: "large", children: [_jsx(TabPane, { tab: "\uD83D\uDD04 Federated Learning", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Federated Nodes Status", loading: federatedLoading, children: _jsx(Table, { dataSource: federatedSyncData, pagination: false, size: "small", columns: [
                                                {
                                                    title: 'Node',
                                                    dataIndex: 'node',
                                                    key: 'node',
                                                    render: (node) => (_jsxs(Space, { children: [_jsx(NodeIndexOutlined, {}), _jsx("span", { children: node })] }))
                                                },
                                                {
                                                    title: 'Status',
                                                    dataIndex: 'status',
                                                    key: 'status',
                                                    render: (status) => (_jsx(Tag, { color: status === 'active' ? 'green' : 'red', children: status === 'active' ? 'Active' : 'Inactive' }))
                                                },
                                                {
                                                    title: 'Samples',
                                                    dataIndex: 'training_samples',
                                                    key: 'training_samples',
                                                    render: (samples) => samples.toLocaleString()
                                                }
                                            ] }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Training Samples Distribution", loading: federatedLoading, children: _jsx("div", { style: { height: '300px' }, children: federatedSyncData.length > 0 ? (_jsx(Column, { ...federatedSyncChartConfig })) : (_jsx("div", { style: {
                                                    height: '100%',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#999'
                                                }, children: "No federated data available" })) }) }) })] }) }, "federated"), _jsx(TabPane, { tab: "\u26A1 Edge Inference", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Edge Models Performance", loading: edgeLoading, children: _jsx(Table, { dataSource: edgePerformanceData, pagination: false, size: "small", columns: [
                                                {
                                                    title: 'Model',
                                                    dataIndex: 'model',
                                                    key: 'model',
                                                    render: (model) => (_jsxs(Space, { children: [_jsx(ThunderboltOutlined, {}), _jsx("span", { children: model })] }))
                                                },
                                                {
                                                    title: 'Avg Time (ms)',
                                                    dataIndex: 'avg_inference_time',
                                                    key: 'avg_inference_time',
                                                    render: (time) => (_jsxs(Tag, { color: time < 200 ? 'green' : 'red', children: [time.toFixed(1), "ms"] }))
                                                },
                                                {
                                                    title: 'Predictions',
                                                    dataIndex: 'total_inferences',
                                                    key: 'total_inferences',
                                                    render: (count) => count.toLocaleString()
                                                }
                                            ] }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Inference Performance", loading: edgeLoading, children: _jsx("div", { style: { height: '300px' }, children: edgePerformanceData.length > 0 ? (_jsx(Column, { ...edgePerformanceChartConfig })) : (_jsx("div", { style: {
                                                    height: '100%',
                                                    display: 'flex',
                                                    alignItems: 'center',
                                                    justifyContent: 'center',
                                                    color: '#999'
                                                }, children: "No edge performance data available" })) }) }) })] }) }, "edge"), _jsx(TabPane, { tab: "\uD83E\uDDE0 Deep Neural Network", children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "DNN Model Status", loading: dnnLoading, children: _jsxs(Space, { direction: "vertical", style: { width: '100%' }, children: [_jsxs("div", { children: [_jsx(Text, { strong: true, children: "Model Version:" }), _jsx("div", { children: dnnStatus?.model_version || 0 })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Accuracy:" }), _jsxs("div", { children: [dnnStatus?.accuracy ? Math.round(dnnStatus.accuracy * 100) : 0, "%"] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Parameters:" }), _jsx("div", { children: dnnStatus?.total_parameters?.toLocaleString() || 0 })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Last Trained:" }), _jsx("div", { children: dnnStatus?.last_trained ? new Date(dnnStatus.last_trained).toLocaleString() : 'Never' })] })] }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Model Accuracy Heatmap", loading: dnnLoading, children: _jsx("div", { style: { height: '300px' }, children: _jsx(Heatmap, { ...modelAccuracyHeatmapConfig }) }) }) })] }) }, "dnn"), _jsx(TabPane, { tab: "\uD83D\uDCCA Global Analytics", children: _jsx(Row, { gutter: 16, children: _jsx(Col, { xs: 24, children: _jsx(Card, { title: "Model Performance Across Locations", children: _jsx("div", { style: { height: '400px' }, children: _jsx(Heatmap, { ...modelAccuracyHeatmapConfig }) }) }) }) }) }, "analytics")] }), _jsx(Modal, { title: "\uD83E\uDDE0 Test Deep Neural Network Prediction", open: predictionModalVisible, onCancel: () => {
                    setPredictionModalVisible(false);
                    predictionForm.resetFields();
                }, footer: null, width: 800, children: _jsxs(Form, { form: predictionForm, layout: "vertical", onFinish: handlePrediction, initialValues: {
                        current_tasks: 5,
                        completed_tasks: 25,
                        avg_completion_time: 4.5,
                        efficiency_score: 0.75,
                        idle_time_percentage: 0.2,
                        day_of_week: 1,
                        hour_of_day: 12,
                        store_load_index: 0.6,
                        seasonality_factor: 0.5,
                        product_complexity: 0.5,
                        worker_experience: 0.7,
                        team_size: 3
                    }, children: [_jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "current_tasks", label: "Current Tasks", children: _jsx(InputNumber, { min: 0, max: 20, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "completed_tasks", label: "Completed Tasks Today", children: _jsx(InputNumber, { min: 0, max: 100, style: { width: '100%' } }) }) })] }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "avg_completion_time", label: "Avg Completion Time (min)", children: _jsx(InputNumber, { min: 1, max: 15, step: 0.1, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "efficiency_score", label: "Efficiency Score", children: _jsx(InputNumber, { min: 0, max: 1, step: 0.01, style: { width: '100%' } }) }) })] }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "idle_time_percentage", label: "Idle Time %", children: _jsx(InputNumber, { min: 0, max: 1, step: 0.01, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "store_load_index", label: "Store Load Index", children: _jsx(InputNumber, { min: 0, max: 1, step: 0.01, style: { width: '100%' } }) }) })] }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "day_of_week", label: "Day of Week", children: _jsx(InputNumber, { min: 0, max: 6, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "hour_of_day", label: "Hour of Day", children: _jsx(InputNumber, { min: 0, max: 23, style: { width: '100%' } }) }) })] }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "seasonality_factor", label: "Seasonality Factor", children: _jsx(InputNumber, { min: 0, max: 1, step: 0.01, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "product_complexity", label: "Product Complexity", children: _jsx(InputNumber, { min: 0, max: 1, step: 0.01, style: { width: '100%' } }) }) })] }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "worker_experience", label: "Worker Experience", children: _jsx(InputNumber, { min: 0, max: 1, step: 0.01, style: { width: '100%' } }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "team_size", label: "Team Size", children: _jsx(InputNumber, { min: 1, max: 10, style: { width: '100%' } }) }) })] }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: predictionMutation.isPending, icon: _jsx(BulbOutlined, {}), children: "Predict Performance" }), _jsx(Button, { onClick: () => setPredictionModalVisible(false), children: "Cancel" })] }) })] }) }), _jsx(Modal, { title: "\uD83D\uDD0D Prediction Explanation", open: explainModalVisible, onCancel: () => setExplainModalVisible(false), footer: [
                    _jsx(Button, { onClick: () => setExplainModalVisible(false), children: "Close" }, "close")
                ], width: 600, children: predictionMutation.data && (_jsxs("div", { children: [_jsx(Alert, { message: `Predicted Performance: ${Math.round(predictionMutation.data.prediction * 100)}%`, description: `Confidence: ${Math.round(predictionMutation.data.confidence * 100)}% | Processing Time: ${predictionMutation.data.processing_time_ms.toFixed(1)}ms`, type: "info", showIcon: true, style: { marginBottom: '16px' } }), predictionMutation.data.feature_importance && (_jsxs("div", { children: [_jsx(Title, { level: 4, children: "Feature Importance" }), _jsx(Table, { dataSource: Object.entries(predictionMutation.data.feature_importance).map(([feature, importance]) => ({
                                        key: feature,
                                        feature,
                                        importance: Number(importance)
                                    })), pagination: false, size: "small", columns: [
                                        {
                                            title: 'Feature',
                                            dataIndex: 'feature',
                                            key: 'feature',
                                        },
                                        {
                                            title: 'Importance',
                                            dataIndex: 'importance',
                                            key: 'importance',
                                            render: (importance) => (_jsx(Progress, { percent: Math.abs(importance) * 100, size: "small", status: importance > 0 ? 'active' : 'exception' }))
                                        }
                                    ] })] }))] })) })] }));
};
export default GlobalAIHubPage;
