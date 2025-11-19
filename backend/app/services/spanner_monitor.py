from google.cloud import monitoring_v3, spanner_v1
from typing import List
from ..models.monitoring import SpannerMetric, StatusType
import time


async def monitor_spanner(project_id: str) -> List[SpannerMetric]:
    """Monitor Spanner CPU and storage utilization"""
    results = []

    try:
        spanner_client = spanner_v1.InstanceAdminClient()
        monitoring_client = monitoring_v3.MetricServiceClient()

        project_path = f"projects/{project_id}"

        # List all Spanner instances
        instances = spanner_client.list_instances(parent=project_path)

        now = time.time()
        seconds = int(now)
        nanos = int((now - seconds) * 10 ** 9)
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": seconds, "nanos": nanos},
                "start_time": {"seconds": (seconds - 300), "nanos": nanos},  # Last 5 minutes
            }
        )

        for instance in instances:
            instance_id = instance.name.split('/')[-1]

            try:
                # Monitor CPU utilization (high priority)
                cpu_aggregation = monitoring_v3.Aggregation(
                    {
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                    }
                )

                cpu_results = monitoring_client.list_time_series(
                    request={
                        "name": project_path,
                        "filter": f'metric.type="spanner.googleapis.com/instance/cpu/utilization_by_priority" '
                                  f'AND resource.labels.instance_id="{instance_id}" '
                                  f'AND metric.labels.priority="high"',
                        "interval": interval,
                        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        "aggregation": cpu_aggregation,
                    }
                )

                for result in cpu_results:
                    if result.points:
                        cpu_utilization = (result.points[0].value.double_value or result.points[0].value.int64_value) * 100

                        # Report if > 45%
                        if cpu_utilization > 45:
                            if cpu_utilization > 65:
                                status_icon = StatusType.RED
                            else:
                                status_icon = StatusType.YELLOW

                            results.append(SpannerMetric(
                                project_id=project_id,
                                instance_name=instance_id,
                                metric_type="CPU Utilization (High Priority)",
                                value_percent=round(cpu_utilization, 2),
                                status=status_icon
                            ))
                        break

                # Monitor storage utilization
                storage_results = monitoring_client.list_time_series(
                    request={
                        "name": project_path,
                        "filter": f'metric.type="spanner.googleapis.com/instance/storage/utilization" '
                                  f'AND resource.labels.instance_id="{instance_id}"',
                        "interval": interval,
                        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        "aggregation": cpu_aggregation,
                    }
                )

                for result in storage_results:
                    if result.points:
                        storage_utilization = (result.points[0].value.double_value or result.points[0].value.int64_value) * 100

                        # Report if > 75%
                        if storage_utilization > 75:
                            if storage_utilization > 90:
                                status_icon = StatusType.RED
                            else:
                                status_icon = StatusType.YELLOW

                            results.append(SpannerMetric(
                                project_id=project_id,
                                instance_name=instance_id,
                                metric_type="Storage Utilization",
                                value_percent=round(storage_utilization, 2),
                                status=status_icon
                            ))
                        break

            except Exception as e:
                # Skip individual instance errors
                continue

    except Exception as e:
        # Silently skip if no Spanner instances
        pass

    return results
