export interface UrlMapMetric {
  project_id: string;
  url_map_name: string;
  hostname: string;
  http_status: number | null;
  status: string;
  error?: string;
}

export interface PodMetric {
  project_id: string;
  cluster_name: string;
  namespace: string;
  pod_name: string;
  status: string;
  status_icon: string;
}

export interface PubSubMetric {
  project_id: string;
  subscription_name: string;
  unacked_messages: number;
  oldest_message_age_minutes: number;
  status: string;
}

export interface NodePoolMetric {
  project_id: string;
  cluster_name: string;
  node_pool_name: string;
  current_nodes: number;
  max_nodes: number;
  utilization_percent: number;
  status: string;
  is_regional: boolean;
}

export interface PodRestartMetric {
  project_id: string;
  cluster_name: string;
  namespace: string;
  pod_name: string;
  restart_count: number;
  status: string;
}

export interface LatencyMetric {
  project_id: string;
  backend_service: string;
  p95_latency_seconds: number;
  status: string;
}

export interface SpannerMetric {
  project_id: string;
  instance_name: string;
  metric_type: string;
  value_percent: number;
  status: string;
}

export interface MonitoringResponse {
  url_maps: UrlMapMetric[];
  pods: PodMetric[];
  pubsub: PubSubMetric[];
  node_pools: NodePoolMetric[];
  pod_restarts: PodRestartMetric[];
  latency: LatencyMetric[];
  spanner: SpannerMetric[];
  timestamp: string;
  errors: string[];
}
