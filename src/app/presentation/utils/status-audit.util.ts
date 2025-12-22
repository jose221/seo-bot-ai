import {Injectable} from '@angular/core';

@Injectable(
  {
     providedIn: 'root'
  }
)
export class StatusAuditUtil{
  public getStatusText(status: string): string {
    const statusMap: Record<string, string> = {
      'pending': 'Pendiente',
      'in_progress': 'En Progreso',
      'completed': 'Completado',
      'failed': 'Fallido'
    };
    return statusMap[status] || status;
  }
}
