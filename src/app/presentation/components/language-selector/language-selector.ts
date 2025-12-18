import { Component, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';
import { NgClass } from '@angular/common';

@Component({
  selector: 'app-language-selector',
  imports: [NgClass],
  templateUrl: './language-selector.html',
  styleUrl: './language-selector.scss',
})
export class LanguageSelector {
  private readonly translate = inject(TranslateService);

  protected readonly languages = [
    { code: 'es', name: 'Español', flag: '🇪🇸' },
    { code: 'en', name: 'English', flag: '🇺🇸' },
  ];

  get currentLanguage() {
    return this.translate.currentLang || this.translate.defaultLang || 'es';
  }

  changeLanguage(langCode: string) {
    this.translate.use(langCode);
  }
}

