import {
  ApplicationConfig,
  importProvidersFrom,
  provideBrowserGlobalErrorListeners,
  provideZonelessChangeDetection
} from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration, withEventReplay } from '@angular/platform-browser';
import {
  TranslationImplementationRepository
} from '@/app/infrastructure/repositories/translation/translation.implementation.repository';
import {TranslationRepository} from '@/app/domain/repositories/translation/translation.repository';
import {AuthImplementationRepository} from '@/app/infrastructure/repositories/auth/auth.implementation.repository';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {TargetImplementationRepository} from '@/app/infrastructure/repositories/target/target.implementation.repository';
import {TranslateLoader, TranslateModule} from '@ngx-translate/core';
import {HttpClient, provideHttpClient, withFetch} from '@angular/common/http';
import {Observable} from 'rxjs';

// Custom TranslateLoader
export class CustomTranslateLoader implements TranslateLoader {
  constructor(private http: HttpClient) {}

  getTranslation(lang: string): Observable<any> {
    return this.http.get(`/assets/i18n/${lang}.json`);
  }
}
// Factory para el TranslateLoader
export function HttpLoaderFactory(http: HttpClient) {
  return new CustomTranslateLoader(http);
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideZonelessChangeDetection(),
    provideRouter(routes),
    provideClientHydration(withEventReplay()),
    provideHttpClient(withFetch()),
    importProvidersFrom(
      TranslateModule.forRoot({
        defaultLanguage: 'es',
        loader: {
          provide: TranslateLoader,
          useFactory: HttpLoaderFactory,
          deps: [HttpClient]
        }
      })
    ),
    { provide: TranslationRepository, useClass: TranslationImplementationRepository },
    { provide: AuthRepository, useClass: AuthImplementationRepository },
    { provide: TargetRepository, useClass: TargetImplementationRepository }
  ]
};
