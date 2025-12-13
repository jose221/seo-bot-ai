import { AxiosRequestConfig } from "axios";

export class AuthenticationHeader {
  public get headers(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  public get headersKey(): Record<string, string> {
    return {
      Authorization: `Bearer ${this.key}`,
      'Content-Type': 'multipart/form-data',
      'Accept': 'application/json'
    };
  }

  constructor() {}

  public get token(): string | null {
    return localStorage.getItem('token');
  }

  public get key(): string | null {
    return localStorage.getItem('key');
  }

  public setHeaderToken(token: string): Record<string, string> {
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };
  }

  public setHeaderMultipartFormDataToken(token: string): Record<string, string> {
    return {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'multipart/form-data',
      'Accept': 'application/json'
    };
  }

  // Método auxiliar para obtener la configuración completa de Axios
  public getAxiosConfig(): AxiosRequestConfig {
    return {
      headers: this.headers
    };
  }

  // Método auxiliar para obtener la configuración de Axios con multipart
  public getAxiosConfigMultipart(): AxiosRequestConfig {
    return {
      headers: this.headersKey
    };
  }
}
