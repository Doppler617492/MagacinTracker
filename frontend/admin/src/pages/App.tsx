import { useEffect, useState } from "react";
import { Layout, Menu, Button, Typography, Space, Dropdown } from "antd";
import { 
  LogoutOutlined, 
  DashboardOutlined, 
  ShoppingOutlined, 
  CalendarOutlined, 
  DatabaseOutlined, 
  ImportOutlined, 
  BarChartOutlined, 
  FileTextOutlined, 
  BulbOutlined, 
  RobotOutlined, 
  GlobalOutlined, 
  ThunderboltOutlined, 
  SettingOutlined, 
  TeamOutlined,
  WarningOutlined
} from "@ant-design/icons";
import { Outlet, Route, Routes, Link, useLocation } from "react-router-dom";
import DashboardPage from "./DashboardPage";
import TrebovanjaPage from "./TrebovanjaPage";
import SchedulerPage from "./SchedulerPage";
import CatalogPage from "./CatalogPage";
import ImportPage from "./ImportPage";
import AnalyticsPage from "./AnalyticsPage";
import TaskAnalyticsPage from "./TaskAnalyticsPage";
import ReportsPage from "./ReportsPage";
import AIRecommendationsPage from "./AIRecommendationsPage";
import AIModelDashboardPage from "./AIModelDashboardPage";
import GlobalAIHubPage from "./GlobalAIHubPage";
import LiveOpsDashboardPage from "./LiveOpsDashboardPage";
import GlobalOpsDashboardPage from "./GlobalOpsDashboardPage";
import UserManagementPage from "./UserManagementPage";
import ShortageReportsPage from "./ShortageReportsPage";
import TeamsPage from "./TeamsPage";
import LoginPage from "./LoginPage";
import { isAuthenticated, logout } from "../api";

type StoredUser = {
  id?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
  full_name?: string;
  role?: string;
};

const { Header, Content } = Layout;

const AdminLayout = () => {
  const location = useLocation();
  console.log("🔧 AdminLayout rendered, location:", location.pathname);
  
  const menuItems = [
    {
      key: "/",
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>
    },
    {
      key: "/trebovanja",
      icon: <ShoppingOutlined />,
      label: <Link to="/trebovanja">Trebovanja</Link>
    },
    {
      key: "/scheduler",
      icon: <CalendarOutlined />,
      label: <Link to="/scheduler">Scheduler</Link>
    },
    {
      key: "/catalog",
      icon: <DatabaseOutlined />,
      label: <Link to="/catalog">Katalog</Link>
    },
    {
      key: "/import",
      icon: <ImportOutlined />,
      label: <Link to="/import">Uvoz</Link>
    },
    {
      key: "/analytics",
      icon: <BarChartOutlined />,
      label: <Link to="/analytics">Analitika</Link>
    },
    {
      key: "/task-analytics",
      icon: <BarChartOutlined />,
      label: <Link to="/task-analytics">Analitika zadataka</Link>
    },
    {
      key: "/reports",
      icon: <FileTextOutlined />,
      label: <Link to="/reports">Izvještaji</Link>
    },
    {
      key: "/shortages",
      icon: <WarningOutlined />,
      label: <Link to="/shortages">Manjkovi</Link>
    },
    {
      key: "/ai-recommendations",
      icon: <BulbOutlined />,
      label: <Link to="/ai-recommendations">AI Preporuke</Link>
    },
    {
      key: "/ai-models",
      icon: <RobotOutlined />,
      label: <Link to="/ai-models">AI Modeli</Link>
    },
    {
      key: "/global-ai-hub",
      icon: <GlobalOutlined />,
      label: <Link to="/global-ai-hub">Global AI Hub</Link>
    },
    {
      key: "/live-ops",
      icon: <ThunderboltOutlined />,
      label: <Link to="/live-ops">Live Ops</Link>
    },
    {
      key: "/global-ops",
      icon: <SettingOutlined />,
      label: <Link to="/global-ops">Global Ops</Link>
    },
    {
      key: "/teams",
      icon: <TeamOutlined />,
      label: <Link to="/teams">Timovi</Link>
    },
    {
      key: "/users",
      icon: <TeamOutlined />,
      label: <Link to="/users">Korisnici</Link>
    }
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ color: "#fff", fontWeight: 600, fontSize: "18px" }}>Magacin Admin</div>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[location.pathname]}
          items={menuItems}
          style={{ flex: 1, minWidth: "400px" }}
        />
        <Space size="large" align="center">
          <UserMenu />
        </Space>
      </Header>
      <Content style={{ padding: "24px" }}>
        <Outlet />
      </Content>
    </Layout>
  );
};

const UserBadge = () => {
  const [user, setUser] = useState<StoredUser | null>(null);
  useEffect(() => {
    try {
      const raw = localStorage.getItem("auth_user");
      if (raw) setUser(JSON.parse(raw));
    } catch {
      setUser(null);
    }
    // Fallback: if no user cached, try to fetch from /auth/me
    if (!localStorage.getItem("auth_user")) {
      fetchMe().then((me) => {
        if (me) {
          try {
            localStorage.setItem("auth_user", JSON.stringify(me));
            setUser(me);
          } catch {}
        }
      }).catch(() => void 0);
    }
  }, []);
  const displayName = user?.full_name || user?.first_name || user?.email || "Korisnik";
  const role = user?.role ? String(user.role).toUpperCase() : undefined;
  return (
    <Typography.Text style={{ color: "#fff" }}>
      {displayName}{role ? ` • ${role}` : ""}
    </Typography.Text>
  );
};

const UserMenu = () => {
  const [user, setUser] = useState<StoredUser | null>(null);
  useEffect(() => {
    try {
      const raw = localStorage.getItem("auth_user");
      if (raw) setUser(JSON.parse(raw));
    } catch {}
  }, []);
  const menuItems = [
    {
      key: "profile",
      label: (
        <div style={{ padding: 8 }}>
          <div style={{ fontWeight: 600 }}>{user?.full_name || user?.email || "Korisnik"}</div>
          <div style={{ opacity: 0.8, fontSize: 12 }}>{user?.role ? String(user.role).toUpperCase() : ""}</div>
        </div>
      ),
    },
    { type: "divider" as const },
    {
      key: "logout",
      label: <span onClick={logout}>Odjava</span>,
    },
  ];
  return (
    <Dropdown
      menu={{ items: menuItems }}
      placement="bottomRight"
      trigger={["click"]}
    >
      <div style={{ cursor: "pointer" }}>
        <UserBadge />
      </div>
    </Dropdown>
  );
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
    return <LoginPage onLoginSuccess={() => setAuthenticated(true)} />;
  }
  
  console.log("✅ Authenticated, showing admin layout");

  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="trebovanja" element={<TrebovanjaPage />} />
        <Route path="scheduler" element={<SchedulerPage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="import" element={<ImportPage />} />
        <Route path="analytics" element={<AnalyticsPage />} />
        <Route path="task-analytics" element={<TaskAnalyticsPage />} />
        <Route path="reports" element={<ReportsPage />} />
        <Route path="ai-recommendations" element={<AIRecommendationsPage />} />
        <Route path="ai-models" element={<AIModelDashboardPage />} />
        <Route path="global-ai-hub" element={<GlobalAIHubPage />} />
        <Route path="live-ops" element={<LiveOpsDashboardPage />} />
        <Route path="global-ops" element={<GlobalOpsDashboardPage />} />
        <Route path="teams" element={<TeamsPage />} />
        <Route path="users" element={<UserManagementPage />} />
        <Route path="shortages" element={<ShortageReportsPage />} />
      </Route>
    </Routes>
  );
};

export default App;
