import axios from "axios";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8123").replace(/\/$/, "");

const client = axios.create({ baseURL: `${API_BASE_URL}/api` });

let token: string | null = null;
let bootstrapPromise: Promise<string> | null = null;

const ADMIN_CREDENTIALS = {
  username: "marko.sef@example.com",
  password: "Magacin123!"
};

async function obtainToken(): Promise<string> {
  const response = await client.post("/auth/login", ADMIN_CREDENTIALS);
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

export async function getSchedulerSuggestion(trebovanjeId: string) {
  await ensureAuth();
  const response = await client.post("/zaduznice/predlog", {
    trebovanje_id: trebovanjeId
  });
  return response.data;
}

// KPI API functions
export async function getDailyStats(filters?: { radnja?: string; period?: string; radnik?: string }) {
  await ensureAuth();
  const response = await client.get("/kpi/daily-stats", { params: filters });
  return response.data;
}

export async function getTopWorkers(filters?: { radnja?: string; period?: string }) {
  await ensureAuth();
  const response = await client.get("/kpi/top-workers", { params: filters });
  return response.data;
}

export async function getManualCompletion(filters?: { radnja?: string; period?: string }) {
  await ensureAuth();
  const response = await client.get("/kpi/manual-completion", { params: filters });
  return response.data;
}

// CSV Export
export async function exportCSV(filters?: { radnja?: string; period?: string; radnik?: string }) {
  await ensureAuth();
  const response = await client.get("/reports/export", { 
    params: filters,
    responseType: 'blob'
  });
  return response.data;
}

export default client;
