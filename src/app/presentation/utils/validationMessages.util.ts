import { Injectable } from '@angular/core';
import { AbstractControl, ValidationErrors } from '@angular/forms';
import { TranslateService } from '@ngx-translate/core';
import {ValidationMessageOptions} from '@/app/presentation/utils/types/validationMessages.type';


@Injectable({ providedIn: 'root' })
export class ValidationMessagesUtil {
  constructor(private readonly translate: TranslateService) {}

  getMessages(
    control: AbstractControl | null | undefined,
    opts: ValidationMessageOptions = {},
    fieldName?: string
  ): string[] {
    if (!control) return [];

    const mode = opts.mode ?? 'touchedOrDirty';
    const keyPrefix = opts.keyPrefix ?? 'validation';

    const shouldShow =
      mode === 'always'
        ? true
        : mode === 'submitted'
          ? !!opts.submitted
          : control.touched || control.dirty;

    if (!shouldShow) return [];

    const errors = control.errors;
    if (!errors) return [];

    const errorKeys = this.getOrderedErrorKeys(errors, opts.errorPriority);

    return errorKeys.map((errorKey) => {
      const i18nKey = this.resolveKey(errorKey, opts, fieldName, keyPrefix);
      const params = this.buildParams(errors, errorKey, opts.fieldLabel);
      return this.translate.instant(i18nKey, params);
    });
  }

  getFirstMessage(
    control: AbstractControl | null | undefined,
    opts: ValidationMessageOptions = {},
    fieldName?: string
  ): string | null {
    const msgs = this.getMessages(control, opts, fieldName);
    return msgs.length ? msgs[0] : null;
  }

  private resolveKey(
    errorKey: string,
    opts: ValidationMessageOptions,
    fieldName: string | undefined,
    keyPrefix: string
  ): string {
    if (fieldName && opts.fieldErrorKeys?.[fieldName]?.[errorKey]) {
      return opts.fieldErrorKeys[fieldName][errorKey];
    }
    return `${keyPrefix}.${errorKey}`;
  }

  private buildParams(errors: ValidationErrors, errorKey: string, fieldLabel?: string): Record<string, unknown> {
    const base: Record<string, unknown> = {};
    if (fieldLabel) base['field'] = fieldLabel;

    const errVal = errors[errorKey];

    // Angular a veces pone boolean, a veces objetos con datos
    if (errVal && typeof errVal === 'object') {
      // Copia segura de propiedades típicas: requiredLength, actualLength, min, max, requiredPattern, actualValue, etc.
      Object.assign(base, errVal as Record<string, unknown>);
    }

    return base;
  }

  private getOrderedErrorKeys(errors: ValidationErrors, priority?: string[]): string[] {
    const keys = Object.keys(errors);

    if (!priority || !priority.length) return keys;

    const set = new Set(keys);
    const ordered = priority.filter((k) => set.has(k));
    const rest = keys.filter((k) => !priority.includes(k));
    return [...ordered, ...rest];
  }
}

