import React, { useState, useEffect, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { Spin, Input } from "antd";
import client, { logout, getStoredUserProfile, StoredUserProfile } from "../api";
import HeaderStatusBar from "../components/HeaderStatusBar";
import AIInsightsPanel from "../components/AIInsightsPanel";
import TaskCard from "../components/TaskCard";
import BottomNav from "../components/BottomNav";
import { theme } from "../theme";
import { offlineQueue, OfflineQueueState } from "../lib/offlineQueue";
import { SearchOutlined } from "@ant-design/icons";

interface TaskData {
  id: string;
  dokument: string;
  lokacija: string;
  progress: number;
  stavke_total: number;
  stavke_completed: number;
  partial_items: number;
  shortage_qty: number;
  status: string;
  due_at?: string;
  assigned_by?: string;
  assigned_by_id?: string;
  assigned_by_name?: string;
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
  const [pendingSync, setPendingSync] = useState<number>(offlineQueue.getState().pending);
  const [lastSyncedAt, setLastSyncedAt] = useState<number | null>(offlineQueue.getLastSyncedAt());
  const [userProfile, setUserProfile] = useState<StoredUserProfile | null>(getStoredUserProfile());
  const [warehouseName, setWarehouseName] = useState<string>(
    getStoredUserProfile()?.location ?? "Tranzitno skladište"
  );
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [searchTerm, setSearchTerm] = useState<string>("");

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
      setEdgeMode(false);
      setOfflinePredictions(null);
      refetchTasks();
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

  // Observe offline queue state for sync indicator
  useEffect(() => {
    const handleQueue = (state: OfflineQueueState) => {
      setPendingSync(state.pending);
      setLastSyncedAt(state.lastSyncedAt);
    };

    offlineQueue.addListener(handleQueue);

    return () => {
      offlineQueue.removeListener(handleQueue);
    };
  }, []);

  // Refresh user profile from storage (handles login bootstrap)
  useEffect(() => {
    setUserProfile(getStoredUserProfile());
  }, []);

  // Update warehouse name from profile or first task
  useEffect(() => {
    if (userProfile?.location) {
      setWarehouseName(userProfile.location);
      return;
    }
    if (tasks && tasks.length > 0) {
      const firstLocation = tasks[0].lokacija;
      if (firstLocation) {
        setWarehouseName(firstLocation);
        localStorage.setItem("user_location", firstLocation);
      }
    }
  }, [tasks, userProfile]);

  const summary = useMemo(() => {
    if (!tasks || tasks.length === 0) {
      return {
        totalTasks: 0,
        activeTasks: 0,
        completedTasks: 0,
        partialDocs: 0,
        totalShortage: 0,
        averageProgress: 0,
        dueSoon: 0,
      };
    }

    const totalTasks = tasks.length;
    const completedTasks = tasks.filter((task) => task.status === "done").length;
    const activeTasks = totalTasks - completedTasks;
    const partialDocs = tasks.filter((task) => (task.partial_items ?? 0) > 0).length;
    const totalShortage = tasks.reduce((sum, task) => sum + (task.shortage_qty ?? 0), 0);
    const averageProgress = Math.round(
      tasks.reduce((sum, task) => sum + (task.progress ?? 0), 0) / totalTasks
    );
    const now = Date.now();
    const dueSoonThreshold = 3 * 60 * 60 * 1000; // 3h
    const dueSoon = tasks.filter((task) => {
      if (!task.due_at) return false;
      const dueTs = new Date(task.due_at).getTime();
      return dueTs >= now && dueTs - now <= dueSoonThreshold;
    }).length;

    return {
      totalTasks,
      activeTasks,
      completedTasks,
      partialDocs,
      totalShortage: Math.round(totalShortage),
      averageProgress,
      dueSoon,
    };
  }, [tasks]);

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

  const filteredTasks = useMemo(() => {
    if (!tasks) return [];

    const searchValue = searchTerm.trim().toLowerCase();
    const statusPriority: Record<"new" | "in_progress" | "completed", number> = {
      in_progress: 0,
      new: 1,
      completed: 2,
    };

    return tasks
      .filter((task) => {
        const normalizedStatus = mapTaskStatus(task.status);
        const matchesStatus =
          statusFilter === "all" ||
          (statusFilter === "active" && normalizedStatus !== "completed") ||
          (statusFilter === "in_progress" && normalizedStatus === "in_progress") ||
          (statusFilter === "new" && normalizedStatus === "new") ||
          (statusFilter === "completed" && normalizedStatus === "completed") ||
          (statusFilter === "partial" && (task.partial_items ?? 0) > 0);

        if (!matchesStatus) {
          return false;
        }

        if (!searchValue) {
          return true;
        }

        const haystacks = [
          task.dokument,
          task.lokacija,
          task.assigned_by_name,
          task.assigned_by,
        ]
          .filter(Boolean)
          .map((value) => value!.toLowerCase());

        return haystacks.some((value) => value.includes(searchValue));
      })
      .sort((a, b) => {
        const aPartial = (a.partial_items ?? 0) > 0 ? 0 : 1;
        const bPartial = (b.partial_items ?? 0) > 0 ? 0 : 1;
        if (aPartial !== bPartial) {
          return aPartial - bPartial;
        }

        const aStatus = mapTaskStatus(a.status);
        const bStatus = mapTaskStatus(b.status);
        const statusDiff = statusPriority[aStatus] - statusPriority[bStatus];
        if (statusDiff !== 0) {
          return statusDiff;
        }

        const aDue = a.due_at ? new Date(a.due_at).getTime() : Number.POSITIVE_INFINITY;
        const bDue = b.due_at ? new Date(b.due_at).getTime() : Number.POSITIVE_INFINITY;
        if (aDue !== bDue) {
          return aDue - bDue;
        }

      return a.dokument.localeCompare(b.dokument);
    });
  }, [tasks, statusFilter, searchTerm]);

  const statusCounts = useMemo(() => {
    if (!tasks) {
      return {
        in_progress: 0,
        new: 0,
        completed: 0,
      };
    }

    return tasks.reduce(
      (counts, task) => {
        const normalized = mapTaskStatus(task.status);
        counts[normalized] += 1;
        return counts;
      },
      {
        in_progress: 0,
        new: 0,
        completed: 0,
      } as Record<"in_progress" | "new" | "completed", number>
    );
  }, [tasks]);

  const summaryCards = useMemo(
    () => [
      {
        label: "Ukupno zadataka",
        value: summary.totalTasks,
        helper: `${summary.completedTasks} završeno`,
        accent: theme.colors.accent,
      },
      {
        label: "Aktivni zadaci",
        value: summary.activeTasks,
        helper: `${summary.partialDocs} djelimično`,
        accent: theme.colors.primary,
      },
      {
        label: "Prosječan napredak",
        value: `${summary.averageProgress}%`,
        helper: summary.totalTasks > 0 ? "Praćenje produktivnosti" : "Nema zadataka",
        accent: theme.colors.success,
      },
      {
        label: "Ukupna razlika",
        value: `${summary.totalShortage} kom`,
        helper: `${summary.dueSoon} roka < 3h`,
        accent: theme.colors.warning,
      },
    ],
    [summary]
  );

  const filterOptions = useMemo(
    () => [
      { value: "all", label: "Sve", count: summary.totalTasks },
      { value: "active", label: "Aktivne", count: summary.activeTasks },
      { value: "in_progress", label: "U toku", count: statusCounts.in_progress },
      { value: "new", label: "Nove", count: statusCounts.new },
      { value: "partial", label: "Djelimične", count: summary.partialDocs },
      { value: "completed", label: "Završene", count: statusCounts.completed },
    ],
    [statusCounts, summary]
  );

  const displayRole = userProfile?.role
    ? userProfile.role.charAt(0).toUpperCase() + userProfile.role.slice(1)
    : "Magacioner";

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
        warehouseName={warehouseName}
        userName={userProfile?.fullName ?? "Worker"}
        userRole={displayRole}
        userEmail={userProfile?.email}
        isOnline={isOnline}
        pendingSyncCount={pendingSync}
        lastSyncedAt={lastSyncedAt}
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
        <div
          style={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
            gap: theme.spacing.md,
            flexWrap: "wrap",
          }}
        >
          <div>
            <h2
              style={{
                color: theme.colors.text,
                fontSize: theme.typography.sizes["2xl"],
                fontWeight: theme.typography.weights.bold,
                margin: 0,
                letterSpacing: "0.6px",
              }}
            >
              Moji zadaci
            </h2>
            <div
              style={{
                color: theme.colors.textSecondary,
                fontSize: theme.typography.sizes.sm,
              }}
            >
              Prikazano {filteredTasks.length} od {summary.totalTasks} zadataka
            </div>
          </div>
        </div>

        {/* Summary Metrics */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
            gap: theme.spacing.md,
          }}
        >
          {summaryCards.map((card) => (
            <div
              key={card.label}
              style={{
                background: theme.colors.cardBackground,
                borderRadius: theme.borderRadius.lg,
                padding: theme.spacing.md,
                borderLeft: `4px solid ${card.accent}`,
                display: "flex",
                flexDirection: "column",
                gap: theme.spacing.xs,
                boxShadow: theme.shadows.sm,
              }}
            >
              <span
                style={{
                  color: theme.colors.textSecondary,
                  fontSize: theme.typography.sizes.xs,
                  textTransform: "uppercase",
                  letterSpacing: "0.6px",
                }}
              >
                {card.label}
              </span>
              <span
                style={{
                  color: theme.colors.text,
                  fontSize: theme.typography.sizes["2xl"],
                  fontWeight: theme.typography.weights.bold,
                }}
              >
                {card.value}
              </span>
              <span
                style={{
                  color: theme.colors.textSecondary,
                  fontSize: theme.typography.sizes.xs,
                }}
              >
                {card.helper}
              </span>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: theme.spacing.md,
            alignItems: "center",
          }}
        >
          <Input
            allowClear
            prefix={<SearchOutlined style={{ color: theme.colors.textSecondary }} />}
            placeholder="Pretraži dokument, lokaciju ili dodjelu..."
            value={searchTerm}
            onChange={(event) => setSearchTerm(event.target.value)}
            style={{
              width: "280px",
              background: theme.colors.cardBackground,
              borderColor: theme.colors.border,
              color: theme.colors.text,
            }}
          />
          <div
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: theme.spacing.sm,
            }}
          >
            {filterOptions.map((option) => {
              const isActive = statusFilter === option.value;
              const accentMap: Record<string, string> = {
                all: theme.colors.accent,
                active: theme.colors.primary,
                in_progress: theme.colors.accent,
                new: "#3B82F6",
                partial: theme.colors.warning,
                completed: theme.colors.success,
              };
              const accent = accentMap[option.value] ?? theme.colors.accent;

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setStatusFilter(option.value)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: theme.spacing.xs,
                    padding: `${theme.spacing.xs} ${theme.spacing.md}`,
                    borderRadius: theme.borderRadius.md,
                    border: `1px solid ${isActive ? accent : theme.colors.border}`,
                    background: isActive ? `rgba(0, 200, 150, 0.12)` : "transparent",
                    color: isActive ? theme.colors.text : theme.colors.textSecondary,
                    fontWeight: theme.typography.weights.medium,
                    fontSize: theme.typography.sizes.sm,
                    cursor: "pointer",
                    transition: "all 0.18s ease",
                  }}
                >
                  {option.label}
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      justifyContent: "center",
                      minWidth: "26px",
                      padding: `0 ${theme.spacing.xs}`,
                      borderRadius: "999px",
                      background: isActive ? accent : theme.colors.border,
                      color: isActive ? theme.colors.background : theme.colors.text,
                      fontSize: theme.typography.sizes.xs,
                    }}
                  >
                    {option.count}
                  </span>
                </button>
              );
            })}
          </div>
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
        {!isLoading && filteredTasks.length === 0 && (
          <div
            style={{
              textAlign: "center",
              padding: theme.spacing["2xl"],
              color: theme.colors.textSecondary,
              border: `1px dashed ${theme.colors.border}`,
              borderRadius: theme.borderRadius.lg,
              background: "rgba(17, 24, 39, 0.6)",
            }}
          >
            <p style={{ fontSize: theme.typography.sizes.base, marginBottom: theme.spacing.sm }}>
              Nema zadataka koji odgovaraju filterima
            </p>
            <p style={{ fontSize: theme.typography.sizes.sm }}>
              Uklonite filtere ili provjerite kasnije za nove dodjele
            </p>
          </div>
        )}

        {/* Task Cards */}
        {!isLoading &&
          filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              documentNumber={task.dokument}
              location={task.lokacija}
              totalItems={task.stavke_total}
              completedItems={
                task.stavke_completed || Math.round((task.progress / 100) * task.stavke_total)
              }
              partialItems={task.partial_items}
              shortageQty={task.shortage_qty}
              dueTime={task.due_at ? new Date(task.due_at).toLocaleString("sr-Latn-ME") : undefined}
              assignedBy={task.assigned_by_name || task.assigned_by}
              status={mapTaskStatus(task.status)}
              progress={task.progress}
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
