import { useEffect, useState } from "react";
import { Layout, Spin, Menu } from "antd";
import { Outlet, Route, Routes, Link, useLocation } from "react-router-dom";
import DashboardPage from "./DashboardPage";
import TrebovanjaPage from "./TrebovanjaPage";
import SchedulerPage from "./SchedulerPage";
import CatalogPage from "./CatalogPage";
import ImportPage from "./ImportPage";
import { ensureAuth } from "../api";

const { Header, Content } = Layout;

const AdminLayout = () => {
  const location = useLocation();
  
  const menuItems = [
    {
      key: "/",
      label: <Link to="/">Dashboard</Link>
    },
    {
      key: "/trebovanja",
      label: <Link to="/trebovanja">Trebovanja</Link>
    },
    {
      key: "/scheduler",
      label: <Link to="/scheduler">Scheduler</Link>
    },
    {
      key: "/catalog",
      label: <Link to="/catalog">Katalog</Link>
    },
    {
      key: "/import",
      label: <Link to="/import">Uvoz</Link>
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
          style={{ minWidth: "400px" }}
        />
      </Header>
      <Content style={{ padding: "24px" }}>
        <Outlet />
      </Content>
    </Layout>
  );
};

const App = () => {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    ensureAuth()
      .then(() => setReady(true))
      .catch((error) => {
        console.error("Auth bootstrap failed", error);
      });
  }, []);

  if (!ready) {
    return (
      <Layout style={{ minHeight: "100vh", justifyContent: "center", alignItems: "center" }}>
        <Spin tip="Prijavljivanje..." size="large" />
      </Layout>
    );
  }

  return (
    <Routes>
      <Route element={<AdminLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="trebovanja" element={<TrebovanjaPage />} />
        <Route path="scheduler" element={<SchedulerPage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="import" element={<ImportPage />} />
      </Route>
    </Routes>
  );
};

export default App;
