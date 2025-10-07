import { motion } from "framer-motion";
import { useEffect, useMemo, useState } from "react";
import { io, Socket } from "socket.io-client";
import { useQuery } from "@tanstack/react-query";
import client, { ensureAuth } from "./api";
import PrivacyToggle from "./components/PrivacyToggle";
import MilestoneAnimation from "./components/MilestoneAnimation";

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
}

interface KpiSnapshot {
  total_tasks_today: number;
  completed_percentage: number;
  active_workers: number;
  shift_ends_in_minutes: number;
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

const App = () => {
  const [ready, setReady] = useState(false);
  const [isPrivate, setIsPrivate] = useState(false);
  const [previousKpi, setPreviousKpi] = useState<KpiSnapshot | null>(null);
  const { data, refetch } = useQuery({ queryKey: ["tv", "snapshot"], queryFn: fetchSnapshot, enabled: ready });

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
      <div className="tv-controls">
        <div className="brand-header">
          <div className="brand-logo">📦</div>
          <div className="brand-text">
            <h1>Magacin Track</h1>
            <p>Real-time Dashboard</p>
          </div>
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
          <span className="metric-label">Vrijeme do kraja smjene</span>
          <span className="metric-value">{Math.round(kpi.shift_ends_in_minutes)} min</span>
        </div>
      </header>

      <main className="tv-content">
        <section className="leaderboard">
          <h1>Top magacioneri</h1>
          <div className="leaderboard-list">
            {leaderboard.map((entry, index) => (
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
            ))}
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
