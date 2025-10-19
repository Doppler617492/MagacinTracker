import axios from "axios";

const API_BASE_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/$/, "");

const client = axios.create({ baseURL: `${API_BASE_URL}/api` });

// Initialize token from localStorage
let token: string | null = localStorage.getItem('auth_token');

// Set authorization header if token exists
if (token) {
  client.defaults.headers.common.Authorization = `Bearer ${token}`;
}

export async function login(email: string, password: string): Promise<string> {
  const response = await client.post("/auth/login", {
    username: email,
    password,
  });
  
  const accessToken = response.data.access_token;
  token = accessToken;
  localStorage.setItem('auth_token', accessToken);
  client.defaults.headers.common.Authorization = `Bearer ${token}`;
  // Persist user profile if provided by backend
  if (response.data?.user) {
    try {
      localStorage.setItem('auth_user', JSON.stringify(response.data.user));
    } catch {}
  }
  
  return accessToken;
}

export function logout(): void {
  console.log("🔐 Logout called");
  token = null;
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  delete client.defaults.headers.common.Authorization;
  window.location.href = '/';
}

// Debug function to force logout
export function forceLogout(): void {
  console.log("🔐 Force logout called");
  token = null;
  localStorage.clear();
  delete client.defaults.headers.common.Authorization;
  window.location.href = '/';
}

export function isAuthenticated(): boolean {
  console.log("🔐 isAuthenticated called, token exists:", !!token);
  
  if (!token) {
    console.log("🔐 No token found, not authenticated");
    return false;
  }
  
  try {
    // Check if token is expired by decoding the JWT
    const payload = JSON.parse(atob(token.split('.')[1]));
    const now = Math.floor(Date.now() / 1000);
    const exp = payload.exp;
    
    console.log("🔐 Token exp:", exp, "Current time:", now, "Expired:", exp < now);
    
    if (exp && exp < now) {
      // Token is expired, just return false without calling logout
      console.log("🔐 Token expired, not authenticated");
      return false;
    }
    
    console.log("🔐 Token valid, authenticated");
    return true;
  } catch (error) {
    // Invalid token format, just return false without calling logout
    console.log("🔐 Invalid token format, not authenticated:", error);
    return false;
  }
}

// Fetch current user profile from API Gateway
export async function fetchMe(): Promise<any | null> {
  try {
    const res = await client.get("/auth/me");
    return res.data;
  } catch (e) {
    return null;
  }
}

export async function ensureAuth(): Promise<void> {
  if (!isAuthenticated()) {
    throw new Error('Authentication required');
  }
}

export function getToken(): string | null {
  return token;
}

client.interceptors.request.use((config) => {
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor to handle 401 errors
client.interceptors.response.use(
  (response) => response,
  (error) => {
    // If we get a 401 Unauthorized error, the token is invalid/expired
    if (error.response?.status === 401) {
      console.log("🔐 401 Unauthorized - clearing auth and redirecting to login");
      token = null;
      localStorage.removeItem('auth_token');
      delete client.defaults.headers.common.Authorization;
      
      // Only redirect if not already on login page
      if (!window.location.pathname.includes('/login') && window.location.pathname !== '/') {
        window.location.href = '/';
      }
    }
    return Promise.reject(error);
  }
);

export async function getSchedulerSuggestion(trebovanjeId: string) {
  await ensureAuth();
  const response = await client.post("/zaduznice/predlog", {
    trebovanje_id: trebovanjeId
  });
  return response.data;
}

export async function cancelSchedulerSuggestion(trebovanjeId: string) {
  await ensureAuth();
  await client.post(`/zaduznice/predlog/${trebovanjeId}/cancel`);
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

// AI Assistant API functions
export interface AIQueryRequest {
  query: string;
  context?: {
    radnja_id?: string;
    radnik_id?: string;
    days?: number;
    language?: string;
  };
}

export interface AIQueryResponse {
  answer: string;
  data?: any;
  chart_data?: {
    type: string;
    data: any[];
    x_field?: string;
    y_field?: string;
    angle_field?: string;
    color_field?: string;
  };
  confidence: number;
  query_id: string;
  timestamp: string;
}

export async function processAIQuery(request: AIQueryRequest): Promise<AIQueryResponse> {
  await ensureAuth();
  const response = await client.post("/ai/query", request);
  return response.data;
}

export async function getAISuggestions() {
  await ensureAuth();
  const response = await client.get("/ai/suggestions");
  return response.data;
}

export async function getAIHistory(limit: number = 10) {
  await ensureAuth();
  const response = await client.get("/ai/history", { params: { limit } });
  return response.data;
}

// Reports API functions
export interface ReportSchedule {
  id: string;
  name: string;
  description?: string;
  channel: 'email' | 'slack' | 'both';
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  filters: Record<string, any>;
  enabled: boolean;
  time_hour: number;
  time_minute: number;
  created_at: string;
  updated_at: string;
  last_sent?: string;
  next_send?: string;
  total_sent: number;
  total_failed: number;
}

export interface ReportScheduleCreate {
  name: string;
  description?: string;
  channel: 'email' | 'slack' | 'both';
  frequency: 'daily' | 'weekly' | 'monthly';
  recipients: string[];
  filters: Record<string, any>;
  enabled: boolean;
  time_hour: number;
  time_minute: number;
}

export interface ReportScheduleUpdate {
  name?: string;
  description?: string;
  channel?: 'email' | 'slack' | 'both';
  frequency?: 'daily' | 'weekly' | 'monthly';
  recipients?: string[];
  filters?: Record<string, any>;
  enabled?: boolean;
  time_hour?: number;
  time_minute?: number;
}

export async function getReportSchedules(): Promise<ReportSchedule[]> {
  await ensureAuth();
  const response = await client.get("/reports/schedules");
  return response.data;
}

export async function getReportSchedule(id: string): Promise<ReportSchedule> {
  await ensureAuth();
  const response = await client.get(`/reports/schedules/${id}`);
  return response.data;
}

export async function createReportSchedule(schedule: ReportScheduleCreate): Promise<ReportSchedule> {
  await ensureAuth();
  const response = await client.post("/reports/schedules", schedule);
  return response.data;
}

export async function updateReportSchedule(id: string, schedule: ReportScheduleUpdate): Promise<ReportSchedule> {
  await ensureAuth();
  const response = await client.patch(`/reports/schedules/${id}`, schedule);
  return response.data;
}

export async function deleteReportSchedule(id: string): Promise<void> {
  await ensureAuth();
  await client.delete(`/reports/schedules/${id}`);
}

export async function runReportNow(id: string, recipients?: string[], filters?: Record<string, any>): Promise<void> {
  await ensureAuth();
  await client.post(`/reports/run-now/${id}`, {
    schedule_id: id,
    recipients,
    filters
  });
}

export async function getReportHistory(id: string, limit: number = 10): Promise<any> {
  await ensureAuth();
  const response = await client.get(`/reports/schedules/${id}/history`, { params: { limit } });
  return response.data;
}

// Predictive Analytics API functions
export interface ForecastData {
  metric: string;
  horizon: number;
  confidence: number;
  anomaly_detected: boolean;
  anomalies: number[];
  trend: number;
  seasonality: number;
  actual: Array<{
    date: string;
    value: number;
    is_anomaly: boolean;
  }>;
  forecast: Array<{
    date: string;
    value: number;
    lower_bound: number;
    upper_bound: number;
  }>;
  summary: {
    current_value: number;
    forecast_avg: number;
    trend_direction: string;
    trend_strength: number;
    confidence_score: number;
    anomaly_count: number;
  };
  generated_at: string;
  parameters: {
    metric: string;
    period: number;
    horizon: number;
    radnja_id?: string;
    radnik_id?: string;
  };
  processing_time_ms: number;
}

export async function getKPIForecast(params: {
  metric?: string;
  period?: number;
  horizon?: number;
  radnja_id?: string;
  radnik_id?: string;
}): Promise<ForecastData> {
  await ensureAuth();
  const response = await client.get("/kpi/predict", { params });
  return response.data;
}

// AI Recommendations API functions
export interface AIRecommendation {
  id: string;
  type: string;
  priority: string;
  title: string;
  description: string;
  confidence: number;
  impact_score: number;
  actions: Array<{
    type: string;
    [key: string]: any;
  }>;
  estimated_improvement: Record<string, number>;
  reasoning: string;
  created_at: string;
}

export interface LoadBalanceSimulation {
  simulation_id: string;
  recommendation: AIRecommendation;
  before_simulation: {
    store_metrics: Array<{
      store_id: string;
      store_name: string;
      load_index: number;
      worker_count: number;
      pending_tasks: number;
    }>;
    overall_metrics: {
      load_balance_variance: number;
      average_efficiency: number;
      average_idle_time: number;
      total_workers: number;
      total_pending_tasks: number;
    };
  };
  after_simulation: {
    store_metrics: Array<{
      store_id: string;
      store_name: string;
      load_index: number;
      worker_count: number;
      pending_tasks: number;
    }>;
    overall_metrics: {
      load_balance_variance: number;
      average_efficiency: number;
      average_idle_time: number;
      total_workers: number;
      total_pending_tasks: number;
    };
  };
  improvement_metrics: {
    load_balance_improvement: number;
    efficiency_improvement: number;
    completion_time_improvement: number;
  };
  generated_at: string;
}

export async function getAIRecommendations(): Promise<AIRecommendation[]> {
  await ensureAuth();
  const response = await client.post("/ai/recommendations");
  return response.data;
}

export async function simulateLoadBalance(simulationRequest: {
  recommendation_id: string;
  worker_metrics: Array<{
    worker_id: string;
    worker_name: string;
    current_tasks: number;
    completed_tasks_today: number;
    avg_completion_time: number;
    efficiency_score: number;
    idle_time_percentage: number;
    location: string;
  }>;
  store_metrics: Array<{
    store_id: string;
    store_name: string;
    total_tasks: number;
    completed_tasks: number;
    pending_tasks: number;
    avg_completion_time: number;
    worker_count: number;
    load_index: number;
    efficiency_delta: number;
  }>;
}): Promise<LoadBalanceSimulation> {
  await ensureAuth();
  const response = await client.post("/ai/load-balance", simulationRequest);
  return response.data;
}

export async function applyRecommendation(recommendationId: string): Promise<void> {
  await ensureAuth();
  await client.post(`/ai/recommendations/${recommendationId}/apply`);
}

export async function dismissRecommendation(recommendationId: string): Promise<void> {
  await ensureAuth();
  await client.post(`/ai/recommendations/${recommendationId}/dismiss`);
}

// AI Engine API functions
export interface ModelStatus {
  neural_network: {
    architecture: {
      input_size: number;
      hidden_size: number;
      output_size: number;
      total_parameters: number;
    };
    training_status: {
      is_trained: boolean;
      last_trained: string | null;
      training_sessions: number;
    };
    performance: {
      final_loss: number | null;
      final_accuracy: number | null;
      best_accuracy: number | null;
    };
  };
  reinforcement_learning: {
    architecture: {
      state_size: number;
      action_size: number;
      learning_rate: number;
      discount_factor: number;
      epsilon: number;
    };
    training_status: {
      is_trained: boolean;
      last_trained: string | null;
      total_episodes: number;
      training_sessions: number;
    };
    performance: {
      total_reward: number;
      best_reward: number;
      average_reward: number;
      convergence_episode: number | null;
    };
  };
  overall_status: string;
  last_updated: string;
}

export interface TrainingRequest {
  model_type: 'neural_network' | 'reinforcement_learning';
  epochs: number;
  learning_rate: number;
  batch_size: number;
}

export interface TrainingResponse {
  training_id: string;
  model_type: string;
  status: string;
  training_duration_ms: number;
  final_accuracy: number;
  training_history: Record<string, any>;
  started_at: string;
  completed_at: string;
}

export interface OptimizationRequest {
  current_state: Record<string, any>;
  optimization_type: 'adaptive' | 'predictive';
}

export interface OptimizationResponse {
  recommendation_id: string;
  optimization_type: string;
  recommended_action: Record<string, any>;
  confidence: number;
  expected_improvement: Record<string, number>;
  reasoning: string;
  processing_time_ms: number;
  generated_at: string;
}

export async function getAIModelStatus(): Promise<ModelStatus> {
  await ensureAuth();
  const response = await client.get("/ai/model/status");
  return response.data;
}

export async function getAIModelPerformance(): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.get("/ai/model/performance");
  return response.data;
}

export async function trainAIModel(trainingRequest: TrainingRequest): Promise<TrainingResponse> {
  await ensureAuth();
  const response = await client.post("/ai/train", trainingRequest);
  return response.data;
}

export async function getTrainingStatus(trainingId: string): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.get(`/ai/train/status/${trainingId}`);
  return response.data;
}

export async function cancelTraining(trainingId: string): Promise<void> {
  await ensureAuth();
  await client.post(`/ai/train/cancel/${trainingId}`);
}

export async function getAIOptimization(optimizationRequest: OptimizationRequest): Promise<OptimizationResponse> {
  await ensureAuth();
  const response = await client.post("/ai/optimize", optimizationRequest);
  return response.data;
}

export async function resetAIModels(): Promise<void> {
  await ensureAuth();
  await client.post("/ai/model/reset");
}

// Deep Neural Network API functions
export interface DNNTrainingRequest {
  epochs: number;
  learning_rate: number;
  batch_size: number;
  validation_split: number;
}

export interface DNNTrainingResponse {
  training_id: string;
  status: string;
  training_duration_ms: number;
  final_accuracy: number;
  best_accuracy: number;
  training_history: {
    train_losses: number[];
    val_losses: number[];
    train_accuracies: number[];
    val_accuracies: number[];
    epochs: number;
    early_stopped: boolean;
  };
  started_at: string;
  completed_at: string;
}

export interface DNNPredictionRequest {
  features: number[];
  include_feature_importance: boolean;
}

export interface DNNPredictionResponse {
  prediction: number;
  confidence: number;
  feature_importance?: Record<string, number>;
  model_version: number;
  processing_time_ms: number;
}

// Federated Learning API functions
export interface FederatedNodeStatus {
  node_id: string;
  is_initialized: boolean;
  last_updated: string | null;
  training_samples: number;
  last_sync: string | null;
  should_sync: boolean;
  is_syncing: boolean;
}

export interface FederatedSystemStatus {
  global_model: {
    version: number;
    last_aggregated: string | null;
    total_samples: number;
    is_initialized: boolean;
  };
  nodes: Record<string, FederatedNodeStatus>;
  aggregation_status: {
    total_nodes: number;
    trained_nodes: number;
    should_aggregate: boolean;
    last_aggregation: string | null;
  };
}

export interface FederatedAggregationResponse {
  status: string;
  nodes_participated: number;
  total_samples: number;
  global_model_version: number;
  aggregation_time: string;
  participating_nodes: string[];
}

// Edge Inference API functions
export interface EdgePredictionRequest {
  model_id: string;
  features: number[];
  request_id?: string;
}

export interface EdgePredictionResponse {
  prediction: number;
  confidence: number;
  inference_time_ms: number;
  model_version: number;
  edge_mode: boolean;
  request_id: string;
  timestamp: string;
}

export interface EdgeSystemStatus {
  total_models: number;
  initialized_models: number;
  total_predictions: number;
  sync_errors: number;
  last_sync: string | null;
  should_sync: boolean;
  sync_running: boolean;
  models: Record<string, any>;
}

export async function trainDNNModel(trainingRequest: DNNTrainingRequest): Promise<DNNTrainingResponse> {
  await ensureAuth();
  const response = await client.post("/ai/dnn/train", trainingRequest);
  return response.data;
}

export async function getDNNStatus(): Promise<Record<string, any> | null> {
  await ensureAuth();
  try {
    const response = await client.get("/ai/dnn/status");
    return response.data;
  } catch (e: any) {
    // Gracefully handle missing endpoint in some environments
    if (e?.response?.status === 404) {
      return null;
    }
    throw e;
  }
}

export async function predictDNN(predictionRequest: DNNPredictionRequest): Promise<DNNPredictionResponse> {
  await ensureAuth();
  const response = await client.post("/ai/dnn/predict", predictionRequest);
  return response.data;
}

export async function getFederatedSystemStatus(): Promise<FederatedSystemStatus> {
  await ensureAuth();
  const response = await client.get("/ai/federated/status");
  return response.data;
}

export async function aggregateFederatedModels(): Promise<FederatedAggregationResponse> {
  await ensureAuth();
  const response = await client.post("/ai/federated/aggregate");
  return response.data;
}

export async function registerFederatedNode(nodeId: string): Promise<void> {
  await ensureAuth();
  await client.post(`/ai/federated/nodes/${nodeId}/register`);
}

export async function trainFederatedNode(nodeId: string, localData: any[]): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.post(`/ai/federated/nodes/${nodeId}/train`, { local_data: localData });
  return response.data;
}

export async function getEdgeSystemStatus(): Promise<EdgeSystemStatus> {
  await ensureAuth();
  const response = await client.get("/edge/system/status");
  return response.data;
}

export async function predictEdge(predictionRequest: EdgePredictionRequest): Promise<EdgePredictionResponse> {
  await ensureAuth();
  const response = await client.post("/edge/predict", predictionRequest);
  return response.data;
}


export async function getEdgeModelStatus(modelId: string): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.get(`/edge/models/${modelId}/status`);
  return response.data;
}

// Streaming & Real-Time API functions
export interface StreamEvent {
  event_id: string;
  event_type: string;
  warehouse_id: string;
  timestamp: string;
  data: Record<string, any>;
  correlation_id?: string;
  processed: boolean;
}

export interface EventPublishRequest {
  event_type: string;
  warehouse_id: string;
  data: Record<string, any>;
  correlation_id?: string;
}

export interface EventPublishResponse {
  event_id: string;
  status: string;
  timestamp: string;
}

export interface StreamMetrics {
  events_processed: number;
  events_per_second: number;
  average_processing_time: number;
  queue_size: number;
  last_event_time: string | null;
  processing_errors: number;
  active_workers: number;
  active_warehouses: number;
  event_history_size: number;
}

export interface WorkerActivity {
  [workerId: string]: {
    last_activity: string;
    event_count: number;
    warehouse_id: string;
  };
}

export interface WarehouseLoad {
  [warehouseId: string]: {
    event_count: number;
    last_event: string;
    active_workers: string[];
  };
}

// Transformer API functions
export interface TransformerTrainingRequest {
  sequences: string[][];
  labels: number[];
  validation_split: number;
}

export interface TransformerTrainingResponse {
  training_id: string;
  status: string;
  training_duration_ms: number;
  final_accuracy: number;
  training_history: {
    train_losses: number[];
    val_losses: number[];
    train_accuracies: number[];
    val_accuracies: number[];
    epochs: number;
    vocab_size: number;
  };
  started_at: string;
  completed_at: string;
}

export interface TransformerPredictionRequest {
  sequences: string[][];
}

export interface TransformerPredictionResponse {
  predictions: number[];
  pattern_analysis: Array<{
    pattern_prediction: number;
    pattern_type: string;
    sequence_analysis: {
      length: number;
      unique_events: number;
      event_frequency: Record<string, number>;
    };
    confidence: number;
  }>;
  processing_time_ms: number;
}

// Stream Events API
export async function publishEvent(eventRequest: EventPublishRequest): Promise<EventPublishResponse> {
  await ensureAuth();
  const response = await client.post("/stream/events/publish", eventRequest);
  return response.data;
}

export async function getRecentEvents(limit: number = 100): Promise<{ events: StreamEvent[]; total_count: number; timestamp: string }> {
  await ensureAuth();
  const response = await client.get(`/stream/events/recent?limit=${limit}`);
  return response.data;
}

export async function getWorkerActivity(): Promise<{ worker_activity: WorkerActivity; total_workers: number; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/stream/events/worker-activity");
  return response.data;
}

export async function getWarehouseLoad(): Promise<{ warehouse_load: WarehouseLoad; total_warehouses: number; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/stream/events/warehouse-load");
  return response.data;
}

export interface TvQueueEntry {
  dokument: string;
  radnja: string;
  status: string;
  assigned_to: string[];
  eta_minutes?: number | null;
  total_items: number;
  partial_items: number;
  shortage_qty: number;
}

export interface TvKpiSnapshot {
  total_tasks_today: number;
  completed_percentage: number;
  active_workers: number;
  shift_ends_in_minutes: number;
  partial_items: number;
  shortage_qty: number;
}

export interface TvSnapshotResponse {
  generated_at: string;
  leaderboard: any[];
  queue: TvQueueEntry[];
  kpi: TvKpiSnapshot;
}

export async function getTvSnapshot(): Promise<TvSnapshotResponse> {
  await ensureAuth();
  const response = await client.get("/tv/snapshot");
  return response.data;
}

export async function simulateEvents(warehouseId: string = "warehouse_1", eventCount: number = 10): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.post("/stream/events/simulate", { warehouse_id: warehouseId, event_count: eventCount });
  return response.data;
}

// Stream Metrics API
export async function getStreamMetrics(): Promise<{ metrics: StreamMetrics; timestamp: string; service: string }> {
  await ensureAuth();
  const response = await client.get("/stream/metrics");
  return response.data;
}

export async function getThroughputMetrics(): Promise<{ throughput_metrics: Record<string, any>; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/stream/metrics/throughput");
  return response.data;
}

export async function getPerformanceMetrics(): Promise<{ performance_metrics: Record<string, any>; raw_metrics: StreamMetrics; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/stream/metrics/performance");
  return response.data;
}

export async function getHealthMetrics(): Promise<{ health_metrics: Record<string, any>; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/stream/metrics/health");
  return response.data;
}

// Transformer API
export async function trainTransformerModel(trainingRequest: TransformerTrainingRequest): Promise<TransformerTrainingResponse> {
  await ensureAuth();
  const response = await client.post("/ai/transformer/train", trainingRequest);
  return response.data;
}

export async function getTransformerStatus(): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.get("/ai/transformer/status");
  return response.data;
}

export async function predictTransformer(predictionRequest: TransformerPredictionRequest): Promise<TransformerPredictionResponse> {
  await ensureAuth();
  const response = await client.post("/ai/transformer/predict", predictionRequest);
  return response.data;
}

// Kafka Streaming API functions
export interface KafkaEvent {
  event_id: string;
  event_type: string;
  warehouse_id: string;
  timestamp: string;
  data: Record<string, any>;
  correlation_id?: string;
  schema_version: string;
  source: string;
}

export interface KafkaMetrics {
  events_published: number;
  events_consumed: number;
  events_processed: number;
  kafka_latency_ms: number;
  consumer_lag: number;
  throughput_events_per_second: number;
  error_count: number;
  last_event_time: string | null;
  topics: string[];
  consumer_groups: string[];
  queue_sizes: {
    event_queue: number;
    analytics_queue: number;
  };
  analytics_data_size: {
    top_workers: number;
    warehouses: number;
    anomalies: number;
    trends: number;
  };
}

export interface AnalyticsData {
  top_workers: Record<string, number>;
  warehouse_metrics: Record<string, {
    events_count: number;
    last_event: string;
    active_workers: string[];
    ai_decisions: number;
  }>;
  anomalies: Array<{
    type: string;
    warehouse_id: string;
    severity: string;
    description: string;
    timestamp: string;
    event_id: string;
  }>;
  trends: Record<string, Array<{
    timestamp: string;
    warehouse_id: string;
    data: Record<string, any>;
  }>>;
}

// Edge AI API functions
export interface EdgeInferenceRequest {
  inference_type: string;
  device_id: string;
  warehouse_id: string;
  input_data: Record<string, any>;
  request_id?: string;
}

export interface EdgeInferenceResponse {
  request_id: string;
  inference_type: string;
  prediction: number;
  confidence: number;
  inference_time_ms: number;
  model_version: string;
  device_id: string;
  timestamp: string;
  recommendations: Array<{
    type: string;
    message: string;
    action: string;
    priority: string;
  }>;
}

export interface EdgeDeviceStatus {
  device_id: string;
  status: string;
  cpu_usage: number;
  memory_usage: number;
  temperature: number;
  battery_level: number;
  network_status: string;
  last_heartbeat: string;
}

export interface EdgePerformanceMetrics {
  total_inferences: number;
  average_inference_time: number;
  success_rate: number;
  model_accuracy: number;
  last_inference: string | null;
  inference_history_size: number;
  recent_inferences: Array<{
    timestamp: string;
    inference_time_ms: number;
    success: boolean;
  }>;
}

// Kafka Streaming API
export async function getKafkaMetrics(): Promise<{ metrics: KafkaMetrics; timestamp: string; service: string }> {
  await ensureAuth();
  const response = await client.get("/kafka/metrics");
  return response.data;
}

export async function getKafkaAnalytics(): Promise<{ analytics_data: AnalyticsData; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/kafka/analytics");
  return response.data;
}

export async function getKafkaPerformance(): Promise<{ performance_metrics: Record<string, any>; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/kafka/performance");
  return response.data;
}

export async function publishKafkaEvent(eventRequest: any): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.post("/kafka/events/publish", eventRequest);
  return response.data;
}

// Edge AI API
export async function performEdgeInference(inferenceRequest: EdgeInferenceRequest): Promise<EdgeInferenceResponse> {
  await ensureAuth();
  const response = await client.post("/edge/infer", inferenceRequest);
  return response.data;
}

export async function getEdgeStatus(): Promise<{
  device_status: EdgeDeviceStatus;
  performance_metrics: EdgePerformanceMetrics;
  model_info: Record<string, any>;
  timestamp: string;
}> {
  await ensureAuth();
  const response = await client.get("/edge/status");
  return response.data;
}

export async function getEdgeHealth(): Promise<{ health_metrics: Record<string, any>; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/edge/health");
  return response.data;
}

export async function getEdgePerformance(): Promise<{ performance_indicators: Record<string, any>; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/edge/performance");
  return response.data;
}

export async function getEdgeModels(): Promise<{ models: Record<string, any>; total_models: number; device_id: string; timestamp: string }> {
  await ensureAuth();
  const response = await client.get("/edge/models");
  return response.data;
}

export async function syncEdgeModels(): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.post("/edge/sync");
  return response.data;
}


export async function getEdgeSyncStatus(): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.get("/edge/sync/status");
  return response.data;
}

export async function forceEdgeSync(): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.post("/edge/sync/force");
  return response.data;
}

export async function getEdgeHubStatus(): Promise<Record<string, any>> {
  await ensureAuth();
  const response = await client.get("/edge/hub/status");
  return response.data;
}

// Team Management API
export interface TeamMember {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

export interface Team {
  id: string;
  name: string;
  shift: string;
  active: boolean;
  worker1: TeamMember;
  worker2: TeamMember;
  created_at: string;
}

export interface TeamPerformance {
  team_id: string;
  team_name: string;
  total_tasks: number;
  completed_tasks: number;
  in_progress_tasks: number;
  completion_rate: number;
  total_scans: number;
  average_speed_per_hour: number;
}

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

export async function getTeams(): Promise<Team[]> {
  await ensureAuth();
  const response = await client.get("/teams");
  return response.data;
}

export async function getTeam(teamId: string): Promise<Team> {
  await ensureAuth();
  const response = await client.get(`/teams/${teamId}`);
  return response.data;
}

export async function getTeamPerformance(teamId: string): Promise<TeamPerformance> {
  await ensureAuth();
  const response = await client.get(`/teams/${teamId}/performance`);
  return response.data;
}

export async function getLiveDashboard(scope: string = "day"): Promise<LiveDashboard> {
  await ensureAuth();
  const response = await client.get(`/dashboard/live?scope=${scope}`);
  return response.data;
}

// Pantheon ERP Sync
export async function syncPantheonTrebovanja(dateFrom?: string, dateTo?: string): Promise<{
  status: string;
  message: string;
  total_fetched: number;
  trebovanja_created: number;
  trebovanja_updated: number;
  stavke_created: number;
  stavke_skipped: number;
  errors: number;
  duration_seconds: number;
}> {
  const params: any = {};
  if (dateFrom) params.date_from = dateFrom;
  if (dateTo) params.date_to = dateTo;
  
  const response = await client.post("/pantheon/sync/dispatches", null, { params });
  return response.data;
}

// Get users (for dropdowns)
export async function getUsers(params?: { page?: number; per_page?: number; role_filter?: string; active_filter?: boolean }): Promise<any> {
  const response = await client.get("/admin/users", { params });
  return response.data;
}

// Teams Management
export async function createTeam(team: any): Promise<any> {
  const response = await client.post("/teams", team);
  return response.data;
}

export async function updateTeam(teamId: string, team: any): Promise<any> {
  const response = await client.put(`/teams/${teamId}`, team);
  return response.data;
}

export async function deleteTeam(teamId: string): Promise<void> {
  await client.delete(`/teams/${teamId}`);
}

export default client;
