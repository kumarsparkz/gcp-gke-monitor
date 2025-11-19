from google.cloud import pubsub_v1, monitoring_v3
from typing import List
from ..models.monitoring import PubSubMetric, StatusType
from datetime import datetime, timedelta
import time


async def monitor_pubsub(project_id: str) -> List[PubSubMetric]:
    """Monitor Pub/Sub subscriptions for unacked messages older than 5 minutes"""
    results = []

    try:
        subscriber = pubsub_v1.SubscriberClient()
        monitoring_client = monitoring_v3.MetricServiceClient()

        project_path = f"projects/{project_id}"

        # List all subscriptions
        subscriptions = subscriber.list_subscriptions(request={"project": project_path})

        for subscription in subscriptions:
            try:
                subscription_name = subscription.name.split('/')[-1]

                # Query metrics for unacked messages
                now = time.time()
                seconds = int(now)
                nanos = int((now - seconds) * 10 ** 9)
                interval = monitoring_v3.TimeInterval(
                    {
                        "end_time": {"seconds": seconds, "nanos": nanos},
                        "start_time": {"seconds": (seconds - 600), "nanos": nanos},  # Last 10 minutes
                    }
                )

                # Query num_undelivered_messages
                aggregation = monitoring_v3.Aggregation(
                    {
                        "alignment_period": {"seconds": 60},
                        "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
                    }
                )

                results_query = monitoring_client.list_time_series(
                    request={
                        "name": project_path,
                        "filter": f'metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages" '
                                  f'AND resource.labels.subscription_id="{subscription_name}"',
                        "interval": interval,
                        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        "aggregation": aggregation,
                    }
                )

                # Get the latest value
                unacked_count = 0
                for result in results_query:
                    if result.points:
                        unacked_count = int(result.points[0].value.int64_value or result.points[0].value.double_value)
                        break

                # Query oldest_unacked_message_age
                oldest_age_minutes = 0.0
                results_age = monitoring_client.list_time_series(
                    request={
                        "name": project_path,
                        "filter": f'metric.type="pubsub.googleapis.com/subscription/oldest_unacked_message_age" '
                                  f'AND resource.labels.subscription_id="{subscription_name}"',
                        "interval": interval,
                        "view": monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
                        "aggregation": aggregation,
                    }
                )

                for result in results_age:
                    if result.points:
                        oldest_age_seconds = result.points[0].value.double_value or result.points[0].value.int64_value
                        oldest_age_minutes = oldest_age_seconds / 60.0
                        break

                # Only report if there are unacked messages older than 5 minutes
                if unacked_count > 0 and oldest_age_minutes > 5:
                    # Determine status based on age and count
                    if oldest_age_minutes > 30:
                        status_icon = StatusType.RED
                    elif oldest_age_minutes > 10:
                        status_icon = StatusType.YELLOW
                    else:
                        status_icon = StatusType.YELLOW

                    results.append(PubSubMetric(
                        project_id=project_id,
                        subscription_name=subscription_name,
                        unacked_messages=unacked_count,
                        oldest_message_age_minutes=round(oldest_age_minutes, 2),
                        status=status_icon
                    ))

            except Exception as e:
                # Skip individual subscription errors
                continue

    except Exception as e:
        results.append(PubSubMetric(
            project_id=project_id,
            subscription_name="error",
            unacked_messages=0,
            oldest_message_age_minutes=0.0,
            status=StatusType.RED
        ))

    return results
