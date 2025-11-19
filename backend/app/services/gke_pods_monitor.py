from kubernetes import client, config as k8s_config
from google.cloud import container_v1
from typing import List
from ..models.monitoring import PodMetric, StatusType
from ..config import GKEClusterConfig
import base64
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


async def monitor_gke_pods(project_id: str, clusters: List[GKEClusterConfig]) -> List[PodMetric]:
    """Monitor GKE pods and return non-running pods"""
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

                # Filter non-running pods
                for pod in pods.items:
                    pod_status = pod.status.phase

                    if pod_status.lower() != 'running':
                        # Determine status icon based on pod phase
                        if pod_status.lower() in ['pending', 'containercreating']:
                            status_icon = StatusType.YELLOW
                        elif pod_status.lower() in ['failed', 'unknown', 'crashloopbackoff']:
                            status_icon = StatusType.RED
                        else:
                            status_icon = StatusType.YELLOW

                        results.append(PodMetric(
                            project_id=project_id,
                            cluster_name=cluster_config.name,
                            namespace=pod.metadata.namespace,
                            pod_name=pod.metadata.name,
                            status=pod_status,
                            status_icon=status_icon
                        ))

            finally:
                # Clean up temp file
                os.unlink(kubeconfig_path)

        except Exception as e:
            results.append(PodMetric(
                project_id=project_id,
                cluster_name=cluster_config.name,
                namespace="error",
                pod_name="error",
                status=f"Error: {str(e)}",
                status_icon=StatusType.RED
            ))

    return results
