import { Injectable } from '@angular/core';
import Swal, { SweetAlertOptions, SweetAlertResult } from 'sweetalert2';
import {TranslationService} from '@/app/application/services/translation/translation.service';

@Injectable({
  providedIn: 'root',
})

export class SweetAlertUtil {
  swal = Swal;
  constructor(private readonly _translationService: TranslationService) {
  }
  // Crear un alerta con los parámetros predeterminados
  async success(title: string = "Good job!", text: string = "Process has been successfully", icon: any = "success", confirmButtonText: any= 'OK'): Promise<SweetAlertResult<any>> {
    return Swal.fire({
      title: await this._translationService.loadTranslationsAsync(title),
      text: await this._translationService.loadTranslationsAsync(text),
      icon: icon,
      confirmButtonText: await this._translationService.loadTranslationsAsync(confirmButtonText)
    })
  }

  async error(title: string = "Oops...", text: string = "Something went wrong!", icon: any = "error", footer?: string): Promise<SweetAlertResult<any>> {
    return Swal.fire({
      icon: icon,
      title: await this._translationService.loadTranslationsAsync(title),
      text: await this._translationService.loadTranslationsAsync(text),
      footer: footer ? await this._translationService.loadTranslationsAsync(footer) : ''
    });
  }

  // Crear un alerta con todas las opciones posibles
  async fire(options: SweetAlertOptions | any, translateList:string[] = []): Promise<SweetAlertResult<any>> {
    for(let translateText of translateList) {
      options[translateText] = options[translateText] ? await this._translationService.loadTranslationsAsync(options[translateText] ) : ''
    }
    return Swal.fire(options)
  }

  // Otros métodos aquí con otras opciones de swal
}
