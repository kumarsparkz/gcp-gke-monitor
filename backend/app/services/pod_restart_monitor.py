from kubernetes import client, config as k8s_config
from google.cloud import container_v1
from typing import List
from ..models.monitoring import PodRestartMetric, StatusType
from ..config import GKEClusterConfig
import tempfile
import os


def get_gke_credentials(project_id: str, cluster_name: str, location: str):
    """Get GKE cluster credentials"""
    container_client = container_v1.ClusterManagerClient()

    cluster_path = f"projects/{project_id}/locations/{location}/clusters/{cluster_name}"
    cluster = container_client.get_cluster(name=cluster_path)

    # Create kubeconfig
    kubeconfig = {
        "apiVersion": "v1",
        "kind": "Config",
        "clusters": [{
            "name": cluster_name,
            "cluster": {
                "certificate-authority-data": cluster.master_auth.cluster_ca_certificate,
                "server": f"https://{cluster.endpoint}"
            }
        }],
        "contexts": [{
            "name": cluster_name,
            "context": {
                "cluster": cluster_name,
                "user": cluster_name
            }
        }],
        "current-context": cluster_name,
        "users": [{
            "name": cluster_name,
            "user": {
                "exec": {
                    "apiVersion": "client.authentication.k8s.io/v1beta1",
                    "command": "gcloud",
                    "args": [
                        "config",
                        "config-helper",
                        "--format=json"
                    ],
                    "interactiveMode": "Never"
                }
            }
        }]
    }

    return kubeconfig


async def monitor_pod_restarts(project_id: str, clusters: List[GKEClusterConfig]) -> List[PodRestartMetric]:
    """Monitor pod restart counts and report those with >5 restarts"""
    results = []

    for cluster_config in clusters:
        try:
            # Get cluster credentials
            kubeconfig = get_gke_credentials(
                project_id,
                cluster_config.name,
                cluster_config.location
            )

            # Create temporary kubeconfig file
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml') as f:
                import yaml
                yaml.dump(kubeconfig, f)
                kubeconfig_path = f.name

            try:
                # Load the kubeconfig
                k8s_config.load_kube_config(config_file=kubeconfig_path)

                # Create API client
                v1 = client.CoreV1Api()

                # Get all pods across all namespaces
                pods = v1.list_pod_for_all_namespaces(watch=False)

                # Check restart counts
                for pod in pods.items:
                    total_restarts = 0

                    # Sum up restart counts from all containers
                    if pod.status.container_statuses:
                        for container_status in pod.status.container_statuses:
                            total_restarts += container_status.restart_count

                    # Report if restarts > 5
                    if total_restarts > 5:
                        if total_restarts > 20:
                            status_icon = StatusType.RED
                        elif total_restarts > 10:
                            status_icon = StatusType.YELLOW
                        else:
                            status_icon = StatusType.YELLOW

                        results.append(PodRestartMetric(
                            project_id=project_id,
                            cluster_name=cluster_config.name,
                            namespace=pod.metadata.namespace,
                            pod_name=pod.metadata.name,
                            restart_count=total_restarts,
                            status=status_icon
                        ))

            finally:
                # Clean up temp file
                os.unlink(kubeconfig_path)

        except Exception as e:
            results.append(PodRestartMetric(
                project_id=project_id,
                cluster_name=cluster_config.name,
                namespace="error",
                pod_name="error",
                restart_count=0,
                status=StatusType.RED
            ))

    return results
