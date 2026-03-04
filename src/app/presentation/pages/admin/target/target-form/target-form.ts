import {Component, inject, OnInit, signal} from '@angular/core';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {CreateTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';
import {NgClass} from '@angular/common';
import {TranslatePipe} from '@ngx-translate/core';
import {RouterLink} from '@angular/router';

@Component({
  selector: 'app-target-form',
  imports: [
    ReactiveFormsModule,
    NgClass,
    TranslatePipe,
    RouterLink
  ],
  templateUrl: './target-form.html',
  styleUrl: './target-form.scss',
})
export class TargetForm extends ValidationFormBase implements OnInit {
  protected readonly form = inject(FormBuilder).group({
    instructions: ['', [Validators.required]],
    name: ['', Validators.required],
    tech_stack: ['', Validators.required],
    url: ['', Validators.required, Validators.pattern('https?://.+')],
    manual_html_content: [''],
    provider: [''],
  });
  private readonly formRepository = inject(TargetRepository);

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
    try {
      const tags = await this.formRepository.getTags();
      this.availableTags.set(tags);
    } catch {
      this.availableTags.set([]);
    }
  }

  messages(name: string){
    return this.formMessages(name)
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
    await this.create();
  }

  async create(){
    this.error.set('');
    this.loading.set(true);
    try {
      const formValue = this.form.value as any;
      const payload: CreateTargetRequestModel = {
        ...formValue,
        tags: this.tags().length > 0 ? this.tags() : undefined,
        provider: formValue.provider || undefined,
      };
      await this.formRepository.create(payload);
      await this.router.navigateByUrl('/admin/target');
    } catch (e: Error | any) {
      console.log('Error logging in:', e);
      this.error.set( `${e?.response?.statusText ?? e.name} ${e.response?.data?.detail ?? e.message} (${e?.response?.status ?? e?.code}) `);
    } finally {
      this.loading.set(false);
    }
  }
}
