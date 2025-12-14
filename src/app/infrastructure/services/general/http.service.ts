import { Injectable } from '@angular/core';
import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import {HttpClientHelper} from '../../../helper/http-client.helper';
import {environment} from '@/environments/environment';

@Injectable({
  providedIn: 'root'
})
export class HttpService {
  private axiosInstance: AxiosInstance;

  constructor() {
    this.axiosInstance = axios.create({
      baseURL: environment.apiUrl,
      headers: {
        'Content-Type': 'application/json'
      }
    });

    // Interceptor de request para logging
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

    // Interceptor de response para logging
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

  async get<T>(url: string, query?:any|object, config?: AxiosRequestConfig): Promise<T> {
    if (query) {
      url += '?' + HttpClientHelper.objectToQueryString(query);
    }
    const response: AxiosResponse<T> = await this.axiosInstance.get(url, config);
    return response.data;
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.post(url, data, config);
    return response.data;
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.put(url, data, config);
    return response.data;
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response: AxiosResponse<T> = await this.axiosInstance.delete(url, config);
    return response.data;
  }
}
