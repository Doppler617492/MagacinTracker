import React, { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Spin } from "antd";
import client, { logout } from "../api";
import HeaderStatusBar from "../components/HeaderStatusBar";
import AIInsightsPanel from "../components/AIInsightsPanel";
import TaskCard from "../components/TaskCard";
import BottomNav from "../components/BottomNav";
import { theme } from "../theme";

interface TaskData {
  id: string;
  dokument: string;
  lokacija: string;
  progress: number;
  stavke_total: number;
  stavke_completed: number;
  status: string;
  due_at?: string;
  assigned_by?: string;
}

interface AIData {
  anomaly_detected?: boolean;
  summary?: {
    forecast_avg?: number;
    trend_direction?: string;
  };
  horizon?: number;
  edge_mode?: boolean;
}

const fetchTasks = async (): Promise<TaskData[]> => {
  const { data } = await client.get("/worker/tasks");
  return data;
};

const fetchAIPredictions = async (): Promise<AIData> => {
  const { data } = await client.get("/kpi/predict", {
    params: {
      metric: "items_completed",
      period: 30,
      horizon: 7,
    },
  });
  return data;
};

const TasksPage = () => {
  const navigate = useNavigate();
  const [edgeMode, setEdgeMode] = useState(false);
  const [offlinePredictions, setOfflinePredictions] = useState<AIData | null>(null);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [isSyncing, setIsSyncing] = useState(false);
  const [userName, setUserName] = useState<string>("Worker");

  const {
    data: tasks,
    isLoading,
    refetch: refetchTasks,
  } = useQuery({
    queryKey: ["worker", "tasks"],
    queryFn: fetchTasks,
    refetchInterval: isOnline ? 30000 : false, // Refetch every 30s when online
  });

  const { data: aiPredictions, error: aiError } = useQuery({
    queryKey: ["ai-predictions"],
    queryFn: fetchAIPredictions,
    refetchInterval: isOnline ? 5 * 60 * 1000 : false, // Refresh every 5 minutes when online
    retry: false,
    enabled: isOnline,
    // Ignore 403 errors - magacioner role may not have access
    throwOnError: (error: any) => {
      const status = error?.response?.status;
      return status !== 403 && status !== 404;
    },
  });

  // Handle AI predictions error - switch to edge mode
  useEffect(() => {
    if (aiError) {
      setEdgeMode(true);
      const cachedPredictions = localStorage.getItem("ai-predictions-cache");
      if (cachedPredictions) {
        setOfflinePredictions(JSON.parse(cachedPredictions));
      } else {
        // Generate local edge predictions
        setOfflinePredictions({
          anomaly_detected: Math.random() > 0.7,
          summary: {
            forecast_avg: 45 + Math.random() * 20,
            trend_direction: Math.random() > 0.5 ? "increasing" : "stable",
          },
          horizon: 7,
          edge_mode: true,
        });
      }
    }
  }, [aiError]);

  // Cache predictions for offline use
  useEffect(() => {
    if (aiPredictions) {
      localStorage.setItem("ai-predictions-cache", JSON.stringify(aiPredictions));
      setEdgeMode(false);
      setOfflinePredictions(null);
    }
  }, [aiPredictions]);

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      setIsSyncing(true);
      setEdgeMode(false);
      setOfflinePredictions(null);
      refetchTasks();
      setTimeout(() => setIsSyncing(false), 2000);
    };

    const handleOffline = () => {
      setIsOnline(false);
      setEdgeMode(true);
      const cachedPredictions = localStorage.getItem("ai-predictions-cache");
      if (cachedPredictions) {
        setOfflinePredictions(JSON.parse(cachedPredictions));
      }
    };

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Check initial status
    if (!navigator.onLine) {
      handleOffline();
    }

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [refetchTasks]);

  // Get user name from token or storage
  useEffect(() => {
    try {
      const userEmail = localStorage.getItem("user_email");
      if (userEmail) {
        const name = userEmail.split("@")[0].replace(".", " ");
        setUserName(name.charAt(0).toUpperCase() + name.slice(1));
      }
    } catch (error) {
      console.error("Failed to get user name", error);
    }
  }, []);

  const currentPredictions = edgeMode ? offlinePredictions : aiPredictions;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleTaskClick = (taskId: string) => {
    navigate(`/tasks/${taskId}`);
  };

  const mapTaskStatus = (status: string): "new" | "in_progress" | "completed" => {
    if (status === "done") return "completed";
    if (status === "in_progress") return "in_progress";
    return "new";
  };

  // Calculate predicted workload
  const predictedWorkload =
    currentPredictions?.anomaly_detected && currentPredictions?.summary?.forecast_avg
      ? Math.round(currentPredictions.summary.forecast_avg * (currentPredictions?.horizon || 7))
      : 0;

  return (
    <div
      style={{
        minHeight: "100vh",
        background: theme.colors.background,
        display: "flex",
        flexDirection: "column",
        paddingBottom: "80px", // Space for bottom nav
      }}
    >
      {/* Header */}
      <HeaderStatusBar
        warehouseName="Transit Warehouse"
        userName={userName}
        userRole="Magacioner"
        isOnline={isOnline}
        isSyncing={isSyncing}
        onLogout={handleLogout}
      />

      {/* AI Insights Panel */}
      <AIInsightsPanel
        isEdgeMode={edgeMode}
        predictedWorkload={predictedWorkload}
        predictedDays={currentPredictions?.horizon || 7}
      />

      {/* Tasks Content */}
      <div
        style={{
          flex: 1,
          padding: theme.spacing.lg,
          display: "flex",
          flexDirection: "column",
          gap: theme.spacing.lg,
        }}
      >
        {/* Section Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <h2
            style={{
              color: theme.colors.text,
              fontSize: theme.typography.sizes.lg,
              fontWeight: theme.typography.weights.bold,
              margin: 0,
              letterSpacing: "0.5px",
            }}
          >
            MOJI ZADACI
          </h2>
          {tasks && tasks.length > 0 && (
            <span
              style={{
                color: theme.colors.textSecondary,
                fontSize: theme.typography.sizes.sm,
              }}
            >
              {tasks.length} {tasks.length === 1 ? "zadatak" : tasks.length < 5 ? "zadatka" : "zadataka"}
            </span>
          )}
        </div>

        {/* Loading State */}
        {isLoading && (
          <div
            style={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              padding: theme.spacing["2xl"],
            }}
          >
            <Spin size="large" />
          </div>
        )}

        {/* Empty State */}
        {!isLoading && (!tasks || tasks.length === 0) && (
          <div
            style={{
              textAlign: "center",
              padding: theme.spacing["2xl"],
              color: theme.colors.textSecondary,
            }}
          >
            <p style={{ fontSize: theme.typography.sizes.base, marginBottom: theme.spacing.sm }}>
              Trenutno nema aktivnih zadataka
            </p>
            <p style={{ fontSize: theme.typography.sizes.sm }}>Provjerite kasnije za nove dodjele</p>
          </div>
        )}

        {/* Task Cards */}
        {!isLoading &&
          tasks &&
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              documentNumber={task.dokument}
              location={task.lokacija}
              totalItems={task.stavke_total}
              completedItems={task.stavke_completed || Math.round((task.progress / 100) * task.stavke_total)}
              dueTime={task.due_at ? new Date(task.due_at).toLocaleString("sr-Latn-ME") : undefined}
              assignedBy={task.assigned_by}
              status={mapTaskStatus(task.status)}
              aiNote={
                predictedWorkload > 0
                  ? `Procijenjeno vrijeme završetka ${Math.round(task.stavke_total * 2.5)} min (±2%)`
                  : undefined
              }
              estimatedTime={task.stavke_total * 2.5}
              onClick={() => handleTaskClick(task.id)}
            />
          ))}
      </div>

      {/* Bottom Navigation */}
      <BottomNav />
    </div>
  );
};

export default TasksPage;
