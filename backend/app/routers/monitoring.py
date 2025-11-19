from fastapi import APIRouter, HTTPException
from ..models.monitoring import MonitoringResponse
from ..config import load_config
from ..services.urlmap_monitor import monitor_url_maps
from ..services.gke_pods_monitor import monitor_gke_pods
from ..services.pubsub_monitor import monitor_pubsub
from ..services.gke_nodes_monitor import monitor_gke_nodes
from ..services.pod_restart_monitor import monitor_pod_restarts
from ..services.latency_monitor import monitor_latency
from ..services.spanner_monitor import monitor_spanner
from ..services.cluster_discovery import discover_gke_clusters
from datetime import datetime
import asyncio

router = APIRouter()


@router.get("/metrics", response_model=MonitoringResponse)
async def get_metrics():
    """
    Fetch all monitoring metrics from configured GCP projects
    """
    try:
        config = load_config()

        if not config.projects:
            return MonitoringResponse(
                timestamp=datetime.utcnow().isoformat(),
                errors=["No projects configured in config.json"]
            )

        all_url_maps = []
        all_pods = []
        all_pubsub = []
        all_node_pools = []
        all_pod_restarts = []
        all_latency = []
        all_spanner = []
        errors = []

        # Process each project
        for project in config.projects:
            try:
                # Auto-discover GKE clusters if not provided in config
                gke_clusters = project.gke_clusters
                if not gke_clusters:
                    gke_clusters = await discover_gke_clusters(project.project_id)

                # Run all monitoring tasks concurrently for this project
                tasks = []

                if project.monitor_url_maps:
                    tasks.append(("url_maps", monitor_url_maps(project.project_id)))

                if project.monitor_gke_pods and gke_clusters:
                    tasks.append(("pods", monitor_gke_pods(project.project_id, gke_clusters)))

                if project.monitor_pubsub:
                    tasks.append(("pubsub", monitor_pubsub(project.project_id)))

                if project.monitor_gke_nodes and gke_clusters:
                    tasks.append(("nodes", monitor_gke_nodes(project.project_id, gke_clusters)))

                if project.monitor_pod_restarts and gke_clusters:
                    tasks.append(("restarts", monitor_pod_restarts(project.project_id, gke_clusters)))

                if project.monitor_latency:
                    tasks.append(("latency", monitor_latency(project.project_id)))

                if project.monitor_spanner:
                    tasks.append(("spanner", monitor_spanner(project.project_id)))

                # Execute all tasks concurrently
                results = await asyncio.gather(*[task[1] for task in tasks], return_exceptions=True)

                # Collect results
                for i, (task_name, _) in enumerate(tasks):
                    result = results[i]

                    if isinstance(result, Exception):
                        errors.append(f"Error in {task_name} for {project.project_id}: {str(result)}")
                        continue

                    if task_name == "url_maps":
                        all_url_maps.extend(result)
                    elif task_name == "pods":
                        all_pods.extend(result)
                    elif task_name == "pubsub":
                        all_pubsub.extend(result)
                    elif task_name == "nodes":
                        all_node_pools.extend(result)
                    elif task_name == "restarts":
                        all_pod_restarts.extend(result)
                    elif task_name == "latency":
                        all_latency.extend(result)
                    elif task_name == "spanner":
                        all_spanner.extend(result)

            except Exception as e:
                errors.append(f"Error processing project {project.project_id}: {str(e)}")

        return MonitoringResponse(
            url_maps=all_url_maps,
            pods=all_pods,
            pubsub=all_pubsub,
            node_pools=all_node_pools,
            pod_restarts=all_pod_restarts,
            latency=all_latency,
            spanner=all_spanner,
            timestamp=datetime.utcnow().isoformat(),
            errors=errors
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
