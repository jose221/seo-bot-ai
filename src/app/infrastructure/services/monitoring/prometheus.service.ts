import { Injectable } from '@angular/core';
import axios, { AxiosInstance } from 'axios';
import { environment } from '@/environments/environment';

export interface PrometheusMetric {
  name: string;
  help: string;
  type: string;
  metrics: Array<{
    labels: Record<string, string>;
    value: number;
  }>;
}

@Injectable({
  providedIn: 'root'
})
export class PrometheusService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      timeout: 10000,
    });
  }

  async getMetrics(): Promise<string> {
    try {
      const response = await this.axiosInstance.get(environment.metricsUrl);
      return response.data;
    } catch (error) {
      console.error('Error fetching Prometheus metrics:', error);
      throw error;
    }
  }

  async getPrometheusQuery(query: string, time?: string): Promise<any> {
    try {
      const url = `${environment.prometheusUrl}/api/v1/query`;
      const params: any = { query };
      if (time) {
        params.time = time;
      }
      const response = await this.axiosInstance.get(url, { params });
      return response.data;
    } catch (error) {
      console.error('Error executing Prometheus query:', error);
      throw error;
    }
  }

  async getPrometheusQueryRange(
    query: string,
    start: string,
    end: string,
    step: string = '15s'
  ): Promise<any> {
    try {
      const url = `${environment.prometheusUrl}/api/v1/query_range`;
      const params = { query, start, end, step };
      const response = await this.axiosInstance.get(url, { params });
      return response.data;
    } catch (error) {
      console.error('Error executing Prometheus range query:', error);
      throw error;
    }
  }

  parseMetrics(metricsText: string): PrometheusMetric[] {
    const lines = metricsText.split('\n');
    const metrics: PrometheusMetric[] = [];
    let currentMetric: PrometheusMetric | null = null;

    for (const line of lines) {
      if (line.startsWith('# HELP')) {
        const parts = line.split(' ');
        const name = parts[2];
        const help = parts.slice(3).join(' ');
        currentMetric = { name, help, type: '', metrics: [] };
        metrics.push(currentMetric);
      } else if (line.startsWith('# TYPE')) {
        const parts = line.split(' ');
        const type = parts[3];
        if (currentMetric) {
          currentMetric.type = type;
        }
      } else if (line && !line.startsWith('#') && currentMetric) {
        const match = line.match(/^([a-zA-Z_:][a-zA-Z0-9_:]*)\{?(.*?)\}?\s+([0-9.e+-]+)/);
        if (match) {
          const [, metricName, labelsStr, valueStr] = match;
          const labels: Record<string, string> = {};

          if (labelsStr) {
            const labelPairs = labelsStr.match(/(\w+)="([^"]*)"/g);
            if (labelPairs) {
              for (const pair of labelPairs) {
                const [key, value] = pair.split('=');
                labels[key] = value.replace(/"/g, '');
              }
            }
          }

          currentMetric.metrics.push({
            labels,
            value: parseFloat(valueStr)
          });
        }
      }
    }

    return metrics;
  }
}

