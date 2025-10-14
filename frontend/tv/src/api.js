import axios from "axios";
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "http://localhost:8123").replace(/\/$/, "");
const client = axios.create({ baseURL: `${API_BASE_URL}/api` });
let token = null;
let bootstrapPromise = null;
const TV_CREDENTIALS = {
    username: "it@cungu.com",
    password: "Dekodera1989"
};
async function obtainToken() {
    const response = await client.post("/auth/login", TV_CREDENTIALS);
    return response.data.access_token;
}
export async function ensureAuth() {
    if (token)
        return;
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
export default client;
