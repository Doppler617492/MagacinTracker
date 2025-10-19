import axios from "axios";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8123").replace(/\/$/, "");

const client = axios.create({ baseURL: `${API_BASE_URL}/api` });

let token: string | null = null;

const AUTH_TOKEN_KEY = "auth_token";
const AUTH_TOKEN_EXPIRES_KEY = "auth_token_expires";
const USER_PROFILE_KEY = "user_profile";
const USER_ID_KEY = "user_id";
const USER_ROLE_KEY = "user_role";
const USER_FULL_NAME_KEY = "user_full_name";
const USER_EMAIL_KEY = "user_email";
const USER_LOCATION_KEY = "user_location";

interface LoginResponseDTO {
  access_token: string;
  expires_in?: number;
  user?: {
    id: string;
    email?: string;
    first_name?: string;
    last_name?: string;
    full_name?: string;
    role?: string;
    default_location?: string | null;
    location?: string | null;
  };
}

export interface StoredUserProfile {
  id: string;
  email: string;
  fullName: string;
  role: string;
  location: string | null;
  firstName?: string;
  lastName?: string;
}

function getStoredToken(): string | null {
  const storedToken = localStorage.getItem(AUTH_TOKEN_KEY);
  const expiresAt = localStorage.getItem(AUTH_TOKEN_EXPIRES_KEY);

  if (storedToken && expiresAt) {
    const expirationTime = parseInt(expiresAt, 10);
    if (Number.isFinite(expirationTime) && Date.now() < expirationTime) {
      return storedToken;
    }
    localStorage.removeItem(AUTH_TOKEN_KEY);
    localStorage.removeItem(AUTH_TOKEN_EXPIRES_KEY);
  }

  return null;
}

function persistUserProfile(user: LoginResponseDTO["user"], fallbackEmail: string): void {
  const email = user?.email ?? fallbackEmail;
  const derivedName = [user?.first_name, user?.last_name].filter(Boolean).join(" ");
  const fullName = user?.full_name ?? (derivedName || email.split("@")[0]);
  const role = (user?.role ?? "").toLowerCase();
  const location =
    user?.default_location ??
    user?.location ??
    localStorage.getItem(USER_LOCATION_KEY) ??
    null;

  const profile: StoredUserProfile = {
    id: user?.id ?? "",
    email,
    fullName,
    role,
    location,
    firstName: user?.first_name,
    lastName: user?.last_name,
  };

  localStorage.setItem(USER_PROFILE_KEY, JSON.stringify(profile));
  if (profile.id) {
    localStorage.setItem(USER_ID_KEY, profile.id);
  }
  localStorage.setItem(USER_ROLE_KEY, profile.role);
  localStorage.setItem(USER_FULL_NAME_KEY, profile.fullName);
  localStorage.setItem(USER_EMAIL_KEY, profile.email);
  if (profile.location) {
    localStorage.setItem(USER_LOCATION_KEY, profile.location);
  }
}

export function getStoredUserProfile(): StoredUserProfile | null {
  const raw = localStorage.getItem(USER_PROFILE_KEY);
  if (!raw) {
    return null;
  }

  try {
    return JSON.parse(raw) as StoredUserProfile;
  } catch (error) {
    console.error("Failed to parse stored user profile", error);
    return null;
  }
}

export function isAuthenticated(): boolean {
  return getStoredToken() !== null;
}

export function getToken(): string | null {
  return token || getStoredToken();
}

export async function login(email: string, password: string): Promise<string> {
  // API Gateway expects "username" (email) + password
  const response = await client.post<LoginResponseDTO>("/auth/login", {
    username: email,
    password,
  });

  const accessToken = response.data.access_token;
  const expiresIn = response.data.expires_in || 28800; // default 8h

  localStorage.setItem(AUTH_TOKEN_KEY, accessToken);
  localStorage.setItem(
    AUTH_TOKEN_EXPIRES_KEY,
    (Date.now() + expiresIn * 1000).toString()
  );
  // Persist profile: prefer response user; fallback to /auth/me to fetch id/role
  try {
    let user = response.data.user;
    if (!user) {
      // Set token header to call /auth/me
      client.defaults.headers.common.Authorization = `Bearer ${accessToken}`;
      const me = await client.get("/auth/me");
      user = {
        id: me.data?.id,
        email,
        full_name: email.split("@")[0],
        role: me.data?.role,
      } as any;
    }
    persistUserProfile(user, email);
  } catch (e) {
    // If /auth/me fails, persist minimal profile from email
    persistUserProfile(undefined as any, email);
  }

  token = accessToken;
  client.defaults.headers.common.Authorization = `Bearer ${token}`;

  return accessToken;
}

export function logout(): void {
  token = null;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_TOKEN_EXPIRES_KEY);
  localStorage.removeItem(USER_PROFILE_KEY);
  localStorage.removeItem(USER_ID_KEY);
  localStorage.removeItem(USER_ROLE_KEY);
  localStorage.removeItem(USER_FULL_NAME_KEY);
  localStorage.removeItem(USER_EMAIL_KEY);
  localStorage.removeItem(USER_LOCATION_KEY);
  delete client.defaults.headers.common.Authorization;
}

export async function ensureAuth(): Promise<void> {
  if (token) {
    return;
  }

  const storedToken = getStoredToken();
  if (storedToken) {
    token = storedToken;
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
    return;
  }

  throw new Error("No authentication token found");
}

client.interceptors.request.use((config) => {
  if (!token) {
    token = getStoredToken();
  }
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Team Management
export interface WorkerTeamInfo {
  team_id: string;
  team_name: string;
  shift: string;
  partner_id: string;
  partner_name: string;
  partner_online: boolean;
  shift_status: {
    shift: string;
    status: string;
    next_event: string | null;
    countdown_seconds: number | null;
    countdown_formatted: string | null;
    shift_start: string;
    shift_end: string;
    break_start: string;
    break_end: string;
  };
}

export async function getMyTeam(): Promise<WorkerTeamInfo | null> {
  try {
    const response = await client.get("/worker/my-team");
    return response.data;
  } catch (error: any) {
    if (error.response?.status === 404) {
      return null;
    }
    throw error;
  }
}

export default client;
