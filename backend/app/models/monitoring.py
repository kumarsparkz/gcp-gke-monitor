from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class StatusType(str, Enum):
    GREEN = "🟢"
    YELLOW = "🟡"
    RED = "🔴"
    GREY = "⚪"


class UrlMapMetric(BaseModel):
    project_id: str
    url_map_name: str
    hostname: str
    http_status: Optional[int]
    status: str
    error: Optional[str] = None


class PodMetric(BaseModel):
    project_id: str
    cluster_name: str
    namespace: str
    pod_name: str
    status: str
    status_icon: str


class PubSubMetric(BaseModel):
    project_id: str
    subscription_name: str
    unacked_messages: int
    oldest_message_age_minutes: float
    status: str


class NodePoolMetric(BaseModel):
    project_id: str
    cluster_name: str
    node_pool_name: str
    current_nodes: int
    max_nodes: int
    utilization_percent: float
    status: str
    is_regional: bool


class PodRestartMetric(BaseModel):
    project_id: str
    cluster_name: str
    namespace: str
    pod_name: str
    restart_count: int
    status: str


class LatencyMetric(BaseModel):
    project_id: str
    backend_service: str
    p95_latency_seconds: float
    status: str


class SpannerMetric(BaseModel):
    project_id: str
    instance_name: str
    metric_type: str
    value_percent: float
    status: str


class MonitoringResponse(BaseModel):
    url_maps: List[UrlMapMetric] = []
    pods: List[PodMetric] = []
    pubsub: List[PubSubMetric] = []
    node_pools: List[NodePoolMetric] = []
    pod_restarts: List[PodRestartMetric] = []
    latency: List[LatencyMetric] = []
    spanner: List[SpannerMetric] = []
    timestamp: str
    errors: List[str] = []
