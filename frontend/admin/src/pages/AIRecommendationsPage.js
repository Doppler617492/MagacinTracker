import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Table, Button, Space, Tag, Modal, message, Popconfirm, Tooltip, Row, Col, Statistic, Progress, Typography, Alert, Badge } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined, EyeOutlined, PlayCircleOutlined, BulbOutlined, RiseOutlined, UserOutlined, ShopOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAIRecommendations, applyRecommendation, dismissRecommendation, simulateLoadBalance } from '../api';
const { Title, Text, Paragraph } = Typography;
const AIRecommendationsPage = () => {
    const [simulationModalVisible, setSimulationModalVisible] = useState(false);
    const [selectedRecommendation, setSelectedRecommendation] = useState(null);
    const [simulationData, setSimulationData] = useState(null);
    const queryClient = useQueryClient();
    // Fetch AI recommendations
    const { data: recommendations = [], isLoading, refetch } = useQuery({
        queryKey: ['ai-recommendations'],
        queryFn: getAIRecommendations,
        refetchInterval: 30000, // Refresh every 30 seconds
    });
    // Mutations
    const applyMutation = useMutation({
        mutationFn: applyRecommendation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-recommendations'] });
            message.success('Preporuka je uspešno primijenjena!');
        },
        onError: (error) => {
            message.error('Greška pri primjeni preporuke');
            console.error('Apply error:', error);
        }
    });
    const dismissMutation = useMutation({
        mutationFn: dismissRecommendation,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-recommendations'] });
            message.success('Preporuka je odbačena');
        },
        onError: (error) => {
            message.error('Greška pri odbacivanju preporuke');
            console.error('Dismiss error:', error);
        }
    });
    const simulateMutation = useMutation({
        mutationFn: simulateLoadBalance,
        onSuccess: (data) => {
            setSimulationData(data);
            setSimulationModalVisible(true);
        },
        onError: (error) => {
            message.error('Greška pri simulaciji');
            console.error('Simulate error:', error);
        }
    });
    const handleApply = (recommendationId) => {
        applyMutation.mutate(recommendationId);
    };
    const handleDismiss = (recommendationId) => {
        dismissMutation.mutate(recommendationId);
    };
    const handleSimulate = (recommendation) => {
        setSelectedRecommendation(recommendation);
        // Mock data for simulation
        const mockSimulationRequest = {
            recommendation_id: recommendation.id,
            worker_metrics: [
                {
                    worker_id: "worker_001",
                    worker_name: "Marko Šef",
                    current_tasks: 8,
                    completed_tasks_today: 25,
                    avg_completion_time: 4.2,
                    efficiency_score: 0.85,
                    idle_time_percentage: 0.15,
                    location: "pantheon"
                },
                {
                    worker_id: "worker_002",
                    worker_name: "Ana Radnik",
                    current_tasks: 12,
                    completed_tasks_today: 18,
                    avg_completion_time: 5.1,
                    efficiency_score: 0.72,
                    idle_time_percentage: 0.05,
                    location: "pantheon"
                }
            ],
            store_metrics: [
                {
                    store_id: "pantheon",
                    store_name: "Pantheon",
                    total_tasks: 45,
                    completed_tasks: 30,
                    pending_tasks: 15,
                    avg_completion_time: 4.6,
                    worker_count: 2,
                    load_index: 0.75,
                    efficiency_delta: 0.05
                },
                {
                    store_id: "maxi",
                    store_name: "Maxi",
                    total_tasks: 20,
                    completed_tasks: 18,
                    pending_tasks: 2,
                    avg_completion_time: 3.9,
                    worker_count: 1,
                    load_index: 0.20,
                    efficiency_delta: -0.02
                }
            ]
        };
        simulateMutation.mutate(mockSimulationRequest);
    };
    const getPriorityColor = (priority) => {
        switch (priority) {
            case 'high': return 'red';
            case 'medium': return 'orange';
            case 'low': return 'green';
            default: return 'blue';
        }
    };
    const getTypeIcon = (type) => {
        switch (type) {
            case 'load_balance': return _jsx(RiseOutlined, {});
            case 'resource_allocation': return _jsx(UserOutlined, {});
            case 'task_reassignment': return _jsx(ShopOutlined, {});
            case 'efficiency_optimization': return _jsx(BulbOutlined, {});
            default: return _jsx(BulbOutlined, {});
        }
    };
    const getConfidenceBadge = (confidence) => {
        if (confidence >= 0.9)
            return _jsx(Badge, { status: "success", text: "Visoko pouzdano" });
        if (confidence >= 0.7)
            return _jsx(Badge, { status: "warning", text: "Srednje pouzdano" });
        return _jsx(Badge, { status: "error", text: "Nisko pouzdano" });
    };
    const columns = [
        {
            title: 'Tip',
            dataIndex: 'type',
            key: 'type',
            render: (type) => (_jsxs(Space, { children: [getTypeIcon(type), _jsx("span", { children: type.replace('_', ' ').toUpperCase() })] })),
        },
        {
            title: 'Preporuka',
            dataIndex: 'title',
            key: 'title',
            render: (title, record) => (_jsxs("div", { children: [_jsx("div", { style: { fontWeight: 500, marginBottom: '4px' }, children: title }), _jsx("div", { style: { fontSize: '12px', color: '#666' }, children: record.description })] })),
        },
        {
            title: 'Prioritet',
            dataIndex: 'priority',
            key: 'priority',
            render: (priority) => (_jsx(Tag, { color: getPriorityColor(priority), children: priority.toUpperCase() })),
        },
        {
            title: 'Pouzdanost',
            dataIndex: 'confidence',
            key: 'confidence',
            render: (confidence) => (_jsxs("div", { children: [_jsx("div", { style: { marginBottom: '4px' }, children: getConfidenceBadge(confidence) }), _jsxs("div", { style: { fontSize: '12px', color: '#666' }, children: [Math.round(confidence * 100), "%"] })] })),
        },
        {
            title: 'Očekivano poboljšanje',
            key: 'improvement',
            render: (record) => (_jsx("div", { children: Object.entries(record.estimated_improvement).map(([key, value]) => (_jsxs("div", { style: { fontSize: '12px', marginBottom: '2px' }, children: [key.replace('_', ' '), ": ", value > 0 ? '+' : '', value.toFixed(1), "%"] }, key))) })),
        },
        {
            title: 'Akcije',
            key: 'actions',
            render: (record) => (_jsxs(Space, { children: [_jsx(Tooltip, { title: "Simuliraj", children: _jsx(Button, { size: "small", icon: _jsx(EyeOutlined, {}), onClick: () => handleSimulate(record), loading: simulateMutation.isPending }) }), _jsx(Tooltip, { title: "Primijeni", children: _jsx(Button, { type: "primary", size: "small", icon: _jsx(CheckCircleOutlined, {}), onClick: () => handleApply(record.id), loading: applyMutation.isPending }) }), _jsx(Popconfirm, { title: "Odbaci preporuku", description: "Da li ste sigurni da \u017Eelite da odbacite ovu preporuku?", onConfirm: () => handleDismiss(record.id), okText: "Da", cancelText: "Ne", children: _jsx(Tooltip, { title: "Odbaci", children: _jsx(Button, { size: "small", danger: true, icon: _jsx(CloseCircleOutlined, {}), loading: dismissMutation.isPending }) }) })] })),
        },
    ];
    // Calculate statistics
    const totalRecommendations = recommendations.length;
    const highPriorityCount = recommendations.filter(r => r.priority === 'high').length;
    const avgConfidence = recommendations.length > 0
        ? recommendations.reduce((sum, r) => sum + r.confidence, 0) / recommendations.length
        : 0;
    const avgImpact = recommendations.length > 0
        ? recommendations.reduce((sum, r) => sum + r.impact_score, 0) / recommendations.length
        : 0;
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx(Title, { level: 2, style: { margin: 0 }, children: "AI Preporuke" }), _jsx(Text, { type: "secondary", children: "Inteligentne preporuke za optimizaciju operacija magacina" })] }), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Ukupno preporuka", value: totalRecommendations, valueStyle: { color: '#1890ff' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Visok prioritet", value: highPriorityCount, valueStyle: { color: '#ff4d4f' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Prose\u010Dna pouzdanost", value: Math.round(avgConfidence * 100), suffix: "%", valueStyle: { color: '#52c41a' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Prose\u010Dni uticaj", value: Math.round(avgImpact), suffix: "%", valueStyle: { color: '#722ed1' } }) }) })] }), avgConfidence > 0.8 && (_jsx(Alert, { message: "\uD83E\uDD16 AI sistem je visoko pouzdan", description: `Prosečna pouzdanost preporuka je ${Math.round(avgConfidence * 100)}%. Preporuke su bazirane na analizi istorijskih podataka i trenutnih metrika.`, type: "success", showIcon: true, style: { marginBottom: '24px' } })), _jsx(Card, { title: "Preporuke za optimizaciju", extra: _jsx(Button, { icon: _jsx(PlayCircleOutlined, {}), onClick: () => refetch(), loading: isLoading, children: "Osve\u017Ei" }), children: _jsx(Table, { columns: columns, dataSource: recommendations, rowKey: "id", loading: isLoading, pagination: {
                        pageSize: 10,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total, range) => `${range[0]}-${range[1]} od ${total} preporuka`
                    } }) }), _jsx(Modal, { title: "\u0160ta-ako simulacija", open: simulationModalVisible, onCancel: () => {
                    setSimulationModalVisible(false);
                    setSimulationData(null);
                    setSelectedRecommendation(null);
                }, footer: null, width: 800, children: simulationData && (_jsxs("div", { children: [_jsxs(Card, { style: { marginBottom: '16px' }, children: [_jsx(Title, { level: 4, children: simulationData.recommendation.title }), _jsx(Paragraph, { children: simulationData.recommendation.description }), _jsxs(Space, { children: [_jsx(Tag, { color: getPriorityColor(simulationData.recommendation.priority), children: simulationData.recommendation.priority.toUpperCase() }), getConfidenceBadge(simulationData.recommendation.confidence)] })] }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsxs(Card, { title: "Pre primjene", size: "small", children: [_jsxs("div", { style: { marginBottom: '16px' }, children: [_jsx(Text, { strong: true, children: "Optere\u0107enje po radnjama:" }), simulationData.before_simulation.store_metrics.map(store => (_jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { style: { display: 'flex', justifyContent: 'space-between' }, children: [_jsx("span", { children: store.store_name }), _jsxs("span", { children: [Math.round(store.load_index * 100), "%"] })] }), _jsx(Progress, { percent: Math.round(store.load_index * 100), size: "small", status: store.load_index > 0.8 ? 'exception' : 'normal' })] }, store.store_id)))] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Ukupne metrike:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Prose\u010Dna efikasnost: ", Math.round(simulationData.before_simulation.overall_metrics.average_efficiency * 100), "%"] }), _jsxs("div", { children: ["Prose\u010Dno neaktivno vreme: ", Math.round(simulationData.before_simulation.overall_metrics.average_idle_time * 100), "%"] }), _jsxs("div", { children: ["Ukupno radnika: ", simulationData.before_simulation.overall_metrics.total_workers] })] })] })] }) }), _jsx(Col, { span: 12, children: _jsxs(Card, { title: "Posle primjene", size: "small", children: [_jsxs("div", { style: { marginBottom: '16px' }, children: [_jsx(Text, { strong: true, children: "Optere\u0107enje po radnjama:" }), simulationData.after_simulation.store_metrics.map(store => (_jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { style: { display: 'flex', justifyContent: 'space-between' }, children: [_jsx("span", { children: store.store_name }), _jsxs("span", { children: [Math.round(store.load_index * 100), "%"] })] }), _jsx(Progress, { percent: Math.round(store.load_index * 100), size: "small", status: store.load_index > 0.8 ? 'exception' : 'normal' })] }, store.store_id)))] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Ukupne metrike:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Prose\u010Dna efikasnost: ", Math.round(simulationData.after_simulation.overall_metrics.average_efficiency * 100), "%"] }), _jsxs("div", { children: ["Prose\u010Dno neaktivno vreme: ", Math.round(simulationData.after_simulation.overall_metrics.average_idle_time * 100), "%"] }), _jsxs("div", { children: ["Ukupno radnika: ", simulationData.after_simulation.overall_metrics.total_workers] })] })] })] }) })] }), _jsx(Card, { title: "O\u010Dekivana pobolj\u0161anja", style: { marginTop: '16px' }, children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 8, children: _jsx(Statistic, { title: "Balans optere\u0107enja", value: simulationData.improvement_metrics.load_balance_improvement, suffix: "%", valueStyle: { color: '#52c41a' } }) }), _jsx(Col, { span: 8, children: _jsx(Statistic, { title: "Efikasnost", value: simulationData.improvement_metrics.efficiency_improvement, suffix: "%", valueStyle: { color: '#1890ff' } }) }), _jsx(Col, { span: 8, children: _jsx(Statistic, { title: "Vreme izvr\u0161enja", value: simulationData.improvement_metrics.completion_time_improvement, suffix: "%", valueStyle: { color: '#722ed1' } }) })] }) }), _jsx("div", { style: { marginTop: '24px', textAlign: 'center' }, children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", size: "large", icon: _jsx(CheckCircleOutlined, {}), onClick: () => {
                                            handleApply(simulationData.recommendation.id);
                                            setSimulationModalVisible(false);
                                        }, loading: applyMutation.isPending, children: "Primijeni preporuku" }), _jsx(Button, { size: "large", onClick: () => setSimulationModalVisible(false), children: "Zatvori" })] }) })] })) })] }));
};
export default AIRecommendationsPage;
