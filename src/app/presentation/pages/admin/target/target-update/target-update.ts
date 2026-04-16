import {Component, inject, OnInit, signal} from '@angular/core';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {UpdateTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {NgClass} from '@angular/common';
import {TranslatePipe} from '@ngx-translate/core';
import {ActivatedRoute, RouterLink} from '@angular/router';

@Component({
  selector: 'app-target-update',
  imports: [
    ReactiveFormsModule,
    NgClass,
    TranslatePipe,
    RouterLink
  ],
  templateUrl: './target-update.html',
  styleUrl: './target-update.scss',
})
export class TargetUpdate extends ValidationFormBase implements OnInit {
  protected readonly form = inject(FormBuilder).group({
    name: ['', Validators.required],
    instructions: ['', [Validators.required]],
    tech_stack: ['', Validators.required],
    is_active: [true],
    manual_html_content: [''],
    provider: [''],
  });
  private readonly formRepository = inject(TargetRepository);
  private readonly route = inject(ActivatedRoute);

  targetId = signal<string | null>(null);
  pageLoading = signal<boolean>(true);

  // Tags management
  tags = signal<string[]>([]);
  availableTags = signal<string[]>([]);
  filteredTags = signal<string[]>([]);
  tagInput = signal<string>('');
  showTagDropdown = signal<boolean>(false);

  constructor() {
    super();
  }

  async ngOnInit(): Promise<void> {
    const id = this.route.snapshot.paramMap.get('id');
    if (!id) {
      await this.router.navigateByUrl('/admin/target');
      return;
    }
    this.targetId.set(id);

    try {
      const [target, tags] = await Promise.all([
        this.formRepository.find(id),
        this.formRepository.getTags(),
      ]);
      this.availableTags.set(tags);
      this.form.patchValue({
        name: target.name,
        instructions: target.instructions,
        tech_stack: target.tech_stack,
        is_active: target.is_active,
        manual_html_content: target.manual_html_content ?? '',
        provider: target.provider ?? '',
      });
      if (target.tags?.length) {
        this.tags.set(target.tags);
      }
    } catch (e: any) {
      this.error.set(`No se pudo cargar el target: ${e?.message ?? 'Error desconocido'}`);
    } finally {
      this.pageLoading.set(false);
    }
  }

  messages(name: string) {
    return this.formMessages(name);
  }

  onTagInputChange(value: string): void {
    this.tagInput.set(value);
    if (value.trim()) {
      const lower = value.toLowerCase();
      const filtered = this.availableTags().filter(t =>
        t.toLowerCase().includes(lower) && !this.tags().includes(t)
      );
      this.filteredTags.set(filtered);
      this.showTagDropdown.set(filtered.length > 0);
    } else {
      const filtered = this.availableTags().filter(t => !this.tags().includes(t));
      this.filteredTags.set(filtered);
      this.showTagDropdown.set(filtered.length > 0);
    }
  }

  onTagInputFocus(): void {
    const filtered = this.availableTags().filter(t => !this.tags().includes(t));
    this.filteredTags.set(filtered);
    this.showTagDropdown.set(filtered.length > 0);
  }

  selectTag(tag: string): void {
    if (!this.tags().includes(tag)) {
      this.tags.update(t => [...t, tag]);
    }
    this.tagInput.set('');
    this.showTagDropdown.set(false);
  }

  addTagFromInput(): void {
    const val = this.tagInput().trim();
    if (val && !this.tags().includes(val)) {
      this.tags.update(t => [...t, val]);
    }
    this.tagInput.set('');
    this.showTagDropdown.set(false);
  }

  removeTag(tag: string): void {
    this.tags.update(t => t.filter(x => x !== tag));
  }

  onTagKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      this.addTagFromInput();
    }
  }

  async onSubmit() {
    this.submitted.set(true);
    if (this.form.invalid) return;
    await this.save();
  }

  async save() {
    const id = this.targetId();
    if (!id) return;
    this.error.set('');
    this.loading.set(true);
    try {
      const formValue = this.form.value as any;
      const payload: UpdateTargetRequestModel = {
        name: formValue.name,
        instructions: formValue.instructions,
        tech_stack: formValue.tech_stack,
        is_active: formValue.is_active,
        manual_html_content: formValue.manual_html_content || undefined,
        tags: this.tags().length > 0 ? this.tags() : undefined,
        provider: formValue.provider || undefined,
      };
      await this.formRepository.update(id, payload);
      await this._sweetAlertUtil.success('Éxito', 'Target actualizado correctamente');
      await this.router.navigateByUrl('/admin/target');
    } catch (e: Error | any) {
      console.log('Error updating target:', e);
      this.error.set(`${e?.response?.statusText ?? e.name} ${e.response?.data?.detail ?? e.message} (${e?.response?.status ?? e?.code})`);
    } finally {
      this.loading.set(false);
    }
  }
}

