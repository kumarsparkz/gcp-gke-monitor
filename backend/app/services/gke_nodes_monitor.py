from google.cloud import container_v1
from typing import List
from ..models.monitoring import NodePoolMetric, StatusType
from ..config import GKEClusterConfig


async def monitor_gke_nodes(project_id: str, clusters: List[GKEClusterConfig]) -> List[NodePoolMetric]:
    """Monitor GKE node pools and report those at 80%+ capacity"""
    results = []

    try:
        container_client = container_v1.ClusterManagerClient()

        for cluster_config in clusters:
            try:
                cluster_path = f"projects/{project_id}/locations/{cluster_config.location}/clusters/{cluster_config.name}"
                cluster = container_client.get_cluster(name=cluster_path)

                is_regional = cluster_config.type.lower() == "regional"

                # Iterate through node pools
                for node_pool in cluster.node_pools:
                    if not node_pool.autoscaling or not node_pool.autoscaling.enabled:
                        # Skip non-autoscaling pools
                        continue

                    current_node_count = node_pool.initial_node_count
                    max_nodes = node_pool.autoscaling.max_node_count

                    # For regional clusters, multiply by 3 (one per zone)
                    if is_regional:
                        effective_max = max_nodes * 3
                        effective_current = current_node_count * 3
                    else:
                        effective_max = max_nodes
                        effective_current = current_node_count

                    # Calculate utilization percentage
                    if effective_max > 0:
                        utilization = (effective_current / effective_max) * 100
                    else:
                        utilization = 0

                    # Only report if at 80% or higher
                    if utilization >= 80:
                        if utilization >= 95:
                            status_icon = StatusType.RED
                        elif utilization >= 90:
                            status_icon = StatusType.YELLOW
                        else:
                            status_icon = StatusType.YELLOW

                        results.append(NodePoolMetric(
                            project_id=project_id,
                            cluster_name=cluster_config.name,
                            node_pool_name=node_pool.name,
                            current_nodes=effective_current,
                            max_nodes=effective_max,
                            utilization_percent=round(utilization, 2),
                            status=status_icon,
                            is_regional=is_regional
                        ))

            except Exception as e:
                results.append(NodePoolMetric(
                    project_id=project_id,
                    cluster_name=cluster_config.name,
                    node_pool_name="error",
                    current_nodes=0,
                    max_nodes=0,
                    utilization_percent=0.0,
                    status=StatusType.RED,
                    is_regional=False
                ))

    except Exception as e:
        pass

    return results
