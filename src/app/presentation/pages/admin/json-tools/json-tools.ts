import { Component, computed, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { NgClass } from '@angular/common';
import { encode } from '@toon-format/toon';

type OptimizationMode = 'minified' | 'toon';
type OutputScope = 'sample' | 'all';

@Component({
  selector: 'app-json-tools',
  imports: [ReactiveFormsModule, NgClass],
  templateUrl: './json-tools.html',
  styleUrl: './json-tools.scss',
})
export class JsonTools {
  private readonly fb = inject(FormBuilder);

  protected readonly form = this.fb.group({
    input: ['', Validators.required],
    optimization: ['toon' as OptimizationMode, Validators.required],
    scope: ['sample' as OutputScope, Validators.required],
  });

  protected readonly submitted = signal(false);
  protected readonly parseError = signal('');
  protected readonly output = signal('');
  protected readonly inputLength = signal(0);
  protected readonly outputLength = computed(() => this.output().length);
  protected readonly sizeDelta = computed(() => {
    const input = this.inputLength();
    const output = this.outputLength();

    if (input <= 0 || output <= 0) return null;

    const diff = input - output;
    const isReduction = diff >= 0;
    const percent = Math.abs((diff / input) * 100);

    return {
      diff: Math.abs(diff),
      isReduction,
      percent: Number(percent.toFixed(2)),
    };
  });

  constructor() {
    this.form.get('input')?.valueChanges.subscribe((value) => {
      this.inputLength.set((value ?? '').length);
    });
  }

  transform(): void {
    this.submitted.set(true);
    this.parseError.set('');
    this.output.set('');

    if (this.form.invalid) return;

    const source = (this.form.get('input')?.value ?? '').trim();

    try {
      const parsed = JSON.parse(source);
      const scope = this.form.get('scope')?.value as OutputScope;
      const optimization = this.form.get('optimization')?.value as OptimizationMode;
      const dataToTransform = scope === 'sample' ? this.createRecursiveSample(parsed) : parsed;
      const transformed = optimization === 'minified'
        ? JSON.stringify(dataToTransform)
        : encode(dataToTransform, { keyFolding: 'safe', delimiter: ',' });

      this.output.set(transformed);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'JSON inválido.';
      this.parseError.set(`No se pudo procesar el JSON: ${message}`);
    }
  }

  formatInput(): void {
    const source = (this.form.get('input')?.value ?? '').trim();
    if (!source) return;

    try {
      const parsed = JSON.parse(source);
      this.form.patchValue({ input: JSON.stringify(parsed, null, 2) });
      this.parseError.set('');
    } catch {
      this.parseError.set('No se puede formatear porque el JSON es inválido.');
    }
  }

  private createRecursiveSample(value: unknown): unknown {
    if (Array.isArray(value)) {
      if (value.length === 0) return [];
      return [this.createRecursiveSample(value[0])];
    }

    if (value && typeof value === 'object') {
      const entries = Object.entries(value as Record<string, unknown>)
        .map(([key, nestedValue]) => [key, this.createRecursiveSample(nestedValue)]);
      return Object.fromEntries(entries);
    }

    return value;
  }
}
