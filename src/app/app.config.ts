import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
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

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes), provideClientHydration(withEventReplay()),
    { provide: TranslationRepository, useClass: TranslationImplementationRepository },
    { provide: AuthRepository, useClass: AuthImplementationRepository },
    { provide: TargetRepository, useClass: TargetImplementationRepository }
  ]
};
