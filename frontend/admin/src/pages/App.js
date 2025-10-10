import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { Layout, Menu, Button } from "antd";
import { LogoutOutlined, DashboardOutlined, ShoppingOutlined, CalendarOutlined, DatabaseOutlined, ImportOutlined, BarChartOutlined, FileTextOutlined, BulbOutlined, RobotOutlined, GlobalOutlined, ThunderboltOutlined, SettingOutlined, TeamOutlined } from "@ant-design/icons";
import { Outlet, Route, Routes, Link, useLocation } from "react-router-dom";
import DashboardPage from "./DashboardPage";
import TrebovanjaPage from "./TrebovanjaPage";
import SchedulerPage from "./SchedulerPage";
import CatalogPage from "./CatalogPage";
import ImportPage from "./ImportPage";
import AnalyticsPage from "./AnalyticsPage";
import ReportsPage from "./ReportsPage";
import AIRecommendationsPage from "./AIRecommendationsPage";
import AIModelDashboardPage from "./AIModelDashboardPage";
import GlobalAIHubPage from "./GlobalAIHubPage";
import LiveOpsDashboardPage from "./LiveOpsDashboardPage";
import GlobalOpsDashboardPage from "./GlobalOpsDashboardPage";
import UserManagementPage from "./UserManagementPage";
import LoginPage from "./LoginPage";
import { isAuthenticated, logout } from "../api";
const { Header, Content } = Layout;
const AdminLayout = () => {
    const location = useLocation();
    console.log("🔧 AdminLayout rendered, location:", location.pathname);
    const menuItems = [
        {
            key: "/",
            icon: _jsx(DashboardOutlined, {}),
            label: _jsx(Link, { to: "/", children: "Dashboard" })
        },
        {
            key: "/trebovanja",
            icon: _jsx(ShoppingOutlined, {}),
            label: _jsx(Link, { to: "/trebovanja", children: "Trebovanja" })
        },
        {
            key: "/scheduler",
            icon: _jsx(CalendarOutlined, {}),
            label: _jsx(Link, { to: "/scheduler", children: "Scheduler" })
        },
        {
            key: "/catalog",
            icon: _jsx(DatabaseOutlined, {}),
            label: _jsx(Link, { to: "/catalog", children: "Katalog" })
        },
        {
            key: "/import",
            icon: _jsx(ImportOutlined, {}),
            label: _jsx(Link, { to: "/import", children: "Uvoz" })
        },
        {
            key: "/analytics",
            icon: _jsx(BarChartOutlined, {}),
            label: _jsx(Link, { to: "/analytics", children: "Analitika" })
        },
        {
            key: "/reports",
            icon: _jsx(FileTextOutlined, {}),
            label: _jsx(Link, { to: "/reports", children: "Izvje\u0161taji" })
        },
        {
            key: "/ai-recommendations",
            icon: _jsx(BulbOutlined, {}),
            label: _jsx(Link, { to: "/ai-recommendations", children: "AI Preporuke" })
        },
        {
            key: "/ai-models",
            icon: _jsx(RobotOutlined, {}),
            label: _jsx(Link, { to: "/ai-models", children: "AI Modeli" })
        },
        {
            key: "/global-ai-hub",
            icon: _jsx(GlobalOutlined, {}),
            label: _jsx(Link, { to: "/global-ai-hub", children: "Global AI Hub" })
        },
        {
            key: "/live-ops",
            icon: _jsx(ThunderboltOutlined, {}),
            label: _jsx(Link, { to: "/live-ops", children: "Live Ops" })
        },
        {
            key: "/global-ops",
            icon: _jsx(SettingOutlined, {}),
            label: _jsx(Link, { to: "/global-ops", children: "Global Ops" })
        },
        {
            key: "/users",
            icon: _jsx(TeamOutlined, {}),
            label: _jsx(Link, { to: "/users", children: "Korisnici" })
        }
    ];
    return (_jsxs(Layout, { style: { minHeight: "100vh" }, children: [_jsxs(Header, { style: { display: "flex", alignItems: "center", justifyContent: "space-between" }, children: [_jsx("div", { style: { color: "#fff", fontWeight: 600, fontSize: "18px" }, children: "Magacin Admin" }), _jsx(Menu, { theme: "dark", mode: "horizontal", selectedKeys: [location.pathname], items: menuItems, style: { flex: 1, minWidth: "400px" } }), _jsx(Button, { type: "text", icon: _jsx(LogoutOutlined, {}), onClick: logout, style: { color: "#fff" }, children: "Odjava" })] }), _jsx(Content, { style: { padding: "24px" }, children: _jsx(Outlet, {}) })] }));
};
const App = () => {
    const [authenticated, setAuthenticated] = useState(isAuthenticated());
    console.log("🚀 App component rendering, authenticated:", authenticated);
    useEffect(() => {
        const authStatus = isAuthenticated();
        console.log("🔐 useEffect - auth status:", authStatus);
        setAuthenticated(authStatus);
    }, []);
    // Show login page if not authenticated
    if (!authenticated) {
        console.log("❌ Not authenticated, showing login page");
        return _jsx(LoginPage, { onLoginSuccess: () => setAuthenticated(true) });
    }
    console.log("✅ Authenticated, showing admin layout");
    return (_jsx(Routes, { children: _jsxs(Route, { element: _jsx(AdminLayout, {}), children: [_jsx(Route, { index: true, element: _jsx(DashboardPage, {}) }), _jsx(Route, { path: "trebovanja", element: _jsx(TrebovanjaPage, {}) }), _jsx(Route, { path: "scheduler", element: _jsx(SchedulerPage, {}) }), _jsx(Route, { path: "catalog", element: _jsx(CatalogPage, {}) }), _jsx(Route, { path: "import", element: _jsx(ImportPage, {}) }), _jsx(Route, { path: "analytics", element: _jsx(AnalyticsPage, {}) }), _jsx(Route, { path: "reports", element: _jsx(ReportsPage, {}) }), _jsx(Route, { path: "ai-recommendations", element: _jsx(AIRecommendationsPage, {}) }), _jsx(Route, { path: "ai-models", element: _jsx(AIModelDashboardPage, {}) }), _jsx(Route, { path: "global-ai-hub", element: _jsx(GlobalAIHubPage, {}) }), _jsx(Route, { path: "live-ops", element: _jsx(LiveOpsDashboardPage, {}) }), _jsx(Route, { path: "global-ops", element: _jsx(GlobalOpsDashboardPage, {}) }), _jsx(Route, { path: "users", element: _jsx(UserManagementPage, {}) })] }) }));
};
export default App;
