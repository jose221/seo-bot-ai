import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

function toTrimmedString(value: unknown): string {
  return typeof value === 'string' ? value.trim() : '';
}

export function requiredTrimmed(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    return toTrimmedString(control.value) ? null : { required: true };
  };
}

export function httpsUrl(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = toTrimmedString(control.value);
    if (!value) return null;

    try {
      const url = new URL(value);
      return ['http:', 'https:'].includes(url.protocol) ? null : { url: true };
    } catch {
      return { url: true };
    }
  };
}

export function jsonSyntax(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const value = toTrimmedString(control.value);
    if (!value) return null;

    try {
      JSON.parse(value);
      return null;
    } catch {
      return { invalidJson: true };
    }
  };
}

export function urlList(options: { maxUrls?: number } = {}): ValidatorFn {
  const { maxUrls = 200 } = options;

  return (control: AbstractControl): ValidationErrors | null => {
    const value = toTrimmedString(control.value);
    if (!value) return null;

    const urls = value
      .split('\n')
      .map((item) => item.trim())
      .filter(Boolean);

    if (!urls.length) return { required: true };

    const invalidUrls = urls.filter((item) => {
      try {
        const parsed = new URL(item);
        return !['http:', 'https:'].includes(parsed.protocol);
      } catch {
        return true;
      }
    });

    const duplicateUrls = urls.filter((item, index) => urls.indexOf(item) !== index);
    const duplicateUnique = [...new Set(duplicateUrls)];

    if (urls.length > maxUrls) {
      return {
        maxUrls: {
          actual: urls.length,
          max: maxUrls,
        },
      };
    }

    if (invalidUrls.length) {
      return {
        invalidUrls: {
          count: invalidUrls.length,
          sample: invalidUrls.slice(0, 3).join(', '),
        },
      };
    }

    if (duplicateUnique.length) {
      return {
        duplicateUrls: {
          count: duplicateUnique.length,
          sample: duplicateUnique.slice(0, 3).join(', '),
        },
      };
    }

    return null;
  };
}
