import { Component, inject, signal } from '@angular/core';
import { FormArray, FormBuilder, FormControl, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { StructuredValidationRepository } from '@/app/domain/repositories/structured-validation/structured-validation.repository';
import { requiredTrimmed } from '@/app/presentation/utils/form-validators.util';
import { StructuredValidationCreateRequestModel } from '@/app/domain/models/structured-validation/request/structured-validation-request.model';

@Component({
  selector: 'app-structured-validation-form',
  standalone: true,
  imports: [ReactiveFormsModule, FormsModule, RouterLink],
  templateUrl: './structured-validation-form.html',
  styleUrl: './structured-validation-form.scss',
})
export class StructuredValidationForm {
  private readonly fb = inject(FormBuilder);
  private readonly repository = inject(StructuredValidationRepository);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly submitted = signal(false);
  readonly error = signal('');

  readonly form = this.fb.group({
    input_mode: ['url' as 'url' | 'html', Validators.required],
    name: ['Validacion estructurada', [Validators.maxLength(160)]],
    description: ['', [Validators.maxLength(500)]],
    ai_instruction: ['', [Validators.maxLength(1200)]],
    raw_urls: [''],
    html_items: this.fb.array([this.fb.control('', [requiredTrimmed()])]),
    get_ai_result: [true],
    auto_extract_html: [false],
    validate_google: [true],
    validate_schema_org: [true],
  });

  constructor() {
    this.form.get('input_mode')?.valueChanges.subscribe(() => this.onModeChange());
    const rerunData = history.state?.rerunData as Partial<StructuredValidationCreateRequestModel> | undefined;
    if (rerunData) {
      this.form.patchValue({
        input_mode: rerunData.input_mode ?? 'url',
        name: rerunData.name ?? 'Validacion estructurada',
        description: rerunData.description ?? '',
        ai_instruction: rerunData.ai_instruction ?? '',
        raw_urls: rerunData.raw_urls ?? '',
        get_ai_result: rerunData.get_ai_result ?? true,
        auto_extract_html: rerunData.auto_extract_html ?? false,
        validate_google: rerunData.validate_google ?? true,
        validate_schema_org: rerunData.validate_schema_org ?? true,
      });
      this.htmlItems.clear();
      (rerunData.html_items ?? ['']).forEach((item) => this.htmlItems.push(this.fb.control(item, [requiredTrimmed()])));
      if (this.htmlItems.length === 0) this.addHtmlItem();
    }
    this.onModeChange();
  }

  get htmlItems(): FormArray<FormControl<string | null>> {
    return this.form.get('html_items') as FormArray<FormControl<string | null>>;
  }

  addHtmlItem(): void {
    this.htmlItems.push(this.fb.control('', [requiredTrimmed()]));
  }

  removeHtmlItem(index: number): void {
    if (this.htmlItems.length <= 1) return;
    this.htmlItems.removeAt(index);
  }

  onModeChange(): void {
    const inputMode = this.form.get('input_mode')?.value ?? 'url';
    if (inputMode === 'url') {
      this.form.patchValue({ auto_extract_html: this.form.get('auto_extract_html')?.value ?? false }, { emitEvent: false });
      for (const control of this.htmlItems.controls) {
        control.clearValidators();
        control.updateValueAndValidity({ emitEvent: false });
      }
      return;
    }

    this.form.patchValue({ auto_extract_html: false }, { emitEvent: false });
    if (this.htmlItems.length === 0) this.addHtmlItem();
    for (const control of this.htmlItems.controls) {
      control.setValidators([requiredTrimmed()]);
      control.updateValueAndValidity({ emitEvent: false });
    }
  }

  countUrls(): number {
    const raw = `${this.form.get('raw_urls')?.value ?? ''}`.trim();
    if (!raw) return 0;
    return Array.from(new Set(raw.split(/[\s,]+/).map((item) => item.trim()).filter(Boolean))).length;
  }

  async submit(): Promise<void> {
    this.submitted.set(true);
    this.error.set('');
    const inputMode = this.form.get('input_mode')?.value ?? 'url';
    const rawUrls = (this.form.get('raw_urls')?.value ?? '').trim();
    const htmlItems = this.htmlItems.controls.map((control) => `${control.value ?? ''}`.trim()).filter(Boolean);
    if (inputMode === 'url' && !rawUrls) {
      this.error.set('Debes capturar al menos una URL.');
      return;
    }
    if (inputMode === 'html' && !htmlItems.length) {
      this.error.set('Debes capturar al menos un bloque HTML.');
      return;
    }
    if (!this.form.get('validate_google')?.value && !this.form.get('validate_schema_org')?.value) {
      this.error.set('Activa al menos un validador.');
      return;
    }
    if (this.form.invalid) return;

    this.loading.set(true);
    try {
      const response = await this.repository.create(
        new StructuredValidationCreateRequestModel(
          inputMode,
          `${this.form.get('name')?.value ?? ''}`.trim() || 'Validacion estructurada',
          `${this.form.get('description')?.value ?? ''}`.trim() || null,
          `${this.form.get('ai_instruction')?.value ?? ''}`.trim() || null,
          inputMode === 'url' ? rawUrls : null,
          inputMode === 'html' ? htmlItems : [],
          !!this.form.get('get_ai_result')?.value,
          !!this.form.get('auto_extract_html')?.value,
          !!this.form.get('validate_google')?.value,
          !!this.form.get('validate_schema_org')?.value,
        ),
      );
      await this.router.navigate(['/admin/audit/structured-validations', response.task_id, 'info']);
    } catch (error: any) {
      this.error.set(error?.response?.data?.detail || 'No se pudo crear la tarea.');
    } finally {
      this.loading.set(false);
    }
  }
}
