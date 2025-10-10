import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import TaskDetailPage from "./TaskDetailPage";
import TasksPage from "./TasksPage";
import ReportsPage from "./ReportsPage";
import SettingsPage from "./SettingsPage";
import LoginPage from "./LoginPage";
import OfflineQueueComponent from "../components/OfflineQueue";
import { Route, Routes, Navigate, useLocation } from "react-router-dom";
import { ensureAuth, isAuthenticated } from "../api";

const App = () => {
  const [ready, setReady] = useState(false);
  const [authChecked, setAuthChecked] = useState(0); // Force re-check
  const location = useLocation();

  useEffect(() => {
    ensureAuth()
      .then(() => setReady(true))
      .catch((error) => {
        console.error("Auth bootstrap failed", error);
        setReady(true); // Still show the app, but user will see login page
      });
  }, []);

  // Re-check auth state when location changes (after navigation)
  useEffect(() => {
    setAuthChecked(prev => prev + 1);
  }, [location]);

  if (!ready) {
    return <div className="card">Priprema aplikacije...</div>;
  }

  const authenticated = isAuthenticated();

  return (
    <>
      <Routes>
        <Route 
          path="/login" 
          element={
            authenticated ? <Navigate to="/" replace /> : <LoginPage />
          } 
        />
        <Route 
          element={
            authenticated ? <Layout /> : <Navigate to="/login" replace />
          }
        >
          <Route index element={<TasksPage />} />
          <Route path="tasks/:id" element={<TaskDetailPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <OfflineQueueComponent />
    </>
  );
};

export default App;
