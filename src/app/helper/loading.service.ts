import { Injectable } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {

  show(): void {
    const el = document.getElementById('global-loading');
    if (el) el.style.display = 'block';
  }

  hide(): void {
    const el = document.getElementById('global-loading');
    if (el) el.style.display = 'none';
  }
}


