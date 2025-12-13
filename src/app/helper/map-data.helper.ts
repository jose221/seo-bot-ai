
/**
 * Groups an array of objects by a property
 * @param {Array} array - The array to will be grouped
 * @param {string} property - The property to group by
 * @return {Object} - An object containing the grouped arrays
 */
export function groupBy(array: any[], property: string): any|object {
  return array.reduce((result: any, obj: any) => {
    const keys = property.split('.'); // Dividir la propiedad en partes
    let value = obj;

    for (const key of keys) {
      value = value[key]; // Acceder a la propiedad anidada
      if (value === undefined) {
        break; // Si alguna parte de la propiedad es undefined, salir del bucle
      }
    }

    if (value !== undefined) {
      if (!result[value]) {
        result[value] = [];
      }
      result[value].push(obj);
    }

    return result;
  }, {});
}

/**
 * Groups an array of objects by a specified property and returns an array of objects with the property and its items
 * @param {Array} array - The array of objects to be grouped
 * @param {string} property - The property to group by
 * @return {Array} - An array of objects with the property and its items
 */
export function groupByUnique(array: any[], property: string): {key: string, value: any, items:[]}[] {
  const groupedMap = new Map();

  array.forEach((obj: any) => {
    const value = obj[property];
    if (!groupedMap.has(value)) {
      obj.items = obj.items ?? [];
      groupedMap.set(value, obj);
    }
    groupedMap.get(value).items.push(obj);
  });

  return Array.from(groupedMap.values());
}

/**
 * Push an item or array of items into the array if they do not already exist.
 *
 * @template T - The type of elements in the array.
 *
 * @param {T[]} array - The array to push into.
 * @param {T | T[]} itemOrItems - The item or array of items to push if they do not exist.
 *
 * @returns {T[]} - The updated array.
 */
export function pushIfNotExist<T>(array: T[], itemOrItems: T | T[]): T[] {
  if(Array.isArray(itemOrItems)) {
    itemOrItems.forEach(item => {
      if(!array.includes(item)) {
        array.push(item);
      }
    });
  }
  else {
    if(!array.includes(itemOrItems)) {
      array.push(itemOrItems);
    }
  }

  return array;
}

export function pushIfNotExistByKey<T>(array: any[], itemOrItems: any, key: string): T {
  if (Array.isArray(itemOrItems)) {
    itemOrItems.forEach(item => {
      if (!array.some((existingItem: any) => existingItem[key] === item[key])) {
        array.push(item);
      }
    });
  } else {
    if (!array.some((existingItem: any) => existingItem[key] === itemOrItems[key])) {
      array.push(itemOrItems);
    }
  }

  return array as unknown as T;
}



/**
 * Clase para realizar consultas a un array de objetos
 */
export class Query {
  private data: any[];
  private filters: { key: any | any[], value: string | string[], type:string }[];

  constructor(data: any[]) {
    this.data = data;
    this.filters = [];
  }

  get(): any {
    let items: any[] = this.data;
    for (const { key, value, type } of this.filters) {
      if (type === 'like') {
        items = this.filterLike(items, { key: key as any, value: value as any });
      } else if (type === 'whereIn') {
        items = this.filterWhereIn(items, { key: key, value: value as any[] });
      }
      else if (type === 'likeByPattern') {
        items = this.filterLikeByPattern(items, { key: key as any, value: value as any });
      }

      // ... (otros tipos de filtro)
    }

    return items;
  }
  private filterWhereIn(items: any[], filter: { key: any[], value: any[] }): any {
    const filteredData: any[] = [];
    for (const item of items) {
      for (const k of filter.key) {
        if (k in item && filter.value.includes(item[k])) {
          filteredData.push(item);
          break;
        }
      }
    }
    return filteredData;
  }
  private filterLike(items: any[], filter: { key: any[], value: string }): any {
    const filteredData: any[] = [];
    for (const item of items) {
      //like
      for(const k of filter.key){
        let itemSearch = item;
        for(const key of this.parseNestedKey(k)){
          itemSearch = itemSearch[key];
        }
        if (this.likeInFilterIgnoreAccentsAndCase(itemSearch, filter.value)) {
          filteredData.push(item);
          break;
        }
      }
    }
    return filteredData;
  }

  private filterLikeByPattern(items: any[], filter: { key: string[], value: string }): any {
    const filteredData: any[] = [];
    for (const item of items) {
      //like
      for(const k of filter.key){
        let callbackCompilePattern = this.compilePattern(k);
        if (this.likeInFilterIgnoreAccentsAndCase((callbackCompilePattern(item)), filter.value)) {
          filteredData.push(item);
          break;
        }
      }
    }
    return filteredData;
  }

  private parseNestedKey(key: string): string[] {
    return key.split('.');
  }

  private likeCondition(value: string | any[keyof any], pattern: string): boolean {
    if (typeof value === 'string') {
      const normalizedValue = this.removeAccents((String(value)).toLowerCase());
      const normalizedPattern = this.removeAccents((String(pattern)).toLowerCase());
      return normalizedValue.includes(normalizedPattern);
    }
    return false;
  }

  private removeAccents(text: string): string {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }
  public like(keys:any[] | string ='', value: any[] | string): Query {
    if(value){
      if (typeof keys === 'string') {
        keys = [keys];
      }
      if (typeof value === 'string') {
        this.filters.push({ key: keys, value, type:'like' });
      }else{
        value.forEach(item =>{
          this.filters.push({ key: keys, value:item, type:'like' });
        })
      }
    }
    //this.filters = keys.map(key => ({ key, value, type:'likeOr' }));
    return this;
  }

  likeInFilterIgnoreAccentsAndCase(value:any, pattern: any) {
    const normalizedValue = this.removeAccents((String(value)).toLowerCase());
    const normalizedPattern = this.removeAccents((String(pattern)).toLowerCase());
    const regexPattern = normalizedPattern
      .replace(/%/g, '.*')
      .replace(/_/g, '.');
    const regex = new RegExp(regexPattern, 'i');
    return regex.test(normalizedValue);
  }

  public whereIn(keys: string[], values: any[]): Query {
    if (values && values.length > 0) {
      this.filters.push({ key: keys, value: values, type: 'whereIn' });
    }
    return this;
  }
  public filterByPattern(pattern: string | string[], value: string): Query {
    if (pattern) {
      if (typeof pattern === 'string') {
        pattern = [pattern];
      }
      this.filters.push({ key: pattern, value, type:'likeByPattern' });
    }
    return this;
  }

  compilePattern(pattern: string): (obj: any) => string {
    // Primero, intenta encontrar coincidencias para patrones anidados y simples
    const matches = ((pattern.match(/{[\w.]+}/g) || []) as any[]).map(match => match.replace(/[{}]/g, ''));
    return (obj: any): string => {
      return matches.reduce((acc: string, match: string): string => {
        // Aquí, path será un array de longitud 1 para claves simples, o más para claves anidadas
        const path = match.split('.');
        const resolvedValue = path.reduce((o: any, key: string) => {
          return o && o.hasOwnProperty(key) ? o[key] : null;
        }, obj);
        // Reemplaza tanto patrones anidados como simples en la cadena
        return acc.replace(new RegExp(`{${match}}`, 'g'), resolvedValue !== null ? resolvedValue.toString() : '');
      }, pattern);
    };
  }
}

/**
 * Realiza una copia profunda de un objeto
 * @param obj Objeto a copiar
 * @param visited Mapa de objetos visitados
 */
export function deepCopy<T>(obj: T, visited = new WeakMap()): T {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }

  if (visited.has(obj)) {
    return visited.get(obj);
  }

  if (obj instanceof Date) {
    return new Date(obj) as any;
  }

  if (Array.isArray(obj)) {
    const copyArr: any[] = [];
    visited.set(obj, copyArr);
    for (let i = 0; i < obj.length; i++) {
      copyArr[i] = deepCopy(obj[i], visited);
    }
    return copyArr as any;
  }

  if (obj instanceof Object) {
    const copyObj = {} as T;
    visited.set(obj, copyObj);
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        copyObj[key] = deepCopy(obj[key], visited);
      }
    }
    return copyObj;
  }

  throw new Error("Unable to copy object");
}

export function calculateAccumulatedSumSimple(arr: number[]) {
  let accumulatedSum = 0;
  arr.map(item => accumulatedSum += item);
  return accumulatedSum;
}
export function calculateAccumulatedSum(array:Array<any>, attribute:any) {
  return array.reduce((accumulator, object) => {
    if (attribute in object) {
      accumulator += object[attribute];
    }
    return accumulator;
  }, 0);
}

export function concatenateNames(
  objectsArray: Array<any>,
  searchParam: string,
  callbackValue: (arg: string) => string = (arg) => arg
): string {
  // Inicializar una variable vacía para almacenar los nombres concatenados
  let concatenatedNames = '';

  // Dividir el parámetro de búsqueda en sus componentes
  const searchKeys = searchParam.split('.');

  // Iterar a través del arreglo y concatenar los nombres
  objectsArray.forEach((obj, index) => {
    let value = obj;

    // Navegar a través de los componentes del parámetro de búsqueda para encontrar el valor
    for (const key of searchKeys) {
      value = value[key];
    }

    concatenatedNames += callbackValue(value);

    // Agregar una coma y un espacio después de cada nombre, excepto el último
    if (index < objectsArray.length - 1) {
      concatenatedNames += ', ';
    }
  });

  // Retornar la variable con los nombres concatenados
  return concatenatedNames;
}

export function capitalizeFirstLetter(str: string): string {
  return (String(str)).charAt(0).toUpperCase() + (String(str)).slice(1).toLowerCase();
}

export function deepEqual(obj1: any, obj2: any): boolean {
  if (obj1 === obj2) return true;

  if (typeof obj1 !== 'object' || obj1 === null || typeof obj2 !== 'object' || obj2 === null) {
    return false;
  }

  const keys1 = Object.keys(obj1);
  const keys2 = Object.keys(obj2);

  if (keys1.length !== keys2.length) return false;

  for (const key of keys1) {
    if (!keys2.includes(key) || !deepEqual(obj1[key], obj2[key])) {
      return false;
    }
  }

  return true;
}

export function compareObjects(o1: any, o2: any,  key:string='id'): boolean {
  return o1[key] === o2[key];  // compara por la propiedad 'id'
}
export function arraysAreEqual(arr1: any[], arr2: any[], keys:string| string[] ='id'): boolean {
  if (arr1.length !== arr2.length) return false;
  for (let i = 0; i < arr1.length; i++) {
    if(typeof keys === 'string'){
      if (arr1[i][keys] !== arr2[i][keys]) return false;
    }else if (Array.isArray(keys)){
      for (const key of keys) {
        if (arr1[i][key] !== arr2[i][key]) return false;
      }
    }
  }
  return true;
};


export function orderBy(data: Array<any>, column: string, ascending = true) {
  return data.sort((a, b) => {
    if (ascending) {
      return a[column] - b[column];
    } else {
      return b[column] - a[column];
    }
  });
}

export function generateColumns(data: Array<any>, removeColumns: Array<string> = []) {
  let columns = (Object.keys(data[0])).filter(column => !removeColumns.includes(column));
  return columns;
}

export function orderByString(data: Array<any>, column: string, ascending = true) {
  return data.sort((a, b) => {
    if (ascending) {
      return a[column].localeCompare(b[column]);
    } else {
      return b[column].localeCompare(a[column]);
    }
  });
}

export function orderByDate(data: Array<any>, column: string, ascending = true) {
  return data.sort((a, b) => {
    const dateA = new Date(a[column]);
    const dateB = new Date(b[column]);

    // Manejar fechas inválidas
    const timeA = isNaN(dateA.getTime()) ? 0 : dateA.getTime();
    const timeB = isNaN(dateB.getTime()) ? 0 : dateB.getTime();

    if (ascending) {
      return timeA - timeB;
    } else {
      return timeB - timeA;
    }
  });
}

/**
 * Sorts the given array of strings in ascending or descending order.
 *
 * @param {string[]} data - The array of strings to be sorted.
 * @param {boolean} [ascending=true] - Optional. Set to true to sort in ascending order, false for descending order.
 *                                     Default is true for ascending order.
 * @return {string[]} - The sorted array of strings.
 */
export function orderBySimple(data: string[], ascending = true): string[] {
  return data.sort((a, b) => {
    if (ascending) {
      return a.localeCompare(b);
    } else {
      return b.localeCompare(a);
    }
  });
}

export function orderByArray(data: Array<any>, column: string, keys: Array<string>) {
  let newData: any = [];
  for (const key of keys) {
    const item = data.filter(item => item[column] == key);
    data = data.filter(item => item[column] != key);
    newData = [...newData, ...item];
  }
  newData = [...newData, ...data];
  return newData;
}

export function orderByMatrix(data: Array<any>, key: string, column: string, ascending = true) {
  return data.map(item => {
    item[key] = orderBy(item[key] ?? [], column, ascending)
    return item
  })
}


export function mergeArraysByKey(array1: Array<any>, array2: Array<any>, key: string) {
  // Crear un mapa para un acceso rápido a los objetos por su clave única
  const merged = new Map();

  // Primero, agregamos los elementos del segundo arreglo al mapa
  array2.forEach(item => merged.set(item[key], item));

  // Luego, sobrescribimos con los elementos del primer arreglo, dando prioridad a sus valores
  array1.forEach(item => merged.set(item[key], { ...merged.get(item[key]), ...item }));

  // Convertimos el mapa en un arreglo
  return Array.from(merged.values());
}
export function removeDuplicates(array: Array<any>, key:string): Array<any> {
  return array.filter((item, index, self) =>
      index === self.findIndex((t) => (
        t[key] === item[key]
      ))
  );
}

export function removeDuplicatesStrict(array: Array<any>): Array<any> {
  return array.filter((item, index, self) =>
      index === self.findIndex((t) =>
        JSON.stringify(t) === JSON.stringify(item)
      )
  );
}
export function areAllKeysNullorUndefined(obj: any): boolean  {
  return Object.values(obj).every(value => value === null || value === undefined);
}

export function removeArrayNullorUndefined(obj: any[], key = null): any  {
  return obj.filter(value => {
    let kvalue = key ? value[key] : value;
    return kvalue !== null && kvalue !== undefined && kvalue !== '';
  });
}

/**
 * Renombra las claves de los objetos en un arreglo agregando o eliminando prefijos especificados.
 *
 * @param {any[]} objects - Arreglo de objetos cuyas claves serán renombradas.
 * @param {string[]} prefixes - Prefijos a agregar o eliminar.
 * @param {boolean} add - Indica si se deben agregar (true) o eliminar (false) los prefijos.
 * @returns {any[]} Arreglo de objetos con claves renombradas.
 */
/**
 * Renombra las claves de los objetos en un arreglo agregando o eliminando prefijos especificados.
 * Si se agrega un prefijo, se crea un nuevo objeto por cada prefijo para cada objeto en el arreglo.
 *
 * @param {any[]} objects - Arreglo de objetos cuyas claves serán renombradas.
 * @param {string[]} prefixes - Prefijos a agregar o eliminar.
 * @param {boolean} add - Indica si se deben agregar (true) o eliminar (false) los prefijos.
 * @returns {any[]} Arreglo de objetos con claves renombradas.
 */
export function renameKeys(objects: any[], prefixes:any[], add:boolean = false) {
  if (!add) {
    // Caso original: eliminar prefijos
    return objects.map(obj => {
      const newObj:any = {};
      Object.keys(obj).forEach(key => {
        const newKey = prefixes.reduce((acc, prefix) => key.startsWith(prefix) ? key.slice(prefix.length) : acc, key);
        newObj[newKey] = obj[key];
      });
      return newObj;
    });
  } else {
    // Caso nuevo: agregar prefijos y generar nuevos objetos
    let result:any[] = [];
    objects.forEach(obj => {
      prefixes.forEach(prefix => {
        const newObj:any = {};
        Object.keys(obj).forEach(key => {
          newObj[prefix + key] = obj[key];
        });
        result.push(newObj);
      });
    });
    return result;
  }
}

export function getIncoherencyOfItems(listActors: any[], minAcceptable: number = 90): any[] {
  let listItemsWithErrors:any[] = [];
  let listActorsSanitized = removeDuplicatesStrict(listActors);
  let keysListActors = Object.keys(listActorsSanitized[0]);

  for (let i = 0; i < listActorsSanitized.length; i++) {
    let item = listActorsSanitized[i];
    let countInvalid = 0;
    let countValid = 0;
    for (const actor of listActors) {
      if(JSON.stringify(item) === JSON.stringify(actor)) {
        countValid++;
      }else{
        let pCountValid = 0;
        keysListActors.forEach(key => {
          if(item[key] === actor[key]){
            pCountValid++;
          }
        });
        if(((pCountValid/keysListActors.length) * 100) >= minAcceptable ){
          listItemsWithErrors.push(actor);
          countInvalid ++;
        }
      }
    }

  }
  let listItemsWithErrors2 = removeDuplicatesStrict(listItemsWithErrors);
  return orderBy(listItemsWithErrors2.map(item => {
    item.repeated = listItemsWithErrors.filter(item2 => JSON.stringify(item) === JSON.stringify(item2)).length;
    return item;
  }), 'repeated', false);
}

export function replaceItems(items:any[], itemsReplace:any[], minAcceptable: number = 90){
  return items.map(item => {
    for (const itemReplace of itemsReplace) {
      let keysListActors = Object.keys(itemReplace);
      let pCountValid = 0;
      keysListActors.forEach(key => {
        if(item[key] === itemReplace[key]){
          pCountValid++;
        }
        if(((pCountValid/keysListActors.length) * 100) >= minAcceptable ){
          keysListActors.forEach(key => {
            item[key] = itemReplace[key];
          });
        }
      });
    }
    return item;
  })
}

export function compareObjectsMinAcceptable(item1: any, item2:any, numColumnAcceptableError:number = 0): boolean{
  let keys = Object.keys(Object.keys(item1).length > Object.keys(item2).length ? item2 : item1);
  keys.forEach((key:string) => {
    if(item1[key] !== item2[key]){
      numColumnAcceptableError--;
    }
  });

  return  numColumnAcceptableError >= 0;
}
/**
 * Extracts and returns the columns (keys) from an object or an array of objects, excluding specified columns.
 *
 * @param {object|any|any[]} data - The data source, which can be an object or an array of objects.
 * @param {string[]} columnsSplit - An array of column names to exclude from the result.
 * @return {string[]} An array of column names excluding the specified columnsSplit elements.
 */
export function getColumns(data: any | object | any[], columnsSplit: string[]): string[]{
  let columns:string[] = [];
  if (data){
    if (Array.isArray(data)) {
      columns = Object.keys(data[0]);
    } else if (typeof data === 'object') {
      columns = Object.keys(data);
    }
  }
  return columns.filter(column => !columnsSplit.includes(column));
}
export function generateEmployeeId(length: number = 10): string {
  var result = '';
  var characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  var charactersLength = characters.length;
  for ( var i = 0; i < length; i++ ) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength));
  }
  return result;
}

export function defaultValue<T>(value: T): T {
  if (Array.isArray(value)) return [] as unknown as T;
  if (value !== null && typeof value === 'object') return {} as unknown as T;
  return null as unknown as T;
}

export function replaceTemplateString(str: string, data: any) {
  return str.replace(/\{\{([^}]+)\}\}/g, (match: any, key: any) => {
    let keys = key.split('.');
    let value = data;

    for (let i = 0; i < keys.length; i++) {
      if (value[keys[i]] === undefined) {
        return match; // Retorna el texto original si la clave no existe
      }
      value = value[keys[i]];
    }

    return value;
  });
}

/**
 * Filters a list of objects based on a dynamic key (including nested properties) and a specific value.
 *
 * @param {any[]} items - The array of objects to filter.
 * @param {string} key - The dynamic key, which can represent nested properties separated by dots.
 * @param {any} value - The value to compare with the resolved property from the key.
 * @return {any[]} A filtered array of objects where the resolved key matches the specified value.
 */
export function filterByDynamicKey(items: any[], key: string, value: any): any[] {
  const keyParts = key.split('.'); // Divide la clave en partes para acceder a propiedades anidadas.

  return items.filter(item => {
    let currentItem = item;
    for (const part of keyParts) {
      if (currentItem[part] === undefined) {
        return false; // Si alguna parte de la clave no existe, excluye el elemento.
      }
      currentItem = currentItem[part]; // Accede a la siguiente parte de la clave.
    }
    return currentItem === value; // Compara el valor final encontrado con el valor buscado.
  });
}

/**
 * Retrieves the value from an object based on a given key, which can be deeply nested.
 *
 * @param {any} obj - The object from which the value will be retrieved.
 * @param {string|any} [key=null] - The key or path used to access the value. For nested paths, use dot notation if autoSeparate is true.
 * @param {boolean} [autoSeparate=true] - Determines whether the key should automatically be split by dots into nested parts.
 * @param {Function} [transformKey=(key: any) => key] - A function to transform the key at each level during traversal.
 * @return {any} - Returns the value found at the specified key or undefined if the key does not exist.
 */
export function getValueByKey(obj: any, key: string|any = null, autoSeparate: boolean = true, transformKey = (key: any)=>{
  return key
}): any {
  let result = obj;
  if(key){
    // Divide la clave en partes basándose en el punto.
    const keys = autoSeparate ? key.split('.') : [key];
    // Itera sobre las partes de la clave para acceder al valor deseado.
    for (let i = 0; i < keys.length; i++) {
      let column = transformKey(keys[i].trim())
      //console.log(column)
      if (result[column] === undefined) {
        // Si no se encuentra alguna clave, devuelve undefined o cualquier valor que consideres apropiado.
        return undefined;
      }
      result = result[column];
    }
  }

  return result;
}

export function filterListByKey(list: any[], key: string, autoSeparate: boolean = true, transformKey = (key: any)=>{
  return key
}): any[] {
  let response: any[] = []
  list.forEach((item: any) => {
    let rItem = filterByDynamicKey(list, key, getValueByKey(item, key, autoSeparate, transformKey))
    if(rItem) response = combineUnique(response, rItem)
  })
  return response;
}

export function inArray<T, K extends keyof T>(value: T | T[K], array: T[], key?: K): boolean {
  if (key !== undefined) {
    // Comparación basada en una clave específica del objeto
    return array.some(element => element[key] === value);
  } else {
    // Comparación de objetos por referencia
    return array.includes(value as T);
  }
}

export function implode<T>(separator: string, elements: T[]): string {
  return elements.map(String).join(separator);
}

/**
 * Splits a string into an array of substrings based on a specified separator.
 *
 * @param {string | string[]} separator - The separator used to split the text. It can be a single string or an array of strings.
 * @param {string} text - The text to be split.
 * @return {string[]} - An array containing the substrings split from the text.
 */
export function explode(separator: string | string[], text: string): string[] {
  if (typeof separator === 'string') {
    return text.split(separator);
  } else {
    const regex = new RegExp(separator.join('|'), 'g');
    return text.split(regex);
  }
}
/**
 * Converts a number to an array of consecutive numbers starting from 1.
 *
 * @param {number} [num=1] - The number to convert.
 * @param init
 * @returns {number[]} - An array of consecutive numbers.
 */
export function numberToArray(num: number = 1, init: number = 1): number[] {
  return Array.from({ length: num }, (_, i) => i + init);
}


type OptionsTransformArray = {
  key?: string | null;
  includes?: string[];
  excludes?: string[];
};
/**
 * Transforms an array of objects by selecting specific keys to include or exclude.
 *
 * @param {any[]} array - The array of objects to be transformed.
 * @param {OptionsTransformArray} [options={}] - The transformation options.
 * @param {string} [options.key=null] - The key of the object to include. If provided, only objects with this key will be included.
 * @param {string[]} [options.includes=[]] - The list of keys to include in the transformed objects.
 * @param {string[]} [options.excludes=[]] - The list of keys to exclude from the transformed objects.
 * @return {Array<Object>} - The transformed array of objects.
 */
export function transformArray(array: any[], options: OptionsTransformArray = {} as OptionsTransformArray): {key: any, value: any}[]|any[] {
  const { key = null, includes = [], excludes = [] } = options;
  return array.map(item => {
    const keys = key
      ? [key]
      : Object.keys(item)
        .filter(k => !includes.includes(k) && !excludes.includes(k));
    return keys.map(k => ({
      key: k,
      value: item[k],
      ...Object.fromEntries(includes.map(includeKey => [includeKey, item[includeKey]]))
    }));
  }).flat();
}

/**
 * Groups an array of objects by a specified property and returns the result as a matrix.
 * @param {Array} array - The array to be grouped.
 * @param {string} property - The property to group by.
 * @return {Array} - The grouped array as a matrix.
 */
export function groupByAsMatrix(array: any[], property: string): any[]{
  let gArray = groupBy(array, property)
  return Object.values(gArray);
}


/**
 * Segments a matrix based on a given key and length.
 *
 * @param {any[]} data - The input array of objects.
 * @param {string} key - The key to segment the matrix.
 * @param {number} length - The length of each segment.
 * @returns {any[][]} - The segmented matrix.
 */
export function segmentMatrix<T>(data: any[], key: string, length: number): T[][] {
  const result: any[][] = [];
  let tempArr: any[] = [];
  let count = length
  data.forEach((item) => {
    let items = deepCopy(item[key]);
    let tempItems = deepCopy(items); // Obtiene el resto de elementos

    while (tempItems.length > 0){
      if(count == 0) count = tempItems.length
      let tempSubObj = {
        ...item, // Copiamos los demás atributos del objeto principal
        [key]: []
      }
      tempSubObj[key] = (deepCopy(tempItems)).slice(0, count) ;
      tempArr.push(tempSubObj)
      tempItems = tempItems.slice(count)
      count = count-tempSubObj[key].length
      if(count <= 0){
        count = length
        result.push(tempArr)
        tempArr = []
      }
    }
  });
  return result as T[][];
}

export function segmentSimple<T>(data: any[], key: string, length: number|number[]): T[][] {
  const result: any[][] = [];
  let tempArr: any[] = [];
  length = (Array.isArray(length) ? length : [length])
  data.forEach((item, index) => {
    let count = length[index] ?? length[length.length - 1]
    let items = deepCopy(item[key]);
    let tempItems = deepCopy(items); // Obtiene el resto de elementos

    while (tempItems.length > 0){
      if(count == 0) count = tempItems.length
      let tempSubObj = {
        ...item, // Copiamos los demás atributos del objeto principal
        [key]: []
      }
      tempSubObj[key] = (deepCopy(tempItems)).slice(0, count) ;
      tempArr.push(tempSubObj)
      tempItems = tempItems.slice(count)
      count = count-tempSubObj[key].length
      count = length[index] ?? length[length.length - 1]
      result.push(tempArr)
      tempArr = []
    }
  });
  return result as T[][];
}

export function convertTime(segundos: number): string {
  const horas = Math.floor(segundos / 3600);
  const minutos = Math.floor((segundos % 3600) / 60);
  segundos = segundos % 60;

  return `${horas}h ${minutos}m ${segundos}s`;
}


export function dateFormat(value: any, format: 'long'|'short', language: 'es' | 'en', includeTime: boolean = false, timeZone: 'UTC' | 'America/Cancun'='America/Cancun' ): string {
  if (!value) {
    return '';
  }

  let date;

  // verifica si el valor de entrada es un número (timestamp)
  if (typeof value === 'number') {
    date = new Date(value * 1000); // convertir a milisegundos si es un timestamp en segundos
  } else {
    // Crear un objeto Date usando la cadena de fecha y hora en la zona horaria local del usuario
    date = new Date(value);
  }


  const options:any = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: includeTime ? 'numeric' : undefined,
    minute: includeTime ? 'numeric' : undefined,
    second: includeTime ? 'numeric' : undefined,
    timeZone: timeZone
  };

  if (format === 'long') {
    options.month = 'long';
  }

  if (language === 'es') {
    return date.toLocaleDateString('es-ES', options);
  } else {
    return date.toLocaleDateString('en-US', options);
  }
}


type Signe = '>' | '<' | '<=' | '>=' | '==';

export function validateDate(date: string, signe: Signe, condition: number): boolean {
  const now = new Date();
  const comparisonDate = new Date(date);

  const diffInDays = Math.abs(now.getTime() - comparisonDate.getTime()) / (1000 * 60 * 60 * 24); // difference in days

  const comparisons: Record<Signe, (a: number, b: number) => boolean> = {
    '>': (a, b) => a > b,
    '<': (a, b) => a < b,
    '>=': (a, b) => a >= b,
    '<=': (a, b) => a <= b,
    '==': (a, b) => a === b
  };

  return comparisons[signe](diffInDays, condition);
}


/**
 * Group items by a specified label key and exclude certain keys.
 *
 * @param {any[]} items - Array of items to be grouped.
 * @param {string} labelKey - The key to group items by (default is "key").
 * @param {string[]} exclude - Keys to be excluded from the grouping (default is []).
 *
 * @return {Array<{ label: string; items: { key: string, value: any }[] }>} - An array containing objects with label and grouped items.
 */
export function createGroupedByLabel(items: any[], labelKey="key", exclude: string[] = []): { label: string; items: { key: string, value: any }[]}[] {
  const keys = Object.keys(items[0]).filter(key => key !== labelKey)
    .filter(key => !exclude.includes(key));
  const groupedData = [];

  for (const item of items) {
    const itemLabel = item[labelKey];
    if (exclude.includes(itemLabel)) continue;

    const newItems = keys.map(key => ({
      key: key,
      value: item[key]
    }));

    groupedData.push({
      label: itemLabel,
      items: newItems
    });
  }

  return groupedData;
}


/**
 * Create a new array with unique values from the input array.
 *
 * @param {string[]} array - The input array that may contain duplicate values.
 * @return {string[]} - A new array with only unique values from the input array.
 */
export function uniqueSimpleArray(array: string[]): string[] {
  return Array.from(new Set(array));
}


/**
 * Returns the repeated elements from the provided array, sorted by their frequency in ascending or descending order.
 *
 * @param {string[]} arr - The array of strings to analyze for repeated elements.
 * @param {boolean} [ascending=true] - Determines the order of sorting by frequency.
 *                                      If true, sorts in ascending order, otherwise in descending order.
 * @return {string[]} An array of elements sorted by their count of occurrences.
 */
export function getRepeatedElements(arr: Array<string | undefined | null>, ascending: boolean = true): string[] {
  // Filter out invalid values (undefined, null, empty strings)
  const filteredArray = arr.filter((element): element is string => Boolean(element && element.trim()));

  // Create an object to count the occurrences of each valid element
  const count: Record<string, number> = {};

  filteredArray.forEach((element) => {
    count[element] = (count[element] || 0) + 1;
  });

  // Sort the elements based on the number of occurrences
  const sortedElements = Object.entries(count).sort((a, b) => {
    return ascending ? b[1] - a[1] : a[1] - b[1];
  });

  // Return the elements based on the chosen order
  return sortedElements.map(([element]) => element);
}




/**
 * Filters an array of objects to only include unique objects based on the specified key.
 *
 * @param {Array} array - The array of objects to filter.
 * @param {string} key - The key to use for checking uniqueness.
 *
 * @return {Array} - An array containing only the unique objects based on the specified key.
 */
export function uniqueObjectArray<T>(array: Array<any>, key: string): Array<T> {
  return array.filter((obj, index, self) =>
    index === self.findIndex((el) => (el[key] === obj[key]))
  ) as Array<T>;
}



/**
 * Removes specified columns from each object in the provided list.
 *
 * @param {Array<any>} list - The array of objects from which columns will be removed.
 * @param {Array<string>} columnsToRemove - The list of column keys to remove from each object in the array.
 * @return {Array<any>} A new array of objects with the specified columns removed.
 */
export function removeColumnsFromList(list: Array<any>, columnsToRemove: Array<string>): Array<any> {
  return list.map(item => {
    const newItem = { ...item }; // Crear una copia del objeto para evitar mutaciones
    columnsToRemove.forEach(column => {
      delete newItem[column]; // Eliminar las columnas especificadas
    });
    return newItem; // Retornar el nuevo objeto
  });
}


/**
 * Combines two arrays and returns a new array containing unique elements from both arrays.
 *
 * @param {Array<T>} array1 - The first array to combine.
 * @param {Array<T>} array2 - The second array to combine.
 * @return {Array<T>} A new array containing unique elements from the two input arrays.
 */
export function combineUnique<T>(array1: Array<T>, array2: Array<T>): Array<T> {
  return Array.from(new Set([...array1, ...array2]));
}




/**
 * Calculates the number of unique values across the specified keys from an array of objects.
 *
 * @param {any[]} items - An array of objects to process.
 * @param {string[]} keys - An array of keys whose unique values need to be counted.
 * @return {number} The count of unique values across the specified keys. Returns 0 if the inputs are invalid or there are no keys to process.
 */
export function calculateUniqueKeyValuesCount(items: any[], keys: string[]): number {
  if (!Array.isArray(items) || !Array.isArray(keys) || keys.length === 0) {
    return 0; // Devuelve 0 si no hay datos a procesar
  }

  // Extrae todos los valores de las claves y elimina duplicados en un solo paso
  const uniqueValues = new Set(
    keys.flatMap(key => (items || []).map(item => item[key])) // Obtener valores de las claves
  );

  return uniqueValues.size; // Devuelve el número de valores únicos
}

/**
 * Merges two objects deeply, combining properties from both the target and source objects.
 * If both the target and source contain a nested object or array in the same key*/
export function deepMerge(target: any, source: any): any {
  const output = { ...target };
  if (isObject(target) && isObject(source)) {
    Object.keys(source).forEach(key => {
      if (isObject(source[key])) {
        if (!(key in target)) Object.assign(output, { [key]: source[key] });
        else output[key] = deepMerge(target[key], source[key]);
      } else if (Array.isArray(source[key])) {
        output[key] = [...(target[key] || []), ...source[key]];
      } else {
        Object.assign(output, { [key]: source[key] });
      }
    });
  }
  return output;
}

/**
 * Determines whether the provided parameter is an object.
 *
 * @param {any} item - The value to be checked.
 * @return {boolean} Returns true if the input is an object and not an array; otherwise, false.
 */
export function isObject(item: any): boolean {
  return item && typeof item === 'object' && !Array.isArray(item);
}

export function validateAndAddOrder(arr: any[], key:string = 'order'): any[] {
  arr.forEach((item, index) => {
    if (item[key] === undefined || item[key] === null) {
      item[key] = index + 1; // Asigna el índice como valor de 'order'
    }
  });
  return arr
}



export type StatusChecker<T> = (item: T) => boolean;

export interface CompletionCount {
  completed: number;
  inCompleted: number;
  total: number;
}


/**
 * Counts the completion status of grouped items based on a provided key and a status checker function.
 *
 * @param {T[]} items - The array of items to be grouped and checked for completion status.
 * @param {keyof T | any} groupKey - The key used to group the items.
 * @param {StatusChecker<T>} statusChecker - A callback function that checks if an item meets the completion criteria.
 *
 * @return {CompletionCount} An object containing the counts of completed, incomplete, and total groups.
 */
export function countCompletionStatus<T>(
  items: T[],
  groupKey: keyof T | any,
  statusChecker: StatusChecker<T>
): CompletionCount {
  // Agrupar los elementos por la clave proporcionada
  const groupedItems = groupBy(items, groupKey);
  let completed = 0;
  let inCompleted = 0;
  let total = 0;

  // Iterar sobre cada grupo y verificar el estado
  for (const group of Object.values(groupedItems)) {
    // Verificar que 'group' es un arreglo antes de proceder
    if (Array.isArray(group)) {
      total++;
      const isCompleted = group.every(statusChecker);
      if (isCompleted) {
        completed++;
      } else {
        inCompleted++;
      }
    }
  }

  // Retornar siempre un objeto de tipo CompletionCount
  return { completed, inCompleted, total };
}

export function isNumberOrText(value: any): { isNumber: boolean; isText: boolean } {
  if (typeof value === 'number' || !isNaN(Number(value))) {
    return { isNumber: true, isText: false };
  } else if (typeof value === 'string') {
    return { isNumber: false, isText: true };
  }
  return { isNumber: false, isText: false }; // If it's neither a number nor text
}

export function limitArray(data: any[], limit: number, takeFirst: boolean = true): any[] {
  if (!data || data.length === 0) return [];

  if (takeFirst) {
    return data.slice(0, limit);
  } else {
    return data.slice(-limit);
  }
}


