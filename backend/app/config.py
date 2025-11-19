import json
import os
from typing import List, Dict
from pydantic import BaseModel


class GKEClusterConfig(BaseModel):
    name: str
    location: str
    type: str  # "regional" or "zonal"


class ProjectConfig(BaseModel):
    project_id: str
    gke_clusters: List[GKEClusterConfig] = []
    monitor_url_maps: bool = True
    monitor_gke_pods: bool = True
    monitor_pubsub: bool = True
    monitor_gke_nodes: bool = True
    monitor_pod_restarts: bool = True
    monitor_latency: bool = True
    monitor_spanner: bool = True


class Config(BaseModel):
    projects: List[ProjectConfig]


def load_config() -> Config:
    """Load configuration from config.json"""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config.json")

    if not os.path.exists(config_path):
        # Return empty config if file doesn't exist
        return Config(projects=[])

    with open(config_path, "r") as f:
        data = json.load(f)

    return Config(**data)
