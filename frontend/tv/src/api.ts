import axios from "axios";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8123").replace(/\/$/, "");

const client = axios.create({ baseURL: `${API_BASE_URL}/api` });

let token: string | null = null;
let bootstrapPromise: Promise<string> | null = null;

// Read device credentials from environment variables
const TV_DEVICE_ID = import.meta.env.VITE_TV_DEVICE_ID as string | undefined;
const TV_DEVICE_SECRET = import.meta.env.VITE_TV_DEVICE_SECRET as string | undefined;

async function obtainToken(): Promise<string> {
  if (!TV_DEVICE_ID || !TV_DEVICE_SECRET) {
    throw new Error("TV device credentials missing: set VITE_TV_DEVICE_ID and VITE_TV_DEVICE_SECRET");
  }
  const response = await client.post("/auth/device-token", {
    device_id: TV_DEVICE_ID,
    device_secret: TV_DEVICE_SECRET,
  });
  return response.data.access_token;
}

export async function ensureAuth(): Promise<void> {
  if (token) return;
  if (!bootstrapPromise) {
    bootstrapPromise = obtainToken();
  }
  token = await bootstrapPromise;
  client.defaults.headers.common.Authorization = `Bearer ${token}`;
}

client.interceptors.request.use((config) => {
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Team & Dashboard interfaces
export interface LiveDashboard {
  total_tasks_today: number;
  completed_tasks: number;
  active_teams: number;
  team_progress: Array<{
    team: string;
    team_id: string;
    members: string[];
    completion: number;
    shift: string;
    tasks_total: number;
    tasks_completed: number;
  }>;
  shift_status: {
    active_shift: string | null;
    shift_a: any;
    shift_b: any;
    current_time: string;
  };
  generated_at: string;
}

export async function getLiveDashboard(): Promise<LiveDashboard> {
  await ensureAuth();
  const { data } = await client.get("/dashboard/live");
  return data;
}

export default client;
