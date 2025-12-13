
export class HttpClientHelper{
  static objectToQueryString(obj: any): string {
    const parts: string[] = [];

    Object.keys(obj).forEach(key => {
      if(obj[key]){ // Verifica si el valor asociado a la clave es un arreglo
        if (Array.isArray(obj[key])) {
          // Maneja cada elemento del arreglo individualmente
          obj[key].forEach((element: any) => {
            parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(element)}`);
          });
        } else {
          // Maneja el caso para valores primitivos
          parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(obj[key])}`);
        }
      }
    });

    return parts.join('&');
  }
}
