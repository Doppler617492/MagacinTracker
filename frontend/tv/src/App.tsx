import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { io, Socket } from "socket.io-client";
import { useQuery } from "@tanstack/react-query";
import client, { ensureAuth, getLiveDashboard, LiveDashboard } from "./api";
import PrivacyToggle from "./components/PrivacyToggle";
import MilestoneAnimation from "./components/MilestoneAnimation";

interface ForecastData {
  metric: string;
  horizon: number;
  confidence: number;
  anomaly_detected: boolean;
  anomalies: number[];
  trend: number;
  summary: {
    current_value: number;
    forecast_avg: number;
    trend_direction: string;
    trend_strength: number;
    confidence_score: number;
    anomaly_count: number;
  };
  generated_at: string;
}

interface LeaderboardEntry {
  user_id: string;
  display_name: string;
  items_completed: number;
  task_completion: number;
  speed_per_hour: number;
}

interface QueueEntry {
  dokument: string;
  radnja: string;
  status: string;
  assigned_to: string[];
  eta_minutes?: number | null;
  total_items: number;
  partial_items: number;
  shortage_qty: number;
}

interface KpiSnapshot {
  total_tasks_today: number;
  completed_percentage: number;
  active_workers: number;
  shift_ends_in_minutes: number;
  partial_items: number;
  shortage_qty: number;
}

interface TvSnapshot {
  generated_at: string;
  leaderboard: LeaderboardEntry[];
  queue: QueueEntry[];
  kpi: KpiSnapshot;
}

const socketEndpoint = import.meta.env.VITE_SOCKET_URL ?? window.location.origin;
const queueStatusLabels: Record<string, string> = {
  assigned: "Dodijeljeno",
  in_progress: "U toku",
  done: "Završeno",
  blocked: "Blokirano"
};

const fetchSnapshot = async (): Promise<TvSnapshot> => {
  const { data } = await client.get("/tv/snapshot");
  return data;
};

const fetchForecast = async (): Promise<ForecastData> => {
  const { data } = await client.get("/kpi/predict", {
    params: {
      metric: "items_completed",
      period: 30,
      horizon: 7
    }
  });
  return data;
};

const fetchAIRecommendations = async (): Promise<any[]> => {
  const { data } = await client.post("/ai/recommendations");
  return data;
};

const App = () => {
  const [ready, setReady] = useState(false);
  const [isPrivate, setIsPrivate] = useState(false);
  const [previousKpi, setPreviousKpi] = useState<KpiSnapshot | null>(null);
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

  const { data: liveDashboard } = useQuery<LiveDashboard>({ 
    queryKey: ["tv", "live-dashboard"], 
    queryFn: getLiveDashboard, 
    enabled: ready,
    refetchInterval: 15 * 1000 // Refresh every 15 seconds
  });

  useEffect(() => {
    ensureAuth()
      .then(() => setReady(true))
      .catch((error) => console.error("TV auth bootstrap failed", error));
  }, []);

  useEffect(() => {
    if (!ready) return;
    let socket: Socket | null = null;

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
    return <div className="tv-root">Učitavanje dashboard-a...</div>;
  }

  const leaderboard = data.leaderboard;
  const queue = data.queue;
  const kpi = data.kpi;

  const getDisplayName = (name: string) => {
    if (isPrivate) {
      return name.split(' ').map(n => n.charAt(0) + '*'.repeat(n.length - 1)).join(' ');
    }
    return name;
  };

  return (
    <div className="tv-root">
      {/* Anomaly Warning Overlay */}
      {forecastData?.anomaly_detected && (
        <motion.div
          className="anomaly-overlay"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -50 }}
          style={{
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
          }}
        >
          <div style={{ fontSize: '18px', fontWeight: 'bold', marginBottom: '8px' }}>
            ⚠️ Upozorenje: Produktivnost opada!
          </div>
          <div style={{ fontSize: '14px', opacity: 0.9 }}>
            Sistem je detektovao anomaliju u performansama. 
            Očekivano: {Math.round(forecastData.summary.forecast_avg)} stavki/dan
          </div>
        </motion.div>
      )}

      <div className="tv-controls">
        <div className="brand-header">
          <div className="brand-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 7V5C3 3.89543 3.89543 3 5 3H19C20.1046 3 21 3.89543 21 5V7M3 7V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V7M3 7H21M8 11H16M8 15H12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <div className="brand-text">
            <h1>Magacin Track</h1>
            <p>Real-time Operations Dashboard</p>
          </div>
          {liveDashboard?.shift_status.active_shift && (
            <div style={{ 
              marginLeft: 'auto', 
              fontSize: '18px', 
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '16px',
            }}>
              <span style={{ opacity: 0.8 }}>Aktivna Smjena:</span>
              <span style={{ 
                background: liveDashboard.shift_status.active_shift === 'A' ? '#2563eb' : '#059669',
                padding: '4px 16px',
                borderRadius: '8px',
              }}>
                Smjena {liveDashboard.shift_status.active_shift}
              </span>
              {(() => {
                const shiftData = liveDashboard.shift_status.active_shift === 'A' 
                  ? liveDashboard.shift_status.shift_a 
                  : liveDashboard.shift_status.shift_b;
                return shiftData?.countdown_formatted && (
                  <span style={{ fontFamily: 'monospace', fontSize: '20px' }}>
                    {shiftData.countdown_formatted}
                  </span>
                );
              })()}
            </div>
          )}
        </div>
        <PrivacyToggle onPrivacyChange={setIsPrivate} />
      </div>

      <header className="tv-header">
        <div className="metric">
          <MilestoneAnimation
            value={kpi.total_tasks_today}
            previousValue={previousKpi?.total_tasks_today || 0}
            milestone={50}
            label="Ukupno zadataka"
            icon="📋"
          />
          {forecastData && (
            <div style={{ 
              fontSize: '11px', 
              color: 'var(--text-muted)', 
              marginTop: '6px'
            }}>
              Prognoza: {Math.round(forecastData.summary.forecast_avg)}/dan
            </div>
          )}
        </div>
        <div className="metric">
          <MilestoneAnimation
            value={Math.round(kpi.completed_percentage)}
            previousValue={Math.round(previousKpi?.completed_percentage || 0)}
            milestone={80}
            label="Završeno"
            icon="✅"
          />
        </div>
        <div className="metric">
          <MilestoneAnimation
            value={kpi.active_workers}
            previousValue={previousKpi?.active_workers || 0}
            milestone={10}
            label="Aktivni radnici"
            icon="👥"
          />
        </div>
        <div className="metric">
          <MilestoneAnimation
            value={kpi.partial_items}
            previousValue={previousKpi?.partial_items || 0}
            milestone={25}
            label="Djelimične stavke"
            icon="⚠️"
          />
          <span className="metric-sub">Razlika: {Math.round(kpi.shortage_qty)} kom</span>
        </div>
        <div className="metric">
          <span className="metric-label">Vrijeme do kraja smjene</span>
          <span className="metric-value">{Math.round(kpi.shift_ends_in_minutes)} min</span>
        </div>
      </header>

      {/* Load Balance Monitor */}
      {aiRecommendations.length > 0 && (
        <motion.div
          className="load-balance-monitor"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'linear-gradient(135deg, #1890ff, #40a9ff)',
            color: 'white',
            padding: '16px 24px',
            margin: '0 24px 24px 24px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
            cursor: 'pointer',
            transition: 'all 0.3s ease'
          }}
          whileHover={{ scale: 1.02 }}
          onClick={() => {
            // In a real implementation, this would open the AI recommendations page
            console.log('AI recommendations clicked');
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>
                AI predlaže preraspodjelu zadataka
              </div>
              <div style={{ fontSize: '13px', opacity: 0.9 }}>
                {aiRecommendations.length} preporuka za optimizaciju opterećenja
              </div>
            </div>
            <div style={{ fontSize: '20px' }}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M12 2L13.09 8.26L19 7L14.74 12L19 17L13.09 15.74L12 22L10.91 15.74L5 17L9.26 12L5 7L10.91 8.26L12 2Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
        </motion.div>
      )}

      <main className="tv-content">
        <section className="leaderboard">
          <h1>{(liveDashboard?.team_progress?.length ?? 0) > 0 ? 'Timovi' : 'Top magacioneri'}</h1>
          <div className="leaderboard-list">
            {liveDashboard?.team_progress && (liveDashboard.team_progress.length ?? 0) > 0 ? (
              // Team-based display
              liveDashboard.team_progress.map((team, index) => (
                <motion.div
                  key={team.team_id}
                  className="leaderboard-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className="leaderboard-rank">
                    <span style={{ 
                      background: team.shift === 'A' ? '#2563eb' : '#059669',
                      padding: '2px 8px',
                      borderRadius: '4px',
                      fontSize: '12px',
                    }}>
                      {team.shift}
                    </span>
                  </div>
                  <div className="leaderboard-name">
                    <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>{team.team}</div>
                    <div style={{ fontSize: '12px', opacity: 0.7 }}>
                      {team.members.join(' & ')}
                    </div>
                  </div>
                  <div className="leaderboard-progress">
                    <div className="progress-bar">
                      <div className="progress" style={{ width: `${Math.min(team.completion * 100, 100)}%` }} />
                    </div>
                    <span>{Math.round(team.completion * 100)}%</span>
                  </div>
                  <div className="leaderboard-stats">
                    <span>{team.tasks_completed}/{team.tasks_total} zadataka</span>
                  </div>
                </motion.div>
              ))
            ) : (
              // Fallback to individual leaderboard
              leaderboard.map((entry, index) => (
                <motion.div
                  key={entry.user_id}
                  className="leaderboard-card"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.05 }}
                >
                  <div className="leaderboard-rank">#{index + 1}</div>
                  <div className="leaderboard-name">{getDisplayName(entry.display_name)}</div>
                  <div className="leaderboard-progress">
                    <div className="progress-bar">
                      <div className="progress" style={{ width: `${Math.min(entry.task_completion, 100)}%` }} />
                    </div>
                    <span>{Math.round(entry.task_completion)}%</span>
                  </div>
                  <div className="leaderboard-stats">
                    <span>{entry.items_completed} stavki</span>
                    <span>{entry.speed_per_hour.toFixed(1)}/h</span>
                  </div>
                </motion.div>
              ))
            )}
          </div>
        </section>

        <section className="queue">
          <h2>Queue po radnjama</h2>
          <div className="queue-list">
            {queue.map((item) => (
              <div className="queue-card" key={item.dokument}>
              <div className="queue-title">{item.dokument}</div>
              <div className="queue-sub">{item.radnja}</div>
              <div className="queue-status">Status: {queueStatusLabels[item.status] ?? item.status}</div>
              <div className="queue-partial">Djelimično: {item.partial_items}/{item.total_items}</div>
              <div className="queue-shortage">Razlika: {Math.round(item.shortage_qty)} kom</div>
              <div className="queue-workers">
                Dodijeljeni: {item.assigned_to.length > 0 ? item.assigned_to.map((worker) => worker.slice(0, 8)).join(", ") : "—"}
              </div>
            </div>
          ))}
          </div>
        </section>
      </main>
    </div>
  );
};

export default App;
