import { Component, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { TranslateService, TranslateModule } from '@ngx-translate/core';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, TranslateModule],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('seo-bot-ai');
  private readonly translate = inject(TranslateService);

  constructor() {
    // Inicializar idioma por defecto
    this.translate.setDefaultLang('es');
    this.translate.use('es');
  }
}
