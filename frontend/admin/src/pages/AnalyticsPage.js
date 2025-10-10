import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from 'react';
import { Card, Row, Col, Select, DatePicker, Button, Statistic, message, Space, Divider } from 'antd';
import { Line, Column, Pie } from '@ant-design/charts';
import { DownloadOutlined, ReloadOutlined, RobotOutlined, EyeOutlined, WarningOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import dayjs from 'dayjs';
import { getDailyStats, getTopWorkers, getManualCompletion, exportCSV, getKPIForecast } from '../api';
import AIAssistantModal from '../components/AIAssistantModal';
const { RangePicker } = DatePicker;
const { Option } = Select;
const AnalyticsPage = () => {
    const [filters, setFilters] = useState({
        period: '7d',
        dateRange: [dayjs().subtract(7, 'day'), dayjs()]
    });
    const [aiModalVisible, setAiModalVisible] = useState(false);
    const [showForecast, setShowForecast] = useState(false);
    // KPI Data Queries
    const { data: dailyStats, isLoading: dailyLoading, refetch: refetchDaily } = useQuery({
        queryKey: ['dailyStats', filters],
        queryFn: () => getDailyStats({
            radnja: filters.radnja,
            period: filters.period,
            radnik: filters.radnik
        }),
        staleTime: 5 * 60 * 1000, // 5 minutes
    });
    const { data: topWorkers, isLoading: workersLoading, refetch: refetchWorkers } = useQuery({
        queryKey: ['topWorkers', filters],
        queryFn: () => getTopWorkers({
            radnja: filters.radnja,
            period: filters.period
        }),
        staleTime: 5 * 60 * 1000,
    });
    const { data: manualCompletion, isLoading: manualLoading, refetch: refetchManual } = useQuery({
        queryKey: ['manualCompletion', filters],
        queryFn: () => getManualCompletion({
            radnja: filters.radnja,
            period: filters.period
        }),
        staleTime: 5 * 60 * 1000,
    });
    // Forecast Query
    const { data: forecastData, isLoading: forecastLoading } = useQuery({
        queryKey: ['forecast', filters, showForecast],
        queryFn: () => getKPIForecast({
            metric: 'items_completed',
            period: filters.period === '1d' ? 7 :
                filters.period === '7d' ? 30 :
                    filters.period === '30d' ? 90 : 90,
            horizon: 7,
            radnja_id: filters.radnja,
            radnik_id: filters.radnik
        }),
        enabled: showForecast,
        staleTime: 10 * 60 * 1000, // 10 minutes cache for forecasts
    });
    const handleFilterChange = (key, value) => {
        setFilters(prev => ({ ...prev, [key]: value }));
    };
    const handleDateRangeChange = (dates) => {
        if (dates && dates.length === 2) {
            setFilters(prev => ({
                ...prev,
                dateRange: dates,
                period: undefined // Clear period when custom date range is selected
            }));
        }
    };
    const handleExportCSV = async () => {
        try {
            const blob = await exportCSV({
                radnja: filters.radnja,
                period: filters.period,
                radnik: filters.radnik
            });
            // Create download link
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `magacin-report-${dayjs().format('YYYY-MM-DD')}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            message.success('CSV izvezen uspešno!');
        }
        catch (error) {
            message.error('Greška pri izvozu CSV-a');
            console.error('Export error:', error);
        }
    };
    const handleRefresh = () => {
        refetchDaily();
        refetchWorkers();
        refetchManual();
        message.success('Podaci osveženi');
    };
    const handleForecastToggle = () => {
        setShowForecast(!showForecast);
        if (!showForecast) {
            message.info('🔮 Prognoza je uključena - prikazuju se predviđanja za narednih 7 dana');
        }
    };
    // Prepare chart data with forecast
    const prepareChartData = () => {
        const baseData = dailyStats?.data || [];
        if (!showForecast || !forecastData) {
            return baseData;
        }
        // Combine actual and forecast data
        const combinedData = [
            ...baseData.map(item => ({
                ...item,
                type: 'actual'
            })),
            ...forecastData.forecast.map(item => ({
                date: item.date,
                value: item.value,
                type: 'forecast',
                lower_bound: item.lower_bound,
                upper_bound: item.upper_bound
            }))
        ];
        return combinedData;
    };
    // Chart configurations
    const lineConfig = {
        data: prepareChartData(),
        xField: 'date',
        yField: 'value',
        seriesField: 'type',
        smooth: true,
        animation: {
            appear: {
                animation: 'path-in',
                duration: 1000,
            },
        },
        color: (type) => {
            switch (type) {
                case 'actual': return '#1890ff';
                case 'forecast': return '#722ed1';
                default: return '#1890ff';
            }
        },
        legend: {
            position: 'top',
        },
        xAxis: {
            type: 'time',
            tickCount: 5,
        },
        yAxis: {
            label: {
                formatter: (v) => `${v}`,
            },
        },
        // Add confidence interval area for forecast
        ...(showForecast && forecastData && {
            area: {
                style: {
                    fill: 'l(270) 0:#722ed1 1:#722ed1',
                    fillOpacity: 0.1,
                },
            },
        }),
    };
    const columnConfig = {
        data: topWorkers?.data || [],
        xField: 'worker_name',
        yField: 'completed_tasks',
        color: '#1890ff',
        animation: {
            appear: {
                animation: 'scale-in-y',
                duration: 1000,
            },
        },
        xAxis: {
            label: {
                autoRotate: false,
            },
        },
        yAxis: {
            label: {
                formatter: (v) => `${v}`,
            },
        },
    };
    const pieConfig = {
        data: manualCompletion?.data || [],
        angleField: 'value',
        colorField: 'type',
        radius: 0.8,
        label: {
            type: 'outer',
            content: '{name}: {percentage}',
        },
        color: ['#1890ff', '#52c41a'],
        animation: {
            appear: {
                animation: 'scale-in',
                duration: 1000,
            },
        },
    };
    const isLoading = dailyLoading || workersLoading || manualLoading;
    return (_jsxs("div", { style: { padding: '24px' }, children: [_jsxs("div", { style: { marginBottom: '24px' }, children: [_jsx("h1", { style: { margin: 0, fontSize: '24px', fontWeight: 600 }, children: "Analitika" }), _jsx("p", { style: { margin: '8px 0 0 0', color: '#666' }, children: "Pregled KPI metrika i performansi sistema" })] }), _jsx(Card, { style: { marginBottom: '24px' }, children: _jsxs(Row, { gutter: [16, 16], align: "middle", children: [_jsx(Col, { children: _jsxs(Space, { children: [_jsx("span", { children: "Radnja:" }), _jsxs(Select, { placeholder: "Sve radnje", style: { width: 150 }, allowClear: true, value: filters.radnja, onChange: (value) => handleFilterChange('radnja', value), children: [_jsx(Option, { value: "pantheon", children: "Pantheon" }), _jsx(Option, { value: "maxi", children: "Maxi" }), _jsx(Option, { value: "idea", children: "Idea" })] })] }) }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx("span", { children: "Period:" }), _jsxs(Select, { style: { width: 120 }, value: filters.period, onChange: (value) => handleFilterChange('period', value), children: [_jsx(Option, { value: "1d", children: "1 dan" }), _jsx(Option, { value: "7d", children: "7 dana" }), _jsx(Option, { value: "30d", children: "30 dana" }), _jsx(Option, { value: "90d", children: "90 dana" })] })] }) }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx("span", { children: "Datum:" }), _jsx(RangePicker, { value: filters.dateRange, onChange: handleDateRangeChange, format: "DD.MM.YYYY" })] }) }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx("span", { children: "Radnik:" }), _jsxs(Select, { placeholder: "Svi radnici", style: { width: 150 }, allowClear: true, value: filters.radnik, onChange: (value) => handleFilterChange('radnik', value), children: [_jsx(Option, { value: "marko.sef@example.com", children: "Marko \u0160ef" }), _jsx(Option, { value: "ana.radnik@example.com", children: "Ana Radnik" }), _jsx(Option, { value: "petar.worker@example.com", children: "Petar Worker" })] })] }) }), _jsx(Col, { flex: "auto" }), _jsx(Col, { children: _jsxs(Space, { children: [_jsx(Button, { icon: _jsx(ReloadOutlined, {}), onClick: handleRefresh, loading: isLoading, children: "Osve\u017Ei" }), _jsx(Button, { type: "primary", icon: _jsx(DownloadOutlined, {}), onClick: handleExportCSV, children: "Izvezi CSV" }), _jsx(Button, { type: showForecast ? "primary" : "default", icon: _jsx(EyeOutlined, {}), onClick: handleForecastToggle, loading: forecastLoading, style: showForecast ? {} : { borderColor: '#722ed1', color: '#722ed1' }, children: "\uD83D\uDD2E Prika\u017Ei prognozu" }), _jsx(Button, { type: "default", icon: _jsx(RobotOutlined, {}), onClick: () => setAiModalVisible(true), style: { borderColor: '#1890ff', color: '#1890ff' }, children: "AI Asistent" })] }) })] }) }), showForecast && forecastData?.anomaly_detected && (_jsx(Card, { style: { marginBottom: '24px', borderColor: '#ff4d4f' }, children: _jsxs("div", { style: { display: 'flex', alignItems: 'center', gap: '12px' }, children: [_jsx(WarningOutlined, { style: { color: '#ff4d4f', fontSize: '20px' } }), _jsxs("div", { children: [_jsx("div", { style: { fontWeight: 500, color: '#ff4d4f' }, children: "\u26A0\uFE0F Upozorenje: Detektovane anomalije u performansama!" }), _jsxs("div", { style: { color: '#666', fontSize: '14px' }, children: ["Sistem je detektovao ", forecastData.anomalies.length, " anomalija u poslednjih ", forecastData.horizon, " dana. Preporu\u010Duje se provera operativnih procesa."] })] })] }) })), _jsxs(Row, { gutter: [16, 16], style: { marginBottom: '24px' }, children: [_jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Ukupno stavki", value: dailyStats?.summary?.total_items || 0, valueStyle: { color: '#1890ff' } }), showForecast && forecastData && (_jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: ["\uD83D\uDD2E Prognoza: ", Math.round(forecastData.summary.forecast_avg), " stavki/dan"] }))] }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Manual %", value: dailyStats?.summary?.manual_percentage || 0, suffix: "%", valueStyle: { color: '#faad14' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsx(Card, { children: _jsx(Statistic, { title: "Prosje\u010Dno vrijeme", value: dailyStats?.summary?.avg_time_per_task || 0, suffix: "min", valueStyle: { color: '#52c41a' } }) }) }), _jsx(Col, { xs: 24, sm: 12, lg: 6, children: _jsxs(Card, { children: [_jsx(Statistic, { title: "Aktivni radnici", value: topWorkers?.summary?.active_workers || 0, valueStyle: { color: '#722ed1' } }), showForecast && forecastData && (_jsxs("div", { style: { fontSize: '12px', color: '#666', marginTop: '8px' }, children: ["Trend: ", forecastData.summary.trend_direction] }))] }) })] }), _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { xs: 24, lg: 16, children: _jsx(Card, { title: _jsxs("div", { children: ["Dnevni trend", showForecast && forecastData && (_jsxs("div", { style: { fontSize: '12px', color: '#666', fontWeight: 'normal' }, children: ["\uD83D\uDD2E Prognoza za narednih ", forecastData.horizon, " dana (pouzdanost: ", Math.round(forecastData.confidence * 100), "%)"] }))] }), loading: dailyLoading || forecastLoading, children: _jsx("div", { style: { height: '300px' }, children: dailyStats?.data?.length > 0 ? (_jsx(Line, { ...lineConfig })) : (_jsx("div", { style: {
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#999'
                                    }, children: "Nema podataka za prikaz" })) }) }) }), _jsx(Col, { xs: 24, lg: 8, children: _jsx(Card, { title: "Top 5 radnika", loading: workersLoading, children: _jsx("div", { style: { height: '300px' }, children: topWorkers?.data?.length > 0 ? (_jsx(Column, { ...columnConfig })) : (_jsx("div", { style: {
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#999'
                                    }, children: "Nema podataka za prikaz" })) }) }) })] }), _jsxs(Row, { gutter: [16, 16], style: { marginTop: '16px' }, children: [_jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Ru\u010Dne potvrde vs Skeniranje", loading: manualLoading, children: _jsx("div", { style: { height: '300px' }, children: manualCompletion?.data?.length > 0 ? (_jsx(Pie, { ...pieConfig })) : (_jsx("div", { style: {
                                        height: '100%',
                                        display: 'flex',
                                        alignItems: 'center',
                                        justifyContent: 'center',
                                        color: '#999'
                                    }, children: "Nema podataka za prikaz" })) }) }) }), _jsx(Col, { xs: 24, lg: 12, children: _jsx(Card, { title: "Detaljni pregled", children: _jsxs("div", { style: { padding: '16px 0' }, children: [_jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Statistic, { title: "Skenirano stavki", value: manualCompletion?.summary?.scanned_items || 0, valueStyle: { color: '#52c41a' } }) }), _jsx(Col, { span: 12, children: _jsx(Statistic, { title: "Ru\u010Dno potvr\u0111eno", value: manualCompletion?.summary?.manual_items || 0, valueStyle: { color: '#faad14' } }) })] }), _jsx(Divider, {}), _jsxs(Row, { gutter: [16, 16], children: [_jsx(Col, { span: 12, children: _jsx(Statistic, { title: "Ukupno zadataka", value: dailyStats?.summary?.total_tasks || 0, valueStyle: { color: '#1890ff' } }) }), _jsx(Col, { span: 12, children: _jsx(Statistic, { title: "Zavr\u0161eno zadataka", value: dailyStats?.summary?.completed_tasks || 0, valueStyle: { color: '#52c41a' } }) })] })] }) }) })] }), _jsx(AIAssistantModal, { visible: aiModalVisible, onClose: () => setAiModalVisible(false), filters: {
                    radnja: filters.radnja,
                    period: filters.period,
                    radnik: filters.radnik
                } })] }));
};
export default AnalyticsPage;
