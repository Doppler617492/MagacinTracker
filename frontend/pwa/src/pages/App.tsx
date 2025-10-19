import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import HomePageWhite from "./HomePageWhite";
import UnifiedTasksPage from "./UnifiedTasksPage";
import TaskDetailPageWhite from "./TaskDetailPageWhite";
import StockCountPageWhite from "./StockCountPageWhite";
import ScanPickPageWhite from "./ScanPickPageWhite";
import LookupPageWhite from "./LookupPageWhite";
import ExceptionsPageWhite from "./ExceptionsPageWhite";
import ReportsPageWhite from "./ReportsPageWhite";
import SettingsPageWhite from "./SettingsPageWhite";
import LoginPageWhite from "./LoginPageWhite";
import OfflineQueueComponent from "../components/OfflineQueue";
import { Route, Routes, Navigate, useLocation } from "react-router-dom";
import { ensureAuth, isAuthenticated } from "../api";
import { HeaderProvider } from "../contexts/HeaderContext";
import { useTranslation } from "../hooks/useTranslation";

const App = () => {
  const t = useTranslation('sr');
  const [ready, setReady] = useState(false);
  const [authChecked, setAuthChecked] = useState(0); // Force re-check
  const location = useLocation();

  useEffect(() => {
    ensureAuth()
      .then(() => setReady(true))
      .catch((error) => {
        // Expected on first load before login; keep noise low
        console.warn("Auth bootstrap skipped (no token)");
        setReady(true); // Still show the app, but user will see login page
      });
  }, []);

  // Re-check auth state when location changes (after navigation)
  useEffect(() => {
    setAuthChecked(prev => prev + 1);
  }, [location]);

  if (!ready) {
    return <div className="card">{t.login.preparingApp}</div>;
  }

  const authenticated = isAuthenticated();

  return (
    <HeaderProvider>
      <Routes>
        <Route 
          path="/login" 
          element={
            authenticated ? <Navigate to="/" replace /> : <LoginPageWhite />
          } 
        />
        <Route 
          element={
            authenticated ? <Layout /> : <Navigate to="/login" replace />
          }
        >
          <Route index element={<HomePageWhite />} />
          <Route path="tasks" element={<UnifiedTasksPage />} />
          <Route path="tasks/:id" element={<TaskDetailPageWhite />} />
          <Route path="scan-pick" element={<ScanPickPageWhite />} />
          <Route path="manual-entry" element={<UnifiedTasksPage />} />
          <Route path="stock-count" element={<StockCountPageWhite />} />
          <Route path="lookup" element={<LookupPageWhite />} />
          <Route path="exceptions" element={<ExceptionsPageWhite />} />
          <Route path="history" element={<ReportsPageWhite />} />
          <Route path="reports" element={<ReportsPageWhite />} />
          <Route path="settings" element={<SettingsPageWhite />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <OfflineQueueComponent />
    </HeaderProvider>
  );
};

export default App;
