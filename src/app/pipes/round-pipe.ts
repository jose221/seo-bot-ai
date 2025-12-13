import { Pipe, PipeTransform } from '@angular/core';

@Pipe({
  standalone: true,
  name: 'round'
})
export class RoundPipe implements PipeTransform {

  transform(value: any, decimals: number = 2): any {
    // Verifica si el valor es de tipo numérico
    if (typeof value === 'number') {
      return value.toFixed(decimals);
    }
    // Si no es numérico, devuelve el valor sin modificar
    return (String(value)).toUpperCase();
  }

}
