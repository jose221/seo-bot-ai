import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router } from '@angular/router';

import { AuditRepository } from '@/app/domain/repositories/audit/audit.repository';
import { AuditSchemaRepository } from '@/app/domain/repositories/audit-schema/audit-schema.repository';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { StatusType } from '@/app/domain/types/status.type';

type TrackableTaskKind = 'audit' | 'comparison' | 'schema' | 'url-validation';

interface TrackableTask {
  id: string;
  kind: TrackableTaskKind;
  status: string;
  route: string;
  label: string;
}

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

type BrowserWindowWithDesktopNotifications = Window & {
  desktopNotifications?: DesktopNotificationsBridge;
};

@Injectable({
  providedIn: 'root',
})
export class TaskNotificationService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly router = inject(Router);
  private readonly auditRepository = inject(AuditRepository);
  private readonly auditSchemaRepository = inject(AuditSchemaRepository);
  private readonly auditUrlValidationRepository = inject(AuditUrlValidationRepository);

  private readonly pollIntervalMs = 15000;
  private readonly knownStatuses = new Map<string, string>();

  private started = false;
  private isPolling = false;
  private pollTimer: number | null = null;
  private desktopClickUnsubscribe: (() => void) | null = null;

  start(): void {
    if (!isPlatformBrowser(this.platformId) || this.started) {
      return;
    }

    this.started = true;
    this.registerDesktopClickHandler();
    void this.requestNotificationPermission();
    void this.pollTasks();
    this.pollTimer = window.setInterval(() => {
      void this.pollTasks();
    }, this.pollIntervalMs);
  }

  stop(): void {
    if (this.pollTimer !== null) {
      window.clearInterval(this.pollTimer);
      this.pollTimer = null;
    }

    if (this.desktopClickUnsubscribe) {
      this.desktopClickUnsubscribe();
      this.desktopClickUnsubscribe = null;
    }

    this.started = false;
    this.isPolling = false;
  }

  registerPendingTask(kind: TrackableTaskKind, id: string): void {
    this.knownStatuses.set(this.buildTaskKey(kind, id), 'pending');
  }

  private async pollTasks(): Promise<void> {
    if (this.isPolling) {
      return;
    }

    this.isPolling = true;

    try {
      const taskGroups = await Promise.allSettled([
        this.auditRepository.get(),
        this.auditRepository.getComparisons(),
        this.auditSchemaRepository.getAll(),
        this.auditUrlValidationRepository.getAll(),
      ]);

      const tasks: TrackableTask[] = [];

      if (taskGroups[0].status === 'fulfilled') {
        tasks.push(
          ...taskGroups[0].value.map((audit) => ({
            id: audit.id,
            kind: 'audit' as const,
            status: audit.status,
            route: `/admin/audit/${audit.id}`,
            label: audit.web_page?.name || audit.web_page?.url || `Auditoría ${audit.id}`,
          })),
        );
      }

      if (taskGroups[1].status === 'fulfilled') {
        tasks.push(
          ...taskGroups[1].value.map((comparison) => ({
            id: comparison.id,
            kind: 'comparison' as const,
            status: comparison.status,
            route: `/admin/audit/comparisons/${comparison.id}`,
            label: comparison.base_url || `Comparación ${comparison.id}`,
          })),
        );
      }

      if (taskGroups[2].status === 'fulfilled') {
        tasks.push(
          ...taskGroups[2].value.items.map((schema) => ({
            id: schema.id,
            kind: 'schema' as const,
            status: schema.status,
            route: `/admin/audit/schemas/${schema.id}`,
            label: schema.programming_language || `Schema ${schema.id}`,
          })),
        );
      }

      if (taskGroups[3].status === 'fulfilled') {
        tasks.push(
          ...taskGroups[3].value.items.map((validation) => ({
            id: validation.id,
            kind: 'url-validation' as const,
            status: validation.status,
            route: `/admin/audit/url-validations/${validation.id}`,
            label: validation.name_validation || `Validación ${validation.id}`,
          })),
        );
      }

      for (const task of tasks) {
        const key = this.buildTaskKey(task.kind, task.id);
        const previousStatus = this.knownStatuses.get(key);
        const nextStatus = this.normalizeStatus(task.status);

        if (
          previousStatus &&
          previousStatus !== nextStatus &&
          this.isTerminalStatus(nextStatus) &&
          !this.isTerminalStatus(previousStatus)
        ) {
          this.notify(task, nextStatus);
        }

        this.knownStatuses.set(key, nextStatus);
      }
    } finally {
      this.isPolling = false;
    }
  }

  private notify(task: TrackableTask, status: string): void {
    const title = this.buildNotificationTitle(task.kind, status);
    const body = this.buildNotificationBody(task.label, status);

    if (this.sendDesktopNotification({ title, body, route: task.route })) {
      return;
    }

    if (!this.hasGrantedBrowserNotificationPermission()) {
      return;
    }

    const notification = new Notification(title, {
      body,
      tag: this.buildTaskKey(task.kind, task.id),
      icon: '/favicon.ico',
    });

    notification.onclick = () => {
      window.focus();
      notification.close();
      void this.router.navigateByUrl(task.route);
    };
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

  private buildTaskKey(kind: TrackableTaskKind, id: string): string {
    return `${kind}:${id}`;
  }

  private normalizeStatus(status: string): StatusType | string {
    const normalized = status?.toLowerCase?.() ?? '';
    return normalized;
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
