import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { PrometheusService } from '@/app/infrastructure/services/monitoring/prometheus.service';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

@Component({
  selector: 'app-metrics-dashboard',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="metrics-dashboard">
      <h2>Métricas del Sistema</h2>

      <div class="metrics-grid">
        <div class="metric-card">
          <h3>Request Rate</h3>
          <canvas #requestChart id="requestChart"></canvas>
        </div>

        <div class="metric-card">
          <h3>Response Time</h3>
          <canvas #responseChart id="responseChart"></canvas>
        </div>

        <div class="metric-card">
          <h3>Error Rate</h3>
          <canvas #errorChart id="errorChart"></canvas>
        </div>

        <div class="metric-card">
          <h3>Active Requests</h3>
          <canvas #activeChart id="activeChart"></canvas>
        </div>
      </div>

      <div class="raw-metrics" *ngIf="showRaw">
        <h3>Métricas Raw</h3>
        <pre>{{ rawMetrics }}</pre>
      </div>

      <button (click)="toggleRaw()" class="btn btn-secondary mt-3">
        {{ showRaw ? 'Ocultar' : 'Mostrar' }} Métricas Raw
      </button>
    </div>
  `,
  styles: [`
    .metrics-dashboard {
      padding: 20px;
    }

    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
      gap: 20px;
      margin: 20px 0;
    }

    .metric-card {
      background: white;
      border-radius: 8px;
      padding: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .metric-card h3 {
      margin-top: 0;
      margin-bottom: 15px;
      color: #333;
    }

    .raw-metrics {
      background: #f5f5f5;
      border-radius: 8px;
      padding: 20px;
      margin-top: 20px;
    }

    .raw-metrics pre {
      margin: 0;
      overflow-x: auto;
      font-size: 12px;
    }

    canvas {
      max-height: 200px;
    }
  `]
})
export class MetricsDashboardComponent implements OnInit, OnDestroy {
  rawMetrics: string = '';
  showRaw: boolean = false;
  private charts: Chart[] = [];
  private refreshInterval: any;

  constructor(private prometheusService: PrometheusService) {}

  async ngOnInit() {
    await this.loadMetrics();
    this.refreshInterval = setInterval(() => this.loadMetrics(), 15000);
  }

  ngOnDestroy() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
    this.charts.forEach(chart => chart.destroy());
  }

  async loadMetrics() {
    try {
      const metrics = await this.prometheusService.getMetrics();
      this.rawMetrics = metrics;
      await this.updateCharts();
    } catch (error) {
      console.error('Error loading metrics:', error);
    }
  }

  async updateCharts() {
    try {
      const now = Math.floor(Date.now() / 1000);
      const oneHourAgo = now - 3600;

      // Request rate
      const requestRateData = await this.prometheusService.getPrometheusQueryRange(
        'rate(http_requests_total[5m])',
        oneHourAgo.toString(),
        now.toString()
      );

      // Response time
      const responseTimeData = await this.prometheusService.getPrometheusQueryRange(
        'http_request_duration_seconds',
        oneHourAgo.toString(),
        now.toString()
      );

      this.updateChart('requestChart', requestRateData);
      this.updateChart('responseChart', responseTimeData);
    } catch (error) {
      console.error('Error updating charts:', error);
    }
  }

  private updateChart(chartId: string, data: any) {
    const canvas = document.getElementById(chartId) as HTMLCanvasElement;
    if (!canvas) return;

    const existingChart = this.charts.find(c => c.canvas.id === chartId);
    if (existingChart) {
      existingChart.destroy();
      this.charts = this.charts.filter(c => c.canvas.id !== chartId);
    }

    if (data?.data?.result?.[0]?.values) {
      const values = data.data.result[0].values;
      const labels = values.map((v: any) => new Date(v[0] * 1000).toLocaleTimeString());
      const dataPoints = values.map((v: any) => parseFloat(v[1]));

      const chart = new Chart(canvas, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Value',
            data: dataPoints,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });

      this.charts.push(chart);
    }
  }

  toggleRaw() {
    this.showRaw = !this.showRaw;
  }
}

