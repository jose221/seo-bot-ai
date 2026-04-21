import { inject, Injectable, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { DOCUMENT } from '@angular/common';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  private readonly platformId = inject(PLATFORM_ID);
  private readonly document = inject(DOCUMENT);

  show(): void {
    if (!isPlatformBrowser(this.platformId)) return;
    const el = this.document.getElementById('global-loading');
    if (el) el.style.display = 'block';
  }

  hide(): void {
    if (!isPlatformBrowser(this.platformId)) return;
    const el = this.document.getElementById('global-loading');
    if (el) el.style.display = 'none';
  }
}


