import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect, useRef } from 'react';
import { Modal, Input, Button, List, Card, Typography, Space, Spin, message, Row, Col } from 'antd';
import { SendOutlined, RobotOutlined, HistoryOutlined, BulbOutlined, BarChartOutlined, LineOutlined, PieChartOutlined } from '@ant-design/icons';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Line, Column } from '@ant-design/charts';
import { processAIQuery, getAISuggestions, getAIHistory } from '../api';
const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;
const AIAssistantModal = ({ visible, onClose, filters }) => {
    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);
    // Fetch suggestions and history
    const { data: suggestions } = useQuery({
        queryKey: ['ai-suggestions'],
        queryFn: getAISuggestions,
        enabled: visible,
    });
    const { data: history } = useQuery({
        queryKey: ['ai-history'],
        queryFn: () => getAIHistory(5),
        enabled: visible,
    });
    // AI Query mutation
    const aiQueryMutation = useMutation({
        mutationFn: (request) => processAIQuery(request),
        onSuccess: (response) => {
            const aiMessage = {
                id: Date.now().toString(),
                type: 'ai',
                content: response.answer,
                timestamp: new Date(response.timestamp),
                confidence: response.confidence,
                chart_data: response.chart_data,
                data: response.data
            };
            setMessages(prev => [...prev, aiMessage]);
            setIsLoading(false);
        },
        onError: (error) => {
            message.error('Greška pri obradi upita. Pokušajte ponovo.');
            setIsLoading(false);
        }
    });
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };
    useEffect(() => {
        scrollToBottom();
    }, [messages]);
    const handleSendMessage = async () => {
        if (!inputValue.trim() || isLoading)
            return;
        const userMessage = {
            id: Date.now().toString(),
            type: 'user',
            content: inputValue,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);
        // Prepare context from filters
        const context = {
            days: filters?.period === '1d' ? 1 :
                filters?.period === '7d' ? 7 :
                    filters?.period === '30d' ? 30 : 7,
            language: 'sr'
        };
        if (filters?.radnja) {
            context.radnja_id = filters.radnja;
        }
        if (filters?.radnik) {
            context.radnik_id = filters.radnik;
        }
        aiQueryMutation.mutate({
            query: inputValue,
            context
        });
    };
    const handleSuggestionClick = (suggestion) => {
        setInputValue(suggestion);
    };
    const handleHistoryClick = (historyItem) => {
        const userMessage = {
            id: Date.now().toString(),
            type: 'user',
            content: historyItem.query,
            timestamp: new Date(historyItem.timestamp)
        };
        const aiMessage = {
            id: (Date.now() + 1).toString(),
            type: 'ai',
            content: historyItem.answer,
            timestamp: new Date(historyItem.timestamp),
            confidence: historyItem.confidence
        };
        setMessages([userMessage, aiMessage]);
    };
    const renderChart = (chartData) => {
        if (!chartData || !chartData.data || chartData.data.length === 0) {
            return _jsx(Text, { type: "secondary", children: "Nema podataka za prikaz grafikona" });
        }
        const commonConfig = {
            data: chartData.data,
            animation: {
                appear: {
                    animation: 'path-in',
                    duration: 1000,
                },
            },
        };
        switch (chartData.type) {
            case 'line':
                return (_jsx(Line, { ...commonConfig, xField: chartData.x_field, yField: chartData.y_field, smooth: true, color: "#1890ff" }));
            case 'bar':
                return (_jsx(Column, { ...commonConfig, xField: chartData.x_field, yField: chartData.y_field, color: "#52c41a" }));
            case 'pie':
                return (_jsx(Column, { ...commonConfig, angleField: chartData.angle_field, colorField: chartData.color_field, radius: 0.8, label: {
                        type: 'outer',
                        content: '{name}: {percentage}',
                    } }));
            default:
                return _jsx(Text, { type: "secondary", children: "Nepoznat tip grafikona" });
        }
    };
    const getChartIcon = (chartType) => {
        switch (chartType) {
            case 'line': return _jsx(LineOutlined, {});
            case 'bar': return _jsx(BarChartOutlined, {});
            case 'pie': return _jsx(PieChartOutlined, {});
            default: return _jsx(BarChartOutlined, {});
        }
    };
    return (_jsx(Modal, { title: _jsxs(Space, { children: [_jsx(RobotOutlined, { style: { color: '#1890ff' } }), _jsx("span", { children: "AI Analytics Asistent" })] }), open: visible, onCancel: onClose, footer: null, width: 800, style: { top: 20 }, bodyStyle: { height: '70vh', display: 'flex', flexDirection: 'column' }, children: _jsxs(Row, { gutter: 16, style: { height: '100%' }, children: [_jsxs(Col, { span: 16, style: { display: 'flex', flexDirection: 'column' }, children: [_jsxs("div", { style: {
                                flex: 1,
                                overflowY: 'auto',
                                padding: '16px 0',
                                border: '1px solid #f0f0f0',
                                borderRadius: '6px',
                                marginBottom: '16px'
                            }, children: [messages.length === 0 ? (_jsxs("div", { style: { textAlign: 'center', padding: '40px 20px', color: '#999' }, children: [_jsx(RobotOutlined, { style: { fontSize: '48px', marginBottom: '16px' } }), _jsx(Title, { level: 4, children: "Dobrodo\u0161li u AI Analytics Asistent" }), _jsxs(Paragraph, { children: ["Postavite pitanje o va\u0161im KPI podacima na prirodnom jeziku.", _jsx("br", {}), "Primer: \"Ko je bio najefikasniji radnik pro\u0161le sedmice?\""] })] })) : (messages.map((message) => (_jsx("div", { style: {
                                        marginBottom: '16px',
                                        padding: '0 16px',
                                        display: 'flex',
                                        justifyContent: message.type === 'user' ? 'flex-end' : 'flex-start'
                                    }, children: _jsxs("div", { style: {
                                            maxWidth: '70%',
                                            padding: '12px 16px',
                                            borderRadius: '12px',
                                            backgroundColor: message.type === 'user' ? '#1890ff' : '#f5f5f5',
                                            color: message.type === 'user' ? '#fff' : '#000'
                                        }, children: [_jsx("div", { style: { marginBottom: '8px' }, children: message.content }), message.confidence && (_jsxs("div", { style: { fontSize: '12px', opacity: 0.7 }, children: ["Pouzdanost: ", Math.round(message.confidence * 100), "%"] })), message.chart_data && (_jsxs("div", { style: { marginTop: '16px' }, children: [_jsxs("div", { style: { marginBottom: '8px', display: 'flex', alignItems: 'center' }, children: [getChartIcon(message.chart_data.type), _jsx(Text, { style: { marginLeft: '8px', fontWeight: 500 }, children: "Grafi\u010Dki prikaz" })] }), _jsx("div", { style: { height: '200px' }, children: renderChart(message.chart_data) })] }))] }) }, message.id)))), isLoading && (_jsxs("div", { style: { padding: '16px', textAlign: 'center' }, children: [_jsx(Spin, {}), _jsx(Text, { style: { marginLeft: '8px' }, children: "AI asistent razmi\u0161lja..." })] })), _jsx("div", { ref: messagesEndRef })] }), _jsxs("div", { style: { display: 'flex', gap: '8px' }, children: [_jsx(TextArea, { value: inputValue, onChange: (e) => setInputValue(e.target.value), placeholder: "Postavite pitanje o va\u0161im KPI podacima...", rows: 2, onPressEnter: (e) => {
                                        if (!e.shiftKey) {
                                            e.preventDefault();
                                            handleSendMessage();
                                        }
                                    }, disabled: isLoading }), _jsx(Button, { type: "primary", icon: _jsx(SendOutlined, {}), onClick: handleSendMessage, loading: isLoading, disabled: !inputValue.trim(), children: "Po\u0161alji" })] })] }), _jsxs(Col, { span: 8, children: [_jsx(Card, { title: _jsxs(Space, { children: [_jsx(BulbOutlined, {}), _jsx("span", { children: "Predlozi" })] }), size: "small", style: { marginBottom: '16px' }, children: _jsx(List, { size: "small", dataSource: suggestions?.suggestions || [], renderItem: (item) => (_jsx(List.Item, { style: { padding: '4px 0' }, children: _jsx(Button, { type: "link", size: "small", onClick: () => handleSuggestionClick(item), style: { textAlign: 'left', padding: 0, height: 'auto' }, children: item }) })) }) }), _jsx(Card, { title: _jsxs(Space, { children: [_jsx(HistoryOutlined, {}), _jsx("span", { children: "Istorija" })] }), size: "small", children: _jsx(List, { size: "small", dataSource: history?.history || [], renderItem: (item) => (_jsx(List.Item, { style: { padding: '4px 0' }, children: _jsxs("div", { children: [_jsx(Button, { type: "link", size: "small", onClick: () => handleHistoryClick(item), style: { textAlign: 'left', padding: 0, height: 'auto' }, children: item.query }), _jsx("div", { style: { fontSize: '11px', color: '#999', marginTop: '2px' }, children: new Date(item.timestamp).toLocaleString('sr-RS') })] }) })) }) })] })] }) }));
};
export default AIAssistantModal;
