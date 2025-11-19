from google.cloud import monitoring_v3
from typing import List
from ..models.monitoring import LatencyMetric, StatusType
import time


async def monitor_latency(project_id: str) -> List[LatencyMetric]:
    """Monitor load balancer backend latencies and report p95 > 3s"""
    results = []

    try:
        monitoring_client = monitoring_v3.MetricServiceClient()
        project_path = f"projects/{project_id}"

        # Query for backend latencies
        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": seconds, "nanos": nanos},
                "start_time": {"seconds": (seconds - 600), "nanos": nanos},  # Last 10 minutes
            }
        )

        # Query with percentile aggregation for p95
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": 60},
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_DELTA,
                "cross_series_reducer": monitoring_v3.Aggregation.Reducer.REDUCE_PERCENTILE_95,
                "group_by_fields": ["resource.backend_target_name"],
            }
        )

        results_query = monitoring_client.list_time_series(
            request={
                "name": project_path,
                "filter": 'metric.type="loadbalancing.googleapis.com/https/backend_latencies"',
                "interval": interval,
                "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                "aggregation": aggregation,
            }
        )

        # Process results
        for result in results_query:
            if result.points:
                # Get the latest p95 value (in milliseconds)
                latency_ms = result.points[0].value.distribution_value.mean if hasattr(
                    result.points[0].value, 'distribution_value'
                ) else (result.points[0].value.double_value or result.points[0].value.int64_value)

                # Convert to seconds
                latency_seconds = latency_ms / 1000.0

                # Only report if p95 > 3 seconds
                if latency_seconds > 3.0:
                    # Extract backend service name
                    backend_name = "unknown"
                    for label in result.resource.labels:
                        if label == "backend_target_name":
                            backend_name = result.resource.labels[label]
                            break

                    if latency_seconds > 10.0:
                        status_icon = StatusType.RED
                    elif latency_seconds > 5.0:
                        status_icon = StatusType.YELLOW
                    else:
                        status_icon = StatusType.YELLOW

                    results.append(LatencyMetric(
                        project_id=project_id,
                        backend_service=backend_name,
                        p95_latency_seconds=round(latency_seconds, 2),
                        status=status_icon
                    ))

    except Exception as e:
        # Silently skip errors for latency monitoring
        pass

    return results
