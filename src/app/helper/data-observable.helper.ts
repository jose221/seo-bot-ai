import { signal, computed, effect, Signal, WritableSignal } from '@angular/core';
import { isObservable, Observable } from 'rxjs';
import { isArray } from "chart.js/helpers";


export type TypeCallbackDataHelper = {
  previousValue: any;
  currentValue: any;
  firstChange: boolean;
};

/**
 * A helper class for managing data with Angular Signals.
 *
 * @template T The type of data items.
 */
export class DataSignalHelper<T> {
  private itemsSignal: WritableSignal<T> = signal([] as T);
  private beforeData: any[] | any = null;
  private firstChange: boolean = true;

  // Signal público de solo lectura
  items: Signal<T> = this.itemsSignal.asReadonly();

  /**
   * Sets the next value of the items signal with the provided data.
   *
   * @param {T} items - The items to set as the next value of the items signal.
   *
   * @return {void}
   */
  next(items: T): void {
    this.itemsSignal.set(items);
  }

  /**
   * Updates the signal value using an updater function.
   *
   * @param {(value: T) => T} updaterFn - Function that receives current value and returns new value.
   *
   * @return {void}
   */
  update(updaterFn: (value: T) => T): void {
    this.itemsSignal.update(updaterFn);
  }

  /**
   * Pushes a new item to the array (assumes T is an array type).
   *
   * @param {any} item - The item to push to the array.
   *
   * @return {void}
   */
  push(item: any): void {
    setTimeout(() => {
      const currentValue = this.itemsSignal();

      if (!isArray(currentValue)) {
        this.itemsSignal.set([item] as T);
      } else {
        this.itemsSignal.set([...currentValue, item] as T);
      }
    }, 500);
  }

  /**
   * Returns the current signal value.
   *
   * @return {T} - The current value.
   */
  get data(): T {
    return this.itemsSignal();
  }

  /**
   * Returns the signal itself for reactive access.
   *
   * @return {Signal<T>} - The signal.
   */
  get dataSignal(): Signal<T> {
    return this.items;
  }

  /**
   * Process the input data and execute callback with change information.
   *
   * @param {any} input - The input data to be processed. Can be Observable or plain data.
   * @param {Function} [callback] - Optional callback function to be called after processing the input data.
   * @returns {void}
   */
  processData(input: any, callback?: (data: TypeCallbackDataHelper) => void): void {
    if (isObservable(input)) {
      input.subscribe((data: any) => {
        this.handleDataChange(data, callback);
      });
    } else {
      this.handleDataChange(input, callback);
    }
  }

  /**
   * Private method to handle data changes and trigger callbacks.
   */
  private handleDataChange(data: any, callback?: (data: TypeCallbackDataHelper) => void): void {
    if (callback) {
      callback({
        currentValue: data,
        previousValue: this.beforeData,
        firstChange: this.firstChange
      } as TypeCallbackDataHelper);
    }
    this.beforeData = data;
    if (this.firstChange) {
      this.firstChange = false;
    }
  }

  /**
   * Creates an effect that runs whenever the signal changes.
   *
   * @param {(value: T) => void} callback - Function to execute on signal changes.
   * @returns {void}
   */
  onChange(callback: (value: T) => void): void {
    effect(() => {
      const value = this.itemsSignal();
      callback(value);
    });
  }

  /**
   * Normalize data to an array format.
   *
   * @param {any} data - The data to be normalized.
   * @return {any[]} - The normalized data in array format.
   */
  normalizeDataToArray(data: any): any[] {
    if (Array.isArray(data)) {
      return data;
    } else if (data && typeof data === 'object') {
      return [data];
    } else {
      return [];
    }
  }

  /**
   * Custom implementation of setInterval with a condition and option to specify number of attempts.
   *
   * @param {Function} callback - The function to be executed at each interval.
   * @param {number} delay - The interval in milliseconds.
   * @param {() => boolean} conditionFunc - A function that returns a boolean indicating whether to stop the interval.
   * @param {number} [attempts=0] - The maximum number of attempts before stopping the interval.
   *
   * @return {void}
   */
  customSetInterval(callback: Function, delay: number, conditionFunc: () => boolean, attempts: number = 0): void {
    let counter = 0;

    const intervalId = setInterval(() => {
      if (conditionFunc() || (attempts > 0 && counter >= attempts)) {
        clearInterval(intervalId);

        if (conditionFunc()) {
          callback();
        }
      }
      counter += 1;
    }, delay);
  }

  private isObject(value: any): boolean {
    return value && typeof value === 'object' && value.constructor === Object;
  }

  private isNonEmpty(value: any): boolean {
    return value !== null && value !== undefined && value !== '';
  }

  /**
   * Validates if data is valid and non-empty.
   *
   * @param {Observable<T>|T|any|any[]} data - The data to validate.
   * @param {T} [defaultValue] - Optional default value to compare against.
   * @return {boolean} - True if data is valid.
   */
  isValidData(data: Observable<T> | T | any | any[], defaultValue?: T): boolean {
    let validData = false;

    if (this.isNonEmpty(data)) {
      if (isObservable(data)) {
        validData = true;
      } else if (Array.isArray(data)) {
        if (data.length > 0) validData = true;
      } else if (this.isObject(data)) {
        if (Object.keys(data).length > 0) {
          validData = true;
        }
      } else if (data && data !== defaultValue) {
        validData = true;
      }
    }
    return validData;
  }
}

/**
 * Legacy class for backward compatibility - uses Observables.
 * Consider migrating to DataSignalHelper for better performance.
 *
 * @deprecated Use DataSignalHelper instead
 * @template T The type of data items.
 */
export class DataObservableHelper<T> extends DataSignalHelper<T> {
  // This class now extends DataSignalHelper for compatibility
  // You can gradually migrate to DataSignalHelper
}
