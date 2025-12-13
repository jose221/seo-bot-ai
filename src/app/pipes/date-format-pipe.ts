import { Pipe, PipeTransform } from '@angular/core';
import {dateFormat} from '@/app/helper/map-data.helper';

@Pipe({
    name: 'dateFormat',
    standalone: true
})
export class DateFormatPipe implements PipeTransform {
  transform(value: any, format: 'long'|'short', language: 'es' | 'en', includeTime: boolean = false, timeZone: 'UTC' | 'America/Cancun'='America/Cancun' ): string {
    return dateFormat(value, format, language, includeTime, timeZone)
  }
}
