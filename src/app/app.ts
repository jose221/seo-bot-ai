import { Component, PLATFORM_ID, inject, signal } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { TranslateService, TranslateModule } from '@ngx-translate/core';
import { AppToast } from '@/app/presentation/components/general/app-toast/app-toast';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TranslateModule, AppToast],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('seo-bot-ai');
  private readonly translate = inject(TranslateService);
  private readonly platformId = inject(PLATFORM_ID);
  protected readonly canReload = isPlatformBrowser(this.platformId);

  constructor() {
    // Inicializar idioma por defecto
    this.translate.setDefaultLang('es');
    this.translate.use('es');
  }

  protected reloadPage(): void {
    if (!this.canReload) {
      return;
    }

    window.location.reload();
  }
}
