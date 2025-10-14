import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { io } from "socket.io-client";
import { useQuery } from "@tanstack/react-query";
import client, { ensureAuth } from "./api";
import PrivacyToggle from "./components/PrivacyToggle";
import MilestoneAnimation from "./components/MilestoneAnimation";
const socketEndpoint = import.meta.env.VITE_SOCKET_URL ?? window.location.origin;
const queueStatusLabels = {
    assigned: "Dodijeljeno",
    in_progress: "U toku",
    done: "Završeno",
    blocked: "Blokirano"
};
const fetchSnapshot = async () => {
    const { data } = await client.get("/tv/snapshot");
    return data;
};
const fetchForecast = async () => {
    const { data } = await client.get("/kpi/predict", {
        params: {
            metric: "items_completed",
            period: 30,
            horizon: 7
        }
    });
    return data;
};
const fetchAIRecommendations = async () => {
    const { data } = await client.post("/ai/recommendations");
    return data;
};
const App = () => {
    const [ready, setReady] = useState(false);
    const [isPrivate, setIsPrivate] = useState(false);
    const [previousKpi, setPreviousKpi] = useState(null);
    const { data, refetch } = useQuery({ queryKey: ["tv", "snapshot"], queryFn: fetchSnapshot, enabled: ready });
    const { data: forecastData } = useQuery({
        queryKey: ["tv", "forecast"],
        queryFn: fetchForecast,
        enabled: ready,
        refetchInterval: 5 * 60 * 1000 // Refresh every 5 minutes
    });
    const { data: aiRecommendations = [] } = useQuery({
        queryKey: ["tv", "ai-recommendations"],
        queryFn: fetchAIRecommendations,
        enabled: ready,
        refetchInterval: 2 * 60 * 1000 // Refresh every 2 minutes
    });
    useEffect(() => {
        ensureAuth()
            .then(() => setReady(true))
            .catch((error) => console.error("TV auth bootstrap failed", error));
    }, []);
    useEffect(() => {
        if (!ready)
            return;
        let socket = null;
        const connectSocket = async () => {
            socket = io(socketEndpoint, { path: "/ws" });
            socket.on("connect", () => {
                console.info("Socket connected", socket?.id);
            });
            socket.on("tv_delta", () => {
                refetch();
            });
            socket.on("disconnect", () => {
                console.info("Socket disconnected");
            });
        };
        connectSocket();
        return () => {
            socket?.disconnect();
        };
    }, [ready, refetch]);
    // Track previous KPI values for milestone animations
    useEffect(() => {
        if (data?.kpi && previousKpi) {
            // KPI values have changed, animations will trigger
        }
        if (data?.kpi) {
            setPreviousKpi(data.kpi);
        }
    }, [data?.kpi, previousKpi]);
    if (!ready || !data) {
        return _jsx("div", { className: "tv-root", children: "U\u010Ditavanje dashboard-a..." });
    }
    const leaderboard = data.leaderboard;
    const queue = data.queue;
    const kpi = data.kpi;
    const getDisplayName = (name) => {
        if (isPrivate) {
            return name.split(' ').map(n => n.charAt(0) + '*'.repeat(n.length - 1)).join(' ');
        }
        return name;
    };
    return (_jsxs("div", { className: "tv-root", children: [forecastData?.anomaly_detected && (_jsxs(motion.div, { className: "anomaly-overlay", initial: { opacity: 0, y: -50 }, animate: { opacity: 1, y: 0 }, exit: { opacity: 0, y: -50 }, style: {
                    position: 'fixed',
                    top: '20px',
                    left: '50%',
                    transform: 'translateX(-50%)',
                    background: 'linear-gradient(135deg, #ff4d4f, #ff7875)',
                    color: 'white',
                    padding: '16px 24px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(255, 77, 79, 0.3)',
                    zIndex: 1000,
                    textAlign: 'center',
                    minWidth: '400px'
                }, children: [_jsx("div", { style: { fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }, children: "\u26A0\uFE0F Upozorenje: Produktivnost opada!" }), _jsxs("div", { style: { fontSize: '14px', opacity: 0.9 }, children: ["Sistem je detektovao anomaliju u performansama. O\u010Dekivano: ", Math.round(forecastData.summary.forecast_avg), " stavki/dan"] })] })), _jsxs("div", { className: "tv-controls", children: [_jsxs("div", { className: "brand-header", children: [_jsx("div", { className: "brand-logo", children: "\uD83D\uDCE6" }), _jsxs("div", { className: "brand-text", children: [_jsx("h1", { children: "Magacin Track" }), _jsx("p", { children: "Real-time Dashboard" })] })] }), _jsx(PrivacyToggle, { onPrivacyChange: setIsPrivate })] }), _jsxs("header", { className: "tv-header", children: [_jsxs("div", { className: "metric", children: [_jsx(MilestoneAnimation, { value: kpi.total_tasks_today, previousValue: previousKpi?.total_tasks_today || 0, milestone: 50, label: "Ukupno zadataka", icon: "\uD83D\uDCCB" }), forecastData && (_jsxs("div", { style: {
                                    fontSize: '12px',
                                    color: '#666',
                                    marginTop: '4px',
                                    opacity: 0.8
                                }, children: ["\uD83D\uDD2E Prognoza: ", Math.round(forecastData.summary.forecast_avg), "/dan"] }))] }), _jsx("div", { className: "metric", children: _jsx(MilestoneAnimation, { value: Math.round(kpi.completed_percentage), previousValue: Math.round(previousKpi?.completed_percentage || 0), milestone: 80, label: "Zavr\u0161eno", icon: "\u2705" }) }), _jsx("div", { className: "metric", children: _jsx(MilestoneAnimation, { value: kpi.active_workers, previousValue: previousKpi?.active_workers || 0, milestone: 10, label: "Aktivni radnici", icon: "\uD83D\uDC65" }) }), _jsxs("div", { className: "metric", children: [_jsx(MilestoneAnimation, { value: kpi.partial_items, previousValue: previousKpi?.partial_items || 0, milestone: 25, label: "Djelimi\u010Dne stavke", icon: "\u26A0\uFE0F" }), _jsxs("span", { className: "metric-sub", children: ["Razlika: ", Math.round(kpi.shortage_qty), " kom"] })] }), _jsxs("div", { className: "metric", children: [_jsx("span", { className: "metric-label", children: "Vrijeme do kraja smjene" }), _jsxs("span", { className: "metric-value", children: [Math.round(kpi.shift_ends_in_minutes), " min"] })] })] }), aiRecommendations.length > 0 && (_jsx(motion.div, { className: "load-balance-monitor", initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, style: {
                    background: 'linear-gradient(135deg, #1890ff, #40a9ff)',
                    color: 'white',
                    padding: '16px 24px',
                    margin: '0 24px 24px 24px',
                    borderRadius: '8px',
                    boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease'
                }, whileHover: { scale: 1.02 }, onClick: () => {
                    // In a real implementation, this would open the AI recommendations page
                    console.log('AI recommendations clicked');
                }, children: _jsxs("div", { style: { display: 'flex', alignItems: 'center', justifyContent: 'space-between' }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: '18px', fontWeight: 'bold', marginBottom: '4px' }, children: "\u2699\uFE0F AI predla\u017Ee preraspodjelu zadataka" }), _jsxs("div", { style: { fontSize: '14px', opacity: 0.9 }, children: [aiRecommendations.length, " preporuka za optimizaciju optere\u0107enja"] })] }), _jsx("div", { style: { fontSize: '24px' }, children: "\uD83E\uDD16" })] }) })), _jsxs("main", { className: "tv-content", children: [_jsxs("section", { className: "leaderboard", children: [_jsx("h1", { children: "Top magacioneri" }), _jsx("div", { className: "leaderboard-list", children: leaderboard.map((entry, index) => (_jsxs(motion.div, { className: "leaderboard-card", initial: { opacity: 0, y: 20 }, animate: { opacity: 1, y: 0 }, transition: { delay: index * 0.05 }, children: [_jsxs("div", { className: "leaderboard-rank", children: ["#", index + 1] }), _jsx("div", { className: "leaderboard-name", children: getDisplayName(entry.display_name) }), _jsxs("div", { className: "leaderboard-progress", children: [_jsx("div", { className: "progress-bar", children: _jsx("div", { className: "progress", style: { width: `${Math.min(entry.task_completion, 100)}%` } }) }), _jsxs("span", { children: [Math.round(entry.task_completion), "%"] })] }), _jsxs("div", { className: "leaderboard-stats", children: [_jsxs("span", { children: [entry.items_completed, " stavki"] }), _jsxs("span", { children: [entry.speed_per_hour.toFixed(1), "/h"] })] })] }, entry.user_id))) })] }), _jsxs("section", { className: "queue", children: [_jsx("h2", { children: "Queue po radnjama" }), _jsx("div", { className: "queue-list", children: queue.map((item) => (_jsxs("div", { className: "queue-card", children: [_jsx("div", { className: "queue-title", children: item.dokument }), _jsx("div", { className: "queue-sub", children: item.radnja }), _jsxs("div", { className: "queue-status", children: ["Status: ", queueStatusLabels[item.status] ?? item.status] }), _jsxs("div", { className: "queue-partial", children: ["Djelimi\u010Dno: ", item.partial_items, "/", item.total_items] }), _jsxs("div", { className: "queue-shortage", children: ["Razlika: ", Math.round(item.shortage_qty), " kom"] }), _jsxs("div", { className: "queue-workers", children: ["Dodijeljeni: ", item.assigned_to.length > 0 ? item.assigned_to.map((worker) => worker.slice(0, 8)).join(", ") : "—"] })] }, item.dokument))) })] })] })] }));
};
export default App;
