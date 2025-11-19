from google.cloud import container_v1
from typing import List
from ..config import GKEClusterConfig


async def discover_gke_clusters(project_id: str) -> List[GKEClusterConfig]:
    """
    Discover all GKE clusters in a project using the Container API.
    Returns a list of GKEClusterConfig objects.
    """
    clusters = []

    try:
        container_client = container_v1.ClusterManagerClient()

        # List all clusters in all locations (using '-' as wildcard)
        parent = f"projects/{project_id}/locations/-"

        response = container_client.list_clusters(parent=parent)

        for cluster in response.clusters:
            # Determine if cluster is regional or zonal
            # Regional clusters have location like "us-central1"
            # Zonal clusters have location like "us-central1-a"
            location = cluster.location
            cluster_type = "zonal" if location.count('-') >= 2 else "regional"

            clusters.append(GKEClusterConfig(
                name=cluster.name,
                location=location,
                type=cluster_type
            ))

    except Exception as e:
        # Log error but return empty list to avoid breaking the entire monitoring
        print(f"Error discovering GKE clusters for project {project_id}: {str(e)}")
        return []

    return clusters
