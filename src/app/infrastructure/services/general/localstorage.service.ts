import { Injectable, PLATFORM_ID, inject } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

interface StorageItem {
  value: any;
  expiry: number | null;
}

@Injectable({
  providedIn: 'root'
})
export class LocalstorageService {
  private readonly platformId = inject(PLATFORM_ID);

  /**
   * Guarda un valor con un tiempo de vida opcional.
   * @param key Clave del storage
   * @param value Valor a guardar
   * @param days Días de validez (opcional, null para infinito)
   */
  set(key: string, value: any, days: number | null = 7): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    const expiry = days
      ? new Date().getTime() + (days * 24 * 60 * 60 * 1000)
      : null;

    const item: StorageItem = {
      value: value,
      expiry: expiry
    };

    localStorage.setItem(key, JSON.stringify(item));
  }

  /**
   * Obtiene un valor. Si ha expirado, lo elimina y devuelve null.
   */
  get(key: string): any | null {
    if (!isPlatformBrowser(this.platformId)) {
      return null;
    }

    const itemStr = localStorage.getItem(key);
    if (!itemStr) {
      return null;
    }

    try {
      const item: StorageItem = JSON.parse(itemStr);
      const now = new Date().getTime();

      // Comprobar si tiene expiración y si ya pasó
      if (item.expiry && now > item.expiry) {
        localStorage.removeItem(key);
        return null;
      }

      return item.value;
    } catch (e) {
      // Si el formato no coincide (por datos viejos), devolvemos el string original o null
      return itemStr;
    }
  }

  /**
   * Elimina una clave de localStorage.
   */
  remove(key: string): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    localStorage.removeItem(key);
  }

  /**
   * Limpia todo el contenido de localStorage.
   */
  clear(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }
    localStorage.clear();
  }
}
