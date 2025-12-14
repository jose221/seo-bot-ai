import { Injectable } from '@angular/core';
import {HttpDefaultModel} from '@/app/domain/models/http/http-default.model';
import {AuthenticationHeader} from '@/app/infrastructure/http/authentication-header/authentication-header';
import {TranslateService} from '@ngx-translate/core';
import {HttpService} from '@/app/infrastructure/services/general/http.service';
import {HttpClientHelper} from '@/app/helper/http-client.helper';
import {environment} from '@/environments/environment';

@Injectable(
  {
    providedIn: 'root'
  }
)
export class TranslationService {
  authenticationHeader = new AuthenticationHeader();
  constructor(private translateService: TranslateService, private httpService: HttpService) {}

  init(): void {
    // Utiliza ngx-translate para establecer el idioma
    this.translateService.getFallbackLang();
  }

  get currentLanguage(): string {
    return localStorage.getItem('lang') ?? 'es';
  }

  getTranslation(key: string, lang: string): string {
    // Utiliza ngx-translate para obtener la traducción según la clave y el idioma
    this.translateService.use(lang);
    return this.instant(key);
  }

  instant(key: string): string {
    const lang = this.translateService.currentLang;

    // Usar el método instant() de TranslateService directamente
    let res = this.translateService.instant(key);

    // Si no encuentra la traducción (devuelve la misma key), intentar cargarla
    if (res === key) {
      // Cargar de forma asíncrona sin bloquear
      this.loadTranslationsAsync(lang, key).then((data) => {
        if (data) {
          // Recargar las traducciones después de obtener nuevos datos
          this.translateService.reloadLang(lang);
        }
      }).catch(err => {
        console.error('Error loading translation:', err);
      });
    }

    return res || key;
  }

  setLanguage(lang: string) {
    this.translateService.use(lang);
    localStorage.setItem('lang', lang);
  }

  async loadTranslations(key: string, search?: string) {
    let queryParams = '';
    if (search) {
      queryParams = HttpClientHelper.objectToQueryString({ search });
    }

    const result = await this.httpService.get<HttpDefaultModel<any>>(
      `${environment.endpoints.translate.loadTranslations}/${key}?${queryParams}`,
      undefined,
      { headers: this.authenticationHeader.headers }
    );

    return result.data;
  }

  async loadTranslationsAsync(key: string, search?: string) {
    let queryParams = '';
    if (search) {
      queryParams = HttpClientHelper.objectToQueryString({ text: search, language: key });
    }

    try {
      const result = await this.httpService.get<HttpDefaultModel<any>>(
        `${environment.endpoints.translate.loadTranslations}?${queryParams}`,
        undefined,
        { headers: this.authenticationHeader.headers }
      );

      return result?.data?.text ?? null;
    } catch (error) {
      console.error('Error loading translations:', error);
      return null;
    }
  }

  async translate(key: string, search?: string) {
    let queryParams = '';
    if (search) {
      queryParams = HttpClientHelper.objectToQueryString({ search });
    }

    const result = await this.httpService.get<HttpDefaultModel<any>>(
      `${environment.endpoints.translate.translate}/${key}?${queryParams}`,
      undefined,
      { headers: this.authenticationHeader.headers }
    );

    return result.data;
  }

  async createOrUpdate(lang: string, params?: { key: string; value: string, autoSeparate: boolean }) {
    return await this.httpService.post<HttpDefaultModel<any>>(
      `${environment.endpoints.translate.createOrUpdate}/${lang}`,
      params,
      { headers: this.authenticationHeader.headers }
    );
  }

  async delete(lang: string, params?: { key: string, autoSeparate: boolean }) {
    return await this.httpService.delete<HttpDefaultModel<any>>(
      `${environment.endpoints.translate.delete}/${lang}`,
      {
        headers: this.authenticationHeader.headers,
        data: params
      }
    );
  }

}
