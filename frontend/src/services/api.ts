import axios from 'axios';
import { MonitoringResponse } from '../types/monitoring';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const api = {
  async getMetrics(): Promise<MonitoringResponse> {
    const response = await axios.get<MonitoringResponse>(`${API_BASE_URL}/api/metrics`);
    return response.data;
  },

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await axios.get(`${API_BASE_URL}/api/health`);
    return response.data;
  },
};
