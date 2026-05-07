import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';

import { AuthRepository } from '@/app/domain/repositories/auth/auth.repository';
import { StatusType } from '@/app/domain/types/status.type';
import { ToastService } from '@/app/helper/toast.service';
import { environment } from '@/environments/environment';

type TrackableTaskKind = 'audit' | 'comparison' | 'schema' | 'url-validation';

interface DesktopNotificationPayload {
  title: string;
  body: string;
  route?: string;
}

interface DesktopNotificationClickPayload {
  route?: string;
}

interface DesktopNotificationsBridge {
  notify(payload: DesktopNotificationPayload): void;
  onClick?(callback: (payload: DesktopNotificationClickPayload) => void): () => void;
}

interface TaskStatusChangedEvent {
  event: 'task-status-changed';
  task_kind: TrackableTaskKind;
  task_id: string;
  status: string;
  route: string;
  label: string;
  occurred_at: string;
}

type BrowserWindowWithDesktopNotifications = Window & {
  desktopNotifications?: DesktopNotificationsBridge;
};

@Injectable({
  providedIn: 'root',
})
export class TaskNotificationService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly router = inject(Router);
  private readonly authRepository = inject(AuthRepository);
  private readonly toastService = inject(ToastService);

  private readonly reconnectDelayMs = 4000;
  private readonly pingIntervalMs = 25000;

  private started = false;
  private manualStop = false;
  private websocket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private pingTimer: number | null = null;
  private desktopClickUnsubscribe: (() => void) | null = null;

  start(): void {
    if (!isPlatformBrowser(this.platformId) || this.started) {
      return;
    }

    this.started = true;
    this.manualStop = false;
    this.prepareNotifications();
    this.connectWebSocket();
  }

  prepareNotifications(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.registerDesktopClickHandler();
    void this.requestNotificationPermission();
  }

  stop(): void {
    this.manualStop = true;
    this.started = false;
    this.clearReconnectTimer();
    this.stopPing();

    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }

    if (this.desktopClickUnsubscribe) {
      this.desktopClickUnsubscribe();
      this.desktopClickUnsubscribe = null;
    }
  }

  registerPendingTask(_kind: TrackableTaskKind, _id: string): void {
    this.start();
  }

  notifyTaskResult({
    title,
    body,
    status,
    route,
    tag,
  }: {
    title: string;
    body: string;
    status: 'completed' | 'failed' | string;
    route?: string;
    tag?: string;
  }): void {
    if (status === 'completed') {
      this.toastService.success(body, title);
    } else if (status === 'failed') {
      this.toastService.error(body, title);
    }

    if (this.sendDesktopNotification({ title, body, route })) {
      return;
    }

    if (!this.hasGrantedBrowserNotificationPermission()) {
      return;
    }

    const notification = new Notification(title, {
      body,
      tag: tag ?? title,
      icon: '/favicon.ico',
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
      if (route) {
        void this.router.navigateByUrl(route);
      }
    };
  }

  private connectWebSocket(): void {
    if (!isPlatformBrowser(this.platformId) || this.websocket || !this.authRepository.isAuthenticated()) {
      return;
    }

    const url = this.buildWebSocketUrl();
    if (!url) {
      return;
    }

    this.clearReconnectTimer();
    const socket = new WebSocket(url);
    this.websocket = socket;

    socket.onopen = () => {
      this.startPing();
    };

    socket.onmessage = (event) => {
      this.handleSocketMessage(event.data);
    };

    socket.onerror = () => {
      socket.close();
    };

    socket.onclose = () => {
      this.stopPing();
      if (this.websocket === socket) {
        this.websocket = null;
      }

      if (!this.manualStop && this.started) {
        this.scheduleReconnect();
      }
    };
  }

  private handleSocketMessage(rawMessage: string): void {
    try {
      const payload = JSON.parse(rawMessage) as TaskStatusChangedEvent | { event: 'pong' };
      if (payload.event !== 'task-status-changed') {
        return;
      }

      const status = this.normalizeStatus(payload.status);
      if (!this.isTerminalStatus(status)) {
        return;
      }

      this.notifyTaskResult({
        title: this.buildNotificationTitle(payload.task_kind, status),
        body: this.buildNotificationBody(payload.label, status),
        status,
        route: payload.route,
        tag: `${payload.task_kind}:${payload.task_id}:${status}`,
      });
    } catch (error) {
      console.warn('No se pudo procesar el mensaje WebSocket de tareas', error);
    }
  }

  private buildWebSocketUrl(): string | null {
    const token = this.authRepository.getToken();
    if (!token) {
      return null;
    }

    const apiBase = environment.apiUrl.replace(/\/api\/v1\/?$/, '');
    const wsBase = apiBase.replace(/^http:\/\//i, 'ws://').replace(/^https:\/\//i, 'wss://');
    return `${wsBase}/api/v1/ws/task-notifications?token=${encodeURIComponent(token)}`;
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) {
      return;
    }

    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connectWebSocket();
    }, this.reconnectDelayMs);
  }

  private clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      window.clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private startPing(): void {
    this.stopPing();
    this.pingTimer = window.setInterval(() => {
      if (this.websocket?.readyState === WebSocket.OPEN) {
        this.websocket.send('ping');
      }
    }, this.pingIntervalMs);
  }

  private stopPing(): void {
    if (this.pingTimer !== null) {
      window.clearInterval(this.pingTimer);
      this.pingTimer = null;
    }
  }

  private async requestNotificationPermission(): Promise<void> {
    if (!this.supportsBrowserNotifications() || Notification.permission !== 'default') {
      return;
    }

    try {
      await Notification.requestPermission();
    } catch (error) {
      console.warn('No se pudo solicitar permiso de notificaciones', error);
    }
  }

  private registerDesktopClickHandler(): void {
    const bridge = this.getDesktopBridge();
    if (!bridge?.onClick || this.desktopClickUnsubscribe) {
      return;
    }

    this.desktopClickUnsubscribe = bridge.onClick((payload) => {
      if (!payload?.route) {
        return;
      }

      window.focus();
      void this.router.navigateByUrl(payload.route);
    });
  }

  private sendDesktopNotification(payload: DesktopNotificationPayload): boolean {
    const bridge = this.getDesktopBridge();
    if (!bridge?.notify) {
      return false;
    }

    bridge.notify(payload);
    return true;
  }

  private getDesktopBridge(): DesktopNotificationsBridge | undefined {
    if (!isPlatformBrowser(this.platformId)) {
      return undefined;
    }

    return (window as BrowserWindowWithDesktopNotifications).desktopNotifications;
  }

  private supportsBrowserNotifications(): boolean {
    return isPlatformBrowser(this.platformId) && 'Notification' in window;
  }

  private hasGrantedBrowserNotificationPermission(): boolean {
    return isPlatformBrowser(this.platformId) && 'Notification' in window && Notification.permission === 'granted';
  }

  private normalizeStatus(status: string): StatusType | string {
    return status?.toLowerCase?.() ?? '';
  }

  private isTerminalStatus(status: string): boolean {
    return status === 'completed' || status === 'failed';
  }

  private buildNotificationTitle(kind: TrackableTaskKind, status: string): string {
    const entityMap: Record<TrackableTaskKind, string> = {
      audit: 'Auditoría',
      comparison: 'Comparación',
      schema: 'Auditoría de schemas',
      'url-validation': 'Validación de URLs',
    };

    const suffix = status === 'completed' ? 'completada' : 'fallida';
    return `${entityMap[kind]} ${suffix}`;
  }

  private buildNotificationBody(label: string, status: string): string {
    if (status === 'completed') {
      return `${label} ya terminó y está lista para revisarse.`;
    }

    return `${label} terminó con error.`;
  }
}
