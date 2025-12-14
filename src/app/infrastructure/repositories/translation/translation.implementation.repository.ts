import { Injectable } from '@angular/core';
import { TranslationRepository } from '@/app/domain/repositories/translation/translation.repository';
import { HttpDefaultModel } from '@/app/domain/models/http/http-default.model';
import {TranslationService} from '@/app/infrastructure/services/translation/translation.service';


@Injectable()
export class TranslationImplementationRepository implements TranslationRepository {
  public currentLanguage: string = 'es';
  constructor(private translationService: TranslationService) {
    this.currentLanguage = translationService.currentLanguage;
  }

  init() {
    this.translationService.init();
  }

  getTranslation(key: string, lang: string = ""): string {
    lang = lang || this.currentLanguage;
    return this.translationService.getTranslation(key, lang);
  }

  async translate(key: string, lang: string = "") {
    lang = lang || this.currentLanguage;
    return await this.translationService.translate(key, lang);
  }

  async loadTranslationsAsync(search?: string, language=this.currentLanguage): Promise<HttpDefaultModel<any>|any>{
    const key = language;
    return await (this.translationService.loadTranslationsAsync(key, search))
  }

  async createOrUpdate(lang: string = "",params?: { key: string, value: string, autoSeparate: boolean }){
    lang = lang || this.currentLanguage;
    return await this.translationService.createOrUpdate(lang, params)
  }

  async delete(lang: string = "", params?: { key: string, autoSeparate: boolean }){
    lang = lang || this.currentLanguage;
    console.log(params)
    return await this.translationService.delete(lang, params)
  }

  setLanguage(lang: string) {
    this.translationService.setLanguage(lang);
  }
  instant(key: string): string {
    return this.translationService.instant(key);
  }
  async loadTranslations(key: string, search?: string) {
    return await this.translationService.loadTranslations(key, search);
  }
}
