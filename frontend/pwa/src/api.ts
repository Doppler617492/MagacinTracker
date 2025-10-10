import axios from "axios";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8123").replace(/\/$/, "");

const client = axios.create({ baseURL: `${API_BASE_URL}/api` });

let token: string | null = null;
let bootstrapPromise: Promise<string> | null = null;

// Check for stored token in localStorage
function getStoredToken(): string | null {
  const storedToken = localStorage.getItem('auth_token');
  const expiresAt = localStorage.getItem('auth_token_expires');
  
  if (storedToken && expiresAt) {
    const expirationTime = parseInt(expiresAt, 10);
    if (Date.now() < expirationTime) {
      return storedToken;
    } else {
      // Token expired, remove it
      localStorage.removeItem('auth_token');
      localStorage.removeItem('auth_token_expires');
    }
  }
  
  return null;
}

// Check if user is authenticated
export function isAuthenticated(): boolean {
  return getStoredToken() !== null;
}

// Get current token
export function getToken(): string | null {
  return token || getStoredToken();
}

// Login function
export async function login(email: string, password: string): Promise<string> {
  const response = await client.post("/auth/login", {
    username: email,
    password,
  });
  
  const accessToken = response.data.access_token;
  const expiresIn = response.data.expires_in || 28800; // 8 hours default
  
  // Store token in localStorage
  localStorage.setItem('auth_token', accessToken);
  localStorage.setItem('auth_token_expires', 
    (Date.now() + (expiresIn * 1000)).toString()
  );
  
  token = accessToken;
  client.defaults.headers.common.Authorization = `Bearer ${token}`;
  
  return accessToken;
}

// Logout function
export function logout(): void {
  token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_token_expires');
  delete client.defaults.headers.common.Authorization;
}

export async function ensureAuth(): Promise<void> {
  if (token) return;
  
  const storedToken = getStoredToken();
  if (storedToken) {
    token = storedToken;
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
    return;
  }
  
  // No stored token, user needs to login
  throw new Error('No authentication token found');
}

client.interceptors.request.use((config) => {
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
