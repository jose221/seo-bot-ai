
interface MapOptions {
  except?: string[];
  include?: string[] | Record<string, any>;
  /**
   * Renombra propiedades al mapear.
   * { 'sourceKey': 'targetKey' }
   * Ejemplo: { 'email': 'userEmail' }
   */
  replace?: Record<string, string|any>;
}

/**
 * Utility class for mapping objects.
 */
export abstract class AppMapper {



  /**
   * Copies specified properties from the given object to a new object of type T.
   *
   * @typeparam T - The type of the resulting object.
   * @param param - The object to copy properties from.
   * @param options - The options for copying properties.
   *   - exclude: An array of property names to exclude from the copy.
   *   - include: An array of property names to include in the copy. If not specified, all properties will be included.
   * @returns A new object of type T with the copied properties.
   */
  pipeFrom<T>(param: any, options?: { exclude?: string[], include?: string[] }): T {
    if (!param) return param;

    const result: Partial<T> = {} as T;
    const keys = options?.include || Object.keys(param);
    keys.forEach(key => {
      if (!options?.exclude || !options.exclude.includes(key)) {
        result[key as keyof T] = param[key];
      }
    });
    return result as T;
  }
  /**
   * Copies the properties from a source object to a new object, optionally excluding or including specific properties.
   *
   * @template T - The type of the source object.
   * @param {T} param - The source object to copy properties from.
   * @param {Object} [options] - Optional configuration options.
   * @param {string[]} [options.exclude] - An array of property names to exclude from the copied object.
   * @param {string[]} [options.include] - An array of property names to include in the copied object.
   * @returns {T} - A new object with the copied properties.
   */
  pipeTo<T>(param: T, options?: { exclude?: string[], include?: string[] }): T {
    if (!param) return param;

    const result: any = {};
    const keys = options?.include || Object.keys(param);
    keys.forEach(key => {
      if (!options?.exclude || !options.exclude.includes(key)) {
        result[key] = (param as any)[key];
      }
    });

    return result as T;
  }

  /**
   * Copies specified properties from one object to another and returns the new object.
   *
   * @template T - The type of the source object.
   * @template U - The type of the destination object.
   *
   * @param {T} from - The source object from which properties will be copied.
   * @param {new () => U} to - The constructor of the destination object.
   * @param {MapOptions} [options] - The options for property mapping.
   *
   * @returns {U} - The new object with copied properties.
   */
  pipeData<T, U>(from: T, to: new () => U, options?: MapOptions): U {
    const toInstance = new to();
    const fromProps = from ? Object.keys(from) : [];

    // Determinar las propiedades a incluir: todas si no se especifica "include"
    const includeProps = options?.include || fromProps;

    // Crear un conjunto de propiedades a excluir para facilitar la comprobación
    const exceptProps = new Set(options?.except || []);

    includeProps.forEach((prop: any) => {
      if (fromProps.includes(prop) && !exceptProps.has(prop)) {
        // @ts-ignore: Ignorar el error de TypeScript para permitir asignación dinámica
        toInstance[prop] = from[prop];
      }
    });

    return toInstance;
  }

  /**
   * Maps a model from one type to another using the specified options.
   *
   * @template T The type of the source model.
   * @template U The type of the target model.
   * @param {T} from The source model to be mapped.
   * @param {new () => U} to A constructor function to create a new instance of the target model.
   * @param {MapOptions} [options] The map options to be used during the mapping process.
   * @returns {U} The mapped target model.
   */
  mapModel<T, U>(from: T, to: new () => U, options?: MapOptions): U {
    return this.pipeData(from, to, options);
  }

  /**
   * Maps an entity from one type to another using the specified options.
   *
   * @template T - The type of the source entity.
   * @template U - The type of the target entity.
   * @param {T} from - The source entity to be mapped.
   * @param {new () => U} to - The constructor function of the target entity.
   * @param {MapOptions} [options] - The options to be used during the mapping process.
   * @return {U} - The mapped target entity.
   */
  mapEntity<T, U>(from: T, to: new () => U, options?: MapOptions): U {
    return this.pipeData(from, to, options);
  }
  /**
   * Mapea automáticamente copiando propiedades enumerables de `from`,
   * con soporte para:
   * - `except`: excluir propiedades
   * - `include`:
   *     - Si es array: whitelist (solo incluye esas propiedades de `from`)
   *     - Si es objeto: inyecta esas propiedades con sus valores en el resultado
   * - `replace`: renombrar propiedades { 'sourceKey': 'targetKey' }
   *
   * Útil cuando DTO y Domain comparten nombres de propiedades.
   */
  autoMap<TFrom extends Record<string, any>, TTo>(
    from: TFrom,
    options?: MapOptions
  ): TTo {
    if (!from) return from as unknown as TTo;

    const except = new Set(options?.except ?? []);
    const replace = options?.replace ?? {};
    const result: Record<string, any> = {};

    // Determinar si include es whitelist (array) o inyección (objeto)
    const includeIsArray = Array.isArray(options?.include);
    const includeWhitelist = includeIsArray ? new Set(options!.include as string[]) : null;
    const includeInjection = !includeIsArray && options?.include ? (options.include as Record<string, any>) : null;

    // 1) Copiar propiedades de `from`
    const keysToProcess = includeWhitelist ? Array.from(includeWhitelist) : Object.keys(from);

    for (const sourceKey of keysToProcess) {
      // Saltar si está en except
      if (except.has(sourceKey)) continue;

      // Saltar si está en whitelist y no existe en from
      if (includeWhitelist && !(sourceKey in from)) continue;

      // Determinar el nombre de destino (target)
      const targetKey = replace[sourceKey] ?? sourceKey;

      result[targetKey] = from[sourceKey];
    }

    // 2) Inyectar propiedades adicionales si include es objeto
    if (includeInjection) {
      Object.assign(result, includeInjection);
    }

    return result as TTo;
  }
}
