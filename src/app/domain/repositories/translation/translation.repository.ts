import {HttpDefaultModel} from '@/app/domain/models/http/http-default.model';


export abstract class TranslationRepository {
  abstract getTranslation(key: string, lang: string): string;
  abstract init(): void;
  abstract setLanguage(lang: string): void;
  abstract get currentLanguage(): string;
  abstract translate(key: string, search?: string): Promise<HttpDefaultModel<any> | any>;
  abstract loadTranslationsAsync(key: string, search?: string): Promise<HttpDefaultModel<any> | any>;
  abstract createOrUpdate(lang: string, params?: { key: string; value: string, autoSeparate: boolean }): Promise<HttpDefaultModel<any> | any>;
  abstract delete(lang: string, params?: { key: string, autoSeparate: boolean }): Promise<HttpDefaultModel<any> | any>;
  abstract instant(key: string): string;
  abstract loadTranslations(key: string, search?: string): Promise<HttpDefaultModel<any> | any>;
}
