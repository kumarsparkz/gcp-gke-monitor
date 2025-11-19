import httpx
from google.cloud import compute_v1
from typing import List
from ..models.monitoring import UrlMapMetric, StatusType
import asyncio


async def monitor_url_maps(project_id: str) -> List[UrlMapMetric]:
    """Monitor URL maps and perform synthetic testing"""
    results = []

    try:
        # Initialize the URL Maps client
        url_maps_client = compute_v1.UrlMapsClient()

        # List all URL maps in the project
        request = compute_v1.ListUrlMapsRequest(project=project_id)
        url_maps = url_maps_client.list(request=request)

        # Collect hostnames from all URL maps
        hostnames_to_test = []

        for url_map in url_maps:
            # Extract hostnames from host rules
            if url_map.host_rules:
                for host_rule in url_map.host_rules:
                    for host in host_rule.hosts:
                        hostnames_to_test.append({
                            "url_map_name": url_map.name,
                            "hostname": host
                        })
            else:
                # If no host rules, add the URL map without hostname
                hostnames_to_test.append({
                    "url_map_name": url_map.name,
                    "hostname": "no-hostname-configured"
                })

        # Test each hostname
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            for item in hostnames_to_test:
                hostname = item["hostname"]
                url_map_name = item["url_map_name"]

                if hostname == "no-hostname-configured":
                    results.append(UrlMapMetric(
                        project_id=project_id,
                        url_map_name=url_map_name,
                        hostname=hostname,
                        http_status=None,
                        status=StatusType.GREY,
                        error="No hostname configured"
                    ))
                    continue

                # Construct URL (try HTTPS first)
                url = f"https://{hostname}"

                try:
                    response = await client.get(url)
                    status_code = response.status_code

                    # Determine status based on HTTP code
                    if status_code == 200:
                        status_icon = StatusType.GREEN
                    elif 200 < status_code < 500:
                        status_icon = StatusType.YELLOW
                    else:
                        status_icon = StatusType.RED

                    results.append(UrlMapMetric(
                        project_id=project_id,
                        url_map_name=url_map_name,
                        hostname=hostname,
                        http_status=status_code,
                        status=status_icon
                    ))

                except Exception as e:
                    results.append(UrlMapMetric(
                        project_id=project_id,
                        url_map_name=url_map_name,
                        hostname=hostname,
                        http_status=None,
                        status=StatusType.RED,
                        error=str(e)
                    ))

    except Exception as e:
        results.append(UrlMapMetric(
            project_id=project_id,
            url_map_name="error",
            hostname="error",
            http_status=None,
            status=StatusType.RED,
            error=f"Failed to fetch URL maps: {str(e)}"
        ))

    return results
