import axios from "axios";
const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");
const client = axios.create({ baseURL: `${API_BASE_URL}/api` });
// Initialize token from localStorage
let token = localStorage.getItem('auth_token');
// Set authorization header if token exists
if (token) {
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
}
export async function login(email, password) {
    const response = await client.post("/auth/login", {
        username: email,
        password,
    });
    const accessToken = response.data.access_token;
    token = accessToken;
    localStorage.setItem('auth_token', accessToken);
    client.defaults.headers.common.Authorization = `Bearer ${token}`;
    return accessToken;
}
export function logout() {
    token = null;
    localStorage.removeItem('auth_token');
    delete client.defaults.headers.common.Authorization;
    window.location.href = '/';
}
export function isAuthenticated() {
    return token !== null;
}
export async function ensureAuth() {
    if (!isAuthenticated()) {
        throw new Error('Authentication required');
    }
}
export function getToken() {
    return token;
}
client.interceptors.request.use((config) => {
    if (token) {
        config.headers = config.headers ?? {};
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});
export async function getSchedulerSuggestion(trebovanjeId) {
    await ensureAuth();
    const response = await client.post("/zaduznice/predlog", {
        trebovanje_id: trebovanjeId
    });
    return response.data;
}

export async function cancelSchedulerSuggestion(trebovanjeId) {
    await ensureAuth();
    await client.post(`/zaduznice/predlog/${trebovanjeId}/cancel`);
}
// KPI API functions
export async function getDailyStats(filters) {
    await ensureAuth();
    const response = await client.get("/kpi/daily-stats", { params: filters });
    return response.data;
}
export async function getTopWorkers(filters) {
    await ensureAuth();
    const response = await client.get("/kpi/top-workers", { params: filters });
    return response.data;
}
export async function getManualCompletion(filters) {
    await ensureAuth();
    const response = await client.get("/kpi/manual-completion", { params: filters });
    return response.data;
}
// CSV Export
export async function exportCSV(filters) {
    await ensureAuth();
    const response = await client.get("/reports/export", {
        params: filters,
        responseType: 'blob'
    });
    return response.data;
}
export async function processAIQuery(request) {
    await ensureAuth();
    const response = await client.post("/ai/query", request);
    return response.data;
}
export async function getAISuggestions() {
    await ensureAuth();
    const response = await client.get("/ai/suggestions");
    return response.data;
}
export async function getAIHistory(limit = 10) {
    await ensureAuth();
    const response = await client.get("/ai/history", { params: { limit } });
    return response.data;
}
export async function getReportSchedules() {
    await ensureAuth();
    const response = await client.get("/reports/schedules");
    return response.data;
}
export async function getReportSchedule(id) {
    await ensureAuth();
    const response = await client.get(`/reports/schedules/${id}`);
    return response.data;
}
export async function createReportSchedule(schedule) {
    await ensureAuth();
    const response = await client.post("/reports/schedules", schedule);
    return response.data;
}
export async function updateReportSchedule(id, schedule) {
    await ensureAuth();
    const response = await client.patch(`/reports/schedules/${id}`, schedule);
    return response.data;
}
export async function deleteReportSchedule(id) {
    await ensureAuth();
    await client.delete(`/reports/schedules/${id}`);
}
export async function runReportNow(id, recipients, filters) {
    await ensureAuth();
    await client.post(`/reports/run-now/${id}`, {
        schedule_id: id,
        recipients,
        filters
    });
}
export async function getReportHistory(id, limit = 10) {
    await ensureAuth();
    const response = await client.get(`/reports/schedules/${id}/history`, { params: { limit } });
    return response.data;
}
export async function getKPIForecast(params) {
    await ensureAuth();
    const response = await client.get("/kpi/predict", { params });
    return response.data;
}
export async function getAIRecommendations() {
    await ensureAuth();
    const response = await client.post("/ai/recommendations");
    return response.data;
}
export async function simulateLoadBalance(simulationRequest) {
    await ensureAuth();
    const response = await client.post("/ai/load-balance", simulationRequest);
    return response.data;
}
export async function applyRecommendation(recommendationId) {
    await ensureAuth();
    await client.post(`/ai/recommendations/${recommendationId}/apply`);
}
export async function dismissRecommendation(recommendationId) {
    await ensureAuth();
    await client.post(`/ai/recommendations/${recommendationId}/dismiss`);
}
export async function getAIModelStatus() {
    await ensureAuth();
    const response = await client.get("/ai/model/status");
    return response.data;
}
export async function getAIModelPerformance() {
    await ensureAuth();
    const response = await client.get("/ai/model/performance");
    return response.data;
}
export async function trainAIModel(trainingRequest) {
    await ensureAuth();
    const response = await client.post("/ai/train", trainingRequest);
    return response.data;
}
export async function getTrainingStatus(trainingId) {
    await ensureAuth();
    const response = await client.get(`/ai/train/status/${trainingId}`);
    return response.data;
}
export async function cancelTraining(trainingId) {
    await ensureAuth();
    await client.post(`/ai/train/cancel/${trainingId}`);
}
export async function getAIOptimization(optimizationRequest) {
    await ensureAuth();
    const response = await client.post("/ai/optimize", optimizationRequest);
    return response.data;
}
export async function resetAIModels() {
    await ensureAuth();
    await client.post("/ai/model/reset");
}
export async function trainDNNModel(trainingRequest) {
    await ensureAuth();
    const response = await client.post("/ai/dnn/train", trainingRequest);
    return response.data;
}
export async function getDNNStatus() {
    await ensureAuth();
    const response = await client.get("/ai/dnn/status");
    return response.data;
}
export async function predictDNN(predictionRequest) {
    await ensureAuth();
    const response = await client.post("/ai/dnn/predict", predictionRequest);
    return response.data;
}
export async function getFederatedSystemStatus() {
    await ensureAuth();
    const response = await client.get("/ai/federated/status");
    return response.data;
}
export async function aggregateFederatedModels() {
    await ensureAuth();
    const response = await client.post("/ai/federated/aggregate");
    return response.data;
}
export async function registerFederatedNode(nodeId) {
    await ensureAuth();
    await client.post(`/ai/federated/nodes/${nodeId}/register`);
}
export async function trainFederatedNode(nodeId, localData) {
    await ensureAuth();
    const response = await client.post(`/ai/federated/nodes/${nodeId}/train`, { local_data: localData });
    return response.data;
}
export async function getEdgeSystemStatus() {
    await ensureAuth();
    const response = await client.get("/edge/system/status");
    return response.data;
}
export async function predictEdge(predictionRequest) {
    await ensureAuth();
    const response = await client.post("/edge/predict", predictionRequest);
    return response.data;
}
export async function getEdgeModelStatus(modelId) {
    await ensureAuth();
    const response = await client.get(`/edge/models/${modelId}/status`);
    return response.data;
}
// Stream Events API
export async function publishEvent(eventRequest) {
    await ensureAuth();
    const response = await client.post("/stream/events/publish", eventRequest);
    return response.data;
}
export async function getRecentEvents(limit = 100) {
    await ensureAuth();
    const response = await client.get(`/stream/events/recent?limit=${limit}`);
    return response.data;
}
export async function getWorkerActivity() {
    await ensureAuth();
    const response = await client.get("/stream/events/worker-activity");
    return response.data;
}
export async function getWarehouseLoad() {
    await ensureAuth();
    const response = await client.get("/stream/events/warehouse-load");
    return response.data;
}
export async function simulateEvents(warehouseId = "warehouse_1", eventCount = 10) {
    await ensureAuth();
    const response = await client.post("/stream/events/simulate", { warehouse_id: warehouseId, event_count: eventCount });
    return response.data;
}
// Stream Metrics API
export async function getStreamMetrics() {
    await ensureAuth();
    const response = await client.get("/stream/metrics");
    return response.data;
}
export async function getThroughputMetrics() {
    await ensureAuth();
    const response = await client.get("/stream/metrics/throughput");
    return response.data;
}
export async function getPerformanceMetrics() {
    await ensureAuth();
    const response = await client.get("/stream/metrics/performance");
    return response.data;
}
export async function getHealthMetrics() {
    await ensureAuth();
    const response = await client.get("/stream/metrics/health");
    return response.data;
}
// Transformer API
export async function trainTransformerModel(trainingRequest) {
    await ensureAuth();
    const response = await client.post("/ai/transformer/train", trainingRequest);
    return response.data;
}
export async function getTransformerStatus() {
    await ensureAuth();
    const response = await client.get("/ai/transformer/status");
    return response.data;
}
export async function predictTransformer(predictionRequest) {
    await ensureAuth();
    const response = await client.post("/ai/transformer/predict", predictionRequest);
    return response.data;
}
// Kafka Streaming API
export async function getKafkaMetrics() {
    await ensureAuth();
    const response = await client.get("/kafka/metrics");
    return response.data;
}
export async function getKafkaAnalytics() {
    await ensureAuth();
    const response = await client.get("/kafka/analytics");
    return response.data;
}
export async function getKafkaPerformance() {
    await ensureAuth();
    const response = await client.get("/kafka/performance");
    return response.data;
}
export async function publishKafkaEvent(eventRequest) {
    await ensureAuth();
    const response = await client.post("/kafka/events/publish", eventRequest);
    return response.data;
}
// Edge AI API
export async function performEdgeInference(inferenceRequest) {
    await ensureAuth();
    const response = await client.post("/edge/infer", inferenceRequest);
    return response.data;
}
export async function getEdgeStatus() {
    await ensureAuth();
    const response = await client.get("/edge/status");
    return response.data;
}
export async function getEdgeHealth() {
    await ensureAuth();
    const response = await client.get("/edge/health");
    return response.data;
}
export async function getEdgePerformance() {
    await ensureAuth();
    const response = await client.get("/edge/performance");
    return response.data;
}
export async function getEdgeModels() {
    await ensureAuth();
    const response = await client.get("/edge/models");
    return response.data;
}
export async function syncEdgeModels() {
    await ensureAuth();
    const response = await client.post("/edge/sync");
    return response.data;
}
export async function getEdgeSyncStatus() {
    await ensureAuth();
    const response = await client.get("/edge/sync/status");
    return response.data;
}
export async function forceEdgeSync() {
    await ensureAuth();
    const response = await client.post("/edge/sync/force");
    return response.data;
}
export async function getEdgeHubStatus() {
    await ensureAuth();
    const response = await client.get("/edge/hub/status");
    return response.data;
}
export default client;
