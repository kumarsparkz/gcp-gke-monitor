'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import { MonitoringResponse } from '../types/monitoring';
import { MetricsTable } from '../components/MetricsTable';

export default function Home() {
  const [monitoring, setMonitoring] = useState<MonitoringResponse | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  // Get refresh interval from environment variable (default: 900 seconds)
  const refreshIntervalSeconds = parseInt(process.env.NEXT_PUBLIC_REFRESH_INTERVAL || '900', 10);
  const refreshIntervalMs = refreshIntervalSeconds * 1000;

  const fetchMetrics = useCallback(async () => {
    if (!isMonitoring) return;

    setLoading(true);
    setError(null);

    try {
      const data = await api.getMetrics();
      setMonitoring(data);
      setLastUpdate(new Date().toLocaleString());
    } catch (err: any) {
      setError(err.message || 'Failed to fetch metrics');
    } finally {
      setLoading(false);
    }
  }, [isMonitoring]);

  useEffect(() => {
    if (isMonitoring) {
      // Fetch immediately when enabled
      fetchMetrics();

      // Set up auto-refresh based on configured interval
      const interval = setInterval(fetchMetrics, refreshIntervalMs);

      return () => clearInterval(interval);
    } else {
      // Clear data when monitoring is disabled
      setMonitoring(null);
      setLastUpdate('');
    }
  }, [isMonitoring, fetchMetrics, refreshIntervalMs]);

  const toggleMonitoring = () => {
    setIsMonitoring((prev) => !prev);
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h1 style={styles.mainTitle}>GCP/GKE Monitoring Dashboard</h1>
        <p style={styles.subtitle}>Black Friday Monitoring Dashboard</p>
      </div>

      <div style={styles.controls}>
        <div style={styles.toggleContainer}>
          <label style={styles.toggleLabel}>
            <span style={styles.toggleText}>Pull Metrics</span>
            <button
              onClick={toggleMonitoring}
              style={{
                ...styles.toggleButton,
                backgroundColor: isMonitoring ? '#4ade80' : '#6b7280',
              }}
            >
              <div
                style={{
                  ...styles.toggleCircle,
                  transform: isMonitoring ? 'translateX(24px)' : 'translateX(2px)',
                }}
              />
            </button>
            <span style={styles.statusText}>
              {isMonitoring ? 'ON' : 'OFF'} {isMonitoring ? '🟢' : '⚪'}
            </span>
          </label>
        </div>

        {lastUpdate && (
          <div style={styles.lastUpdate}>
            Last updated: {lastUpdate}
          </div>
        )}
      </div>

      {loading && <div style={styles.loading}>Loading metrics...</div>}

      {error && <div style={styles.error}>Error: {error}</div>}

      {monitoring && (
        <div style={styles.content}>
          {monitoring.errors.length > 0 && (
            <div style={styles.errorSection}>
              <h3>Errors:</h3>
              {monitoring.errors.map((err, i) => (
                <p key={i} style={styles.errorText}>{err}</p>
              ))}
            </div>
          )}

          <MetricsTable
            title="1. URL Maps - Synthetic Testing"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'url_map_name', label: 'URL Map' },
              { key: 'hostname', label: 'Hostname' },
              { key: 'http_status', label: 'HTTP Status' },
              { key: 'status', label: 'Status' },
              { key: 'error', label: 'Error' },
            ]}
            data={monitoring.url_maps}
          />

          <MetricsTable
            title="2. GKE Pods - Non-Running"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'cluster_name', label: 'Cluster' },
              { key: 'namespace', label: 'Namespace' },
              { key: 'pod_name', label: 'Pod Name' },
              { key: 'status', label: 'Pod Status' },
              { key: 'status_icon', label: 'Status' },
            ]}
            data={monitoring.pods}
            emptyMessage="All pods are running"
          />

          <MetricsTable
            title="3. Pub/Sub - Unacked Messages (>5 min old)"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'subscription_name', label: 'Subscription' },
              { key: 'unacked_messages', label: 'Unacked Messages' },
              { key: 'oldest_message_age_minutes', label: 'Oldest Age (min)' },
              { key: 'status', label: 'Status' },
            ]}
            data={monitoring.pubsub}
            emptyMessage="No unacked messages older than 5 minutes"
          />

          <MetricsTable
            title="4. GKE Node Pools - Capacity (≥80%)"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'cluster_name', label: 'Cluster' },
              { key: 'node_pool_name', label: 'Node Pool' },
              { key: 'current_nodes', label: 'Current Nodes' },
              { key: 'max_nodes', label: 'Max Nodes' },
              { key: 'utilization_percent', label: 'Utilization %' },
              { key: 'is_regional', label: 'Regional', render: (val: boolean) => val ? 'Yes' : 'No' },
              { key: 'status', label: 'Status' },
            ]}
            data={monitoring.node_pools}
            emptyMessage="No node pools at high capacity"
          />

          <MetricsTable
            title="5. GKE Pods - High Restart Count (>5)"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'cluster_name', label: 'Cluster' },
              { key: 'namespace', label: 'Namespace' },
              { key: 'pod_name', label: 'Pod Name' },
              { key: 'restart_count', label: 'Restart Count' },
              { key: 'status', label: 'Status' },
            ]}
            data={monitoring.pod_restarts}
            emptyMessage="No pods with high restart counts"
          />

          <MetricsTable
            title="6. Load Balancer Latency - P95 (>3s)"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'backend_service', label: 'Backend Service' },
              { key: 'p95_latency_seconds', label: 'P95 Latency (s)' },
              { key: 'status', label: 'Status' },
            ]}
            data={monitoring.latency}
            emptyMessage="All latencies are within acceptable range"
          />

          <MetricsTable
            title="7. Spanner - CPU & Storage"
            columns={[
              { key: 'project_id', label: 'Project ID' },
              { key: 'instance_name', label: 'Instance' },
              { key: 'metric_type', label: 'Metric' },
              { key: 'value_percent', label: 'Value %' },
              { key: 'status', label: 'Status' },
            ]}
            data={monitoring.spanner}
            emptyMessage="Spanner instances are healthy"
          />
        </div>
      )}

      {!isMonitoring && !monitoring && (
        <div style={styles.placeholder}>
          <p style={styles.placeholderText}>
            Toggle "Pull Metrics" to ON to start monitoring
          </p>
        </div>
      )}
    </div>
  );
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    backgroundColor: '#0a0a0a',
    color: '#ffffff',
    padding: '20px',
  },
  header: {
    textAlign: 'center',
    marginBottom: '30px',
    paddingBottom: '20px',
    borderBottom: '2px solid #333',
  },
  mainTitle: {
    fontSize: '36px',
    fontWeight: 'bold',
    marginBottom: '10px',
  },
  subtitle: {
    fontSize: '18px',
    color: '#9ca3af',
  },
  controls: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '30px',
    padding: '20px',
    backgroundColor: '#1e1e1e',
    borderRadius: '8px',
    border: '1px solid #333',
  },
  toggleContainer: {
    display: 'flex',
    alignItems: 'center',
  },
  toggleLabel: {
    display: 'flex',
    alignItems: 'center',
    gap: '15px',
    cursor: 'pointer',
  },
  toggleText: {
    fontSize: '18px',
    fontWeight: '600',
  },
  toggleButton: {
    position: 'relative',
    width: '52px',
    height: '28px',
    borderRadius: '14px',
    border: 'none',
    cursor: 'pointer',
    transition: 'background-color 0.3s',
  },
  toggleCircle: {
    position: 'absolute',
    top: '2px',
    width: '24px',
    height: '24px',
    borderRadius: '12px',
    backgroundColor: '#ffffff',
    transition: 'transform 0.3s',
  },
  statusText: {
    fontSize: '16px',
    fontWeight: '600',
  },
  lastUpdate: {
    fontSize: '14px',
    color: '#9ca3af',
  },
  loading: {
    textAlign: 'center',
    padding: '20px',
    fontSize: '16px',
    color: '#4ade80',
  },
  error: {
    textAlign: 'center',
    padding: '20px',
    fontSize: '16px',
    color: '#ef4444',
    backgroundColor: '#1e1e1e',
    borderRadius: '8px',
    border: '1px solid #ef4444',
    marginBottom: '20px',
  },
  errorSection: {
    backgroundColor: '#1e1e1e',
    padding: '20px',
    borderRadius: '8px',
    border: '1px solid #ef4444',
    marginBottom: '20px',
  },
  errorText: {
    color: '#ef4444',
    marginBottom: '5px',
  },
  content: {
    maxWidth: '1400px',
    margin: '0 auto',
  },
  placeholder: {
    textAlign: 'center',
    padding: '60px 20px',
  },
  placeholderText: {
    fontSize: '18px',
    color: '#9ca3af',
  },
};
