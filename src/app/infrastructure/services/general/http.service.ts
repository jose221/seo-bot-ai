import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {HttpClientHelper} from '@/app/helper/http-client.helper';
import {environment} from '@/environments/environment';
import {Injectable} from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class HttpService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: environment.apiUrl,
      timeout: environment.timeout,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    this.axiosInstance.interceptors.request.use(
      (config: any) => {
        console.log('Making API request:', config.method?.toUpperCase(), config.url);
        return config;
      },
      (error: any) => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    this.axiosInstance.interceptors.response.use(
      (response: any) => {
        console.log('API response received:', response.status, response.statusText);
        return response;
      },
      (error: any) => {
        console.error('Response error:', error.response?.status, error.message);
        return Promise.reject(error);
      }
    );
  }

  private getHeaders(token?: string | null, config?: AxiosRequestConfig): AxiosRequestConfig {
    const headers: Record<string, string> = {
      ...(config?.headers as Record<string, string> || {})
    };

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return {
      ...config,
      headers
    };
  }

  async get<T>(url: string, query?: any|object, config?: AxiosRequestConfig, token?: string | null): Promise<T> {
    if (query) {
      url += '?' + HttpClientHelper.objectToQueryString(query);
    }
    const finalConfig = this.getHeaders(token, config);
    const response: AxiosResponse<T> = await this.axiosInstance.get(url, finalConfig);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig, token?: string | null): Promise<T> {
    const finalConfig = this.getHeaders(token, config);
    const response: AxiosResponse<T> = await this.axiosInstance.post(url, data, finalConfig);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig, token?: string | null): Promise<T> {
    const finalConfig = this.getHeaders(token, config);
    const response: AxiosResponse<T> = await this.axiosInstance.put(url, data, finalConfig);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig, token?: string | null): Promise<T> {
    const finalConfig = this.getHeaders(token, config);
    const response: AxiosResponse<T> = await this.axiosInstance.delete(url, finalConfig);
    return response.data;
  }
}
