import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Row, Col, Statistic, Button, Space, Tag, Modal, Form, InputNumber, Select, message, Typography, Alert, Popconfirm } from 'antd';
import { PlayCircleOutlined, ReloadOutlined, BulbOutlined, RobotOutlined, BarChartOutlined, TrophyOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Line } from '@ant-design/charts';
import { getAIModelStatus, getAIModelPerformance, trainAIModel, resetAIModels } from '../api';
const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const AIModelDashboardPage = () => {
    const [trainingModalVisible, setTrainingModalVisible] = useState(false);
    const [form] = Form.useForm();
    const queryClient = useQueryClient();
    // Fetch AI model status and performance
    const { data: modelStatus, isLoading: statusLoading, refetch: refetchStatus } = useQuery({
        queryKey: ['ai-model-status'],
        queryFn: getAIModelStatus,
        refetchInterval: 30000, // Refresh every 30 seconds
    });
    const { data: modelPerformance, isLoading: performanceLoading } = useQuery({
        queryKey: ['ai-model-performance'],
        queryFn: getAIModelPerformance,
        refetchInterval: 60000, // Refresh every minute
    });
    // Training mutation
    const trainingMutation = useMutation({
        mutationFn: trainAIModel,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['ai-model-status'] });
            queryClient.invalidateQueries({ queryKey: ['ai-model-performance'] });
            setTrainingModalVisible(false);
            form.resetFields();
            message.success(`Model ${data.model_type} je uspešno treniran! Tačnost: ${Math.round(data.final_accuracy * 100)}%`);
        },
        onError: (error) => {
            message.error('Greška pri treniranju modela');
            console.error('Training error:', error);
        }
    });
    const resetMutation = useMutation({
        mutationFn: resetAIModels,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ai-model-status'] });
            queryClient.invalidateQueries({ queryKey: ['ai-model-performance'] });
            message.success('Svi AI modeli su resetovani');
        },
        onError: (error) => {
            message.error('Greška pri resetovanju modela');
            console.error('Reset error:', error);
        }
    });
    const handleStartTraining = () => {
        setTrainingModalVisible(true);
    };
    const handleTrainingSubmit = async (values) => {
        const trainingRequest = {
            model_type: values.model_type,
            epochs: values.epochs,
            learning_rate: values.learning_rate,
            batch_size: values.batch_size
        };
        trainingMutation.mutate(trainingRequest);
    };
    const handleResetModels = () => {
        resetMutation.mutate();
    };
    const getStatusColor = (status) => {
        switch (status) {
            case 'fully_trained': return 'green';
            case 'partially_trained': return 'orange';
            case 'not_trained': return 'red';
            default: return 'blue';
        }
    };
    const getStatusText = (status) => {
        switch (status) {
            case 'fully_trained': return 'Potpuno treniran';
            case 'partially_trained': return 'Delimično treniran';
            case 'not_trained': return 'Nije treniran';
            default: return 'Nepoznat';
        }
    };
    const getModelIcon = (modelType) => {
        switch (modelType) {
            case 'neural_network': return _jsx(BulbOutlined, { style: { color: '#1890ff' } });
            case 'reinforcement_learning': return _jsx(RobotOutlined, { style: { color: '#52c41a' } });
            default: return _jsx(BulbOutlined, {});
        }
    };
    // Prepare training history data for charts
    const prepareTrainingHistoryData = () => {
        if (!modelStatus?.neural_network?.training_status?.is_trained) {
            return [];
        }
        // Mock training history data (in production, this would come from the API)
        const epochs = Array.from({ length: 100 }, (_, i) => i + 1);
        return epochs.map(epoch => ({
            epoch,
            loss: Math.max(0.01, 0.5 * Math.exp(-epoch / 30) + 0.01),
            accuracy: Math.min(0.95, 0.3 + 0.6 * (1 - Math.exp(-epoch / 25)))
        }));
    };
    const trainingHistoryData = prepareTrainingHistoryData();
    // Chart configurations
    const lossChartConfig = {
        data: trainingHistoryData,
        xField: 'epoch',
        yField: 'loss',
        smooth: true,
        color: '#ff4d4f',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Epoch' },
        },
        yAxis: {
            title: { text: 'Loss' },
        },
    };
    const accuracyChartConfig = {
        data: trainingHistoryData,
        xField: 'epoch',
        yField: 'accuracy',
        smooth: true,
        color: '#52c41a',
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        xAxis: {
            title: { text: 'Epoch' },
        },
        yAxis: {
            title: { text: 'Accuracy' },
        },
    };
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx(Title, { level: 2, style: { margin: 0 }, children: "AI Model Dashboard" }), _jsx(Text, { type: "secondary", children: "Upravljanje i monitoring AI modela za optimizaciju magacina" })] }), _jsx(Card, { style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: 16, align: "middle", children: [_jsx(Col, { children: _jsxs(Space, { children: [_jsx(BulbOutlined, { style: { fontSize: '24px', color: '#1890ff' } }), _jsxs("div", { children: [_jsx("div", { style: { fontSize: '18px', fontWeight: 500 }, children: "AI Model Status" }), _jsx("div", { style: { fontSize: '14px', color: '#666' }, children: modelStatus ? getStatusText(modelStatus.overall_status) : 'Učitavanje...' })] })] }) }), _jsx(Col, { flex: "auto" }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx(Tag, { color: getStatusColor(modelStatus?.overall_status || 'not_trained'), children: modelStatus ? getStatusText(modelStatus.overall_status) : 'Nepoznat' }), _jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: () => refetchStatus(), loading: statusLoading, children: "Osve\u017Ei" })] }) })] }) }), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Neural Network", value: modelStatus?.neural_network?.performance?.final_accuracy ? Math.round(modelStatus.neural_network.performance.final_accuracy * 100) : 0, suffix: "%", prefix: getModelIcon('neural_network'), valueStyle: { color: '#1890ff' } }), _jsx("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: modelStatus?.neural_network?.training_status?.is_trained ? 'Treniran' : 'Nije treniran' })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Reinforcement Learning", value: modelStatus?.reinforcement_learning?.performance?.average_reward ? Math.round(modelStatus.reinforcement_learning.performance.average_reward) : 0, suffix: " pts", prefix: getModelIcon('reinforcement_learning'), valueStyle: { color: '#52c41a' } }), _jsx("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: modelStatus?.reinforcement_learning?.training_status?.is_trained ? 'Treniran' : 'Nije treniran' })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Ukupno parametara", value: modelStatus?.neural_network?.architecture?.total_parameters || 0, prefix: _jsx(BarChartOutlined, {}), valueStyle: { color: '#722ed1' } }), _jsx("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: "Neural Network" })] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Epizode treniranja", value: modelStatus?.reinforcement_learning?.training_status?.total_episodes || 0, prefix: _jsx(TrophyOutlined, {}), valueStyle: { color: '#faad14' } }), _jsx("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: "Reinforcement Learning" })] }) })] }), modelStatus?.overall_status === 'not_trained' && (_jsx(Alert, { message: "\uD83E\uDD16 AI modeli nisu trenirani", description: "Za optimalne preporuke, potrebno je trenirati neuralnu mre\u017Eu i reinforcement learning model. Kliknite 'Treniraj sada' da po\u010Dnete.", type: "warning", showIcon: true, style: { marginBottom: '24px' }, action: _jsx(Button, { size: "small", type: "primary", onClick: handleStartTraining, children: "Treniraj sada" }) })), modelStatus?.neural_network?.training_status?.is_trained && (_jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Training Loss", loading: statusLoading, children: _jsx("div", { style: { height: '300px' }, children: trainingHistoryData.length > 0 ? (_jsx(Line, { ...lossChartConfig })) : (_jsx("div", { style: {
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#999'
                                    }, children: "Nema podataka o treniranju" })) }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Training Accuracy", loading: statusLoading, children: _jsx("div", { style: { height: '300px' }, children: trainingHistoryData.length > 0 ? (_jsx(Line, { ...accuracyChartConfig })) : (_jsx("div", { style: {
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#999'
                                    }, children: "Nema podataka o treniranju" })) }) }) })] })), _jsxs(Row, { gutter: 16, style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsxs(Card, { title: "Neural Network Model", loading: statusLoading, children: [_jsxs("div", { style: { marginBottom: '16px' }, children: [_jsx(Text, { strong: true, children: "Arhitektura:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Input: ", modelStatus?.neural_network?.architecture?.input_size || 0, " neurons"] }), _jsxs("div", { children: ["Hidden: ", modelStatus?.neural_network?.architecture?.hidden_size || 0, " neurons"] }), _jsxs("div", { children: ["Output: ", modelStatus?.neural_network?.architecture?.output_size || 0, " neurons"] })] })] }), _jsxs("div", { style: { marginBottom: '16px' }, children: [_jsx(Text, { strong: true, children: "Performanse:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Finalna ta\u010Dnost: ", modelStatus?.neural_network?.performance?.final_accuracy ? Math.round(modelStatus.neural_network.performance.final_accuracy * 100) : 0, "%"] }), _jsxs("div", { children: ["Najbolja ta\u010Dnost: ", modelStatus?.neural_network?.performance?.best_accuracy ? Math.round(modelStatus.neural_network.performance.best_accuracy * 100) : 0, "%"] }), _jsxs("div", { children: ["Finalni loss: ", modelStatus?.neural_network?.performance?.final_loss?.toFixed(4) || 'N/A'] })] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Status treniranja:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Sesije treniranja: ", modelStatus?.neural_network?.training_status?.training_sessions || 0] }), _jsxs("div", { children: ["Poslednje treniranje: ", modelStatus?.neural_network?.training_status?.last_trained ? new Date(modelStatus.neural_network.training_status.last_trained).toLocaleString('sr-RS') : 'Nikad'] })] })] })] }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsxs(Card, { title: "Reinforcement Learning Model", loading: statusLoading, children: [_jsxs("div", { style: { marginBottom: '16px' }, children: [_jsx(Text, { strong: true, children: "Konfiguracija:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["State size: ", modelStatus?.reinforcement_learning?.architecture?.state_size || 0] }), _jsxs("div", { children: ["Action size: ", modelStatus?.reinforcement_learning?.architecture?.action_size || 0] }), _jsxs("div", { children: ["Learning rate: ", modelStatus?.reinforcement_learning?.architecture?.learning_rate || 0] }), _jsxs("div", { children: ["Discount factor: ", modelStatus?.reinforcement_learning?.architecture?.discount_factor || 0] })] })] }), _jsxs("div", { style: { marginBottom: '16px' }, children: [_jsx(Text, { strong: true, children: "Performanse:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Prose\u010Dna nagrada: ", modelStatus?.reinforcement_learning?.performance?.average_reward?.toFixed(2) || 0] }), _jsxs("div", { children: ["Najbolja nagrada: ", modelStatus?.reinforcement_learning?.performance?.best_reward?.toFixed(2) || 0] }), _jsxs("div", { children: ["Epizoda konvergencije: ", modelStatus?.reinforcement_learning?.performance?.convergence_episode || 'N/A'] })] })] }), _jsxs("div", { children: [_jsx(Text, { strong: true, children: "Status treniranja:" }), _jsxs("div", { style: { marginTop: '8px' }, children: [_jsxs("div", { children: ["Ukupno epizoda: ", modelStatus?.reinforcement_learning?.training_status?.total_episodes || 0] }), _jsxs("div", { children: ["Poslednje treniranje: ", modelStatus?.reinforcement_learning?.training_status?.last_trained ? new Date(modelStatus.reinforcement_learning.training_status.last_trained).toLocaleString('sr-RS') : 'Nikad'] })] })] })] }) })] }), _jsx(Card, { children: _jsxs(Row, { gutter: 16, children: [_jsx(Col, { children: _jsx(Button, { type: "primary", size: "large", icon: _jsx(PlayCircleOutlined, {}), onClick: handleStartTraining, loading: trainingMutation.isPending, children: "Treniraj sada" }) }), _jsx(Col, { children: _jsx(Button, { size: "large", icon: _jsx(ReloadOutlined, {}), onClick: () => {
                                    refetchStatus();
                                    message.success('Status modela osvežen');
                                }, children: "Osve\u017Ei status" }) }), _jsx(Col, { children: _jsx(Popconfirm, { title: "Resetuj AI modele", description: "Da li ste sigurni da \u017Eelite da resetujete sve AI modele? Ovo \u0107e obrisati sve treniranje.", onConfirm: handleResetModels, okText: "Da", cancelText: "Ne", children: _jsx(Button, { size: "large", danger: true, icon: _jsx(ExclamationCircleOutlined, {}), loading: resetMutation.isPending, children: "Resetuj modele" }) }) })] }) }), _jsx(Modal, { title: "Treniraj AI Model", open: trainingModalVisible, onCancel: () => {
                    setTrainingModalVisible(false);
                    form.resetFields();
                }, footer: null, width: 600, children: _jsxs(Form, { form: form, layout: "vertical", onFinish: handleTrainingSubmit, initialValues: {
                        model_type: 'neural_network',
                        epochs: 100,
                        learning_rate: 0.001,
                        batch_size: 32
                    }, children: [_jsx(Form.Item, { name: "model_type", label: "Tip modela", rules: [{ required: true, message: 'Molimo odaberite tip modela' }], children: _jsxs(Select, { placeholder: "Odaberite tip modela", children: [_jsx(Option, { value: "neural_network", children: _jsxs(Space, { children: [_jsx(BulbOutlined, {}), _jsx("span", { children: "Neural Network (Predvi\u0111anje performansi)" })] }) }), _jsx(Option, { value: "reinforcement_learning", children: _jsxs(Space, { children: [_jsx(RobotOutlined, {}), _jsx("span", { children: "Reinforcement Learning (Adaptivna optimizacija)" })] }) })] }) }), _jsxs(Row, { gutter: 16, children: [_jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "epochs", label: "Broj epoha", rules: [{ required: true, message: 'Molimo unesite broj epoha' }], children: _jsx(InputNumber, { min: 10, max: 1000, style: { width: '100%' }, placeholder: "100" }) }) }), _jsx(Col, { span: 12, children: _jsx(Form.Item, { name: "learning_rate", label: "Learning rate", rules: [{ required: true, message: 'Molimo unesite learning rate' }], children: _jsx(InputNumber, { min: 0.0001, max: 0.1, step: 0.001, style: { width: '100%' }, placeholder: "0.001" }) }) })] }), _jsx(Form.Item, { name: "batch_size", label: "Batch size", rules: [{ required: true, message: 'Molimo unesite batch size' }], children: _jsx(InputNumber, { min: 8, max: 128, style: { width: '100%' }, placeholder: "32" }) }), _jsx(Alert, { message: "Treniranje mo\u017Ee potrajati", description: "Neural Network treniranje mo\u017Ee potrajati do 60 sekundi, Reinforcement Learning do 2 minuta.", type: "info", showIcon: true, style: { marginBottom: '16px' } }), _jsx(Form.Item, { children: _jsxs(Space, { children: [_jsx(Button, { type: "primary", htmlType: "submit", loading: trainingMutation.isPending, icon: _jsx(PlayCircleOutlined, {}), children: "Po\u010Dni treniranje" }), _jsx(Button, { onClick: () => setTrainingModalVisible(false), children: "Otka\u017Ei" })] }) })] }) })] }));
};
export default AIModelDashboardPage;
