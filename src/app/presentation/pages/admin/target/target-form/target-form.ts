import {Component, inject} from '@angular/core';
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
export class TargetForm extends ValidationFormBase{
  protected readonly form = inject(FormBuilder).group({
    instructions: ['', [Validators.required]],
    name: ['', Validators.required],
    tech_stack: ['', Validators.required],
    url: ['', Validators.required, Validators.pattern('https?://.+')],
    manual_html_content: ['']
  });
  private readonly formRepository = inject(TargetRepository);

  constructor() {
    super();
  }
  messages(name: string){
    return this.formMessages(name)
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
      await this.formRepository.create(
        this.form.value as CreateTargetRequestModel
      );
      //await this.successMessage()
      await this.router.navigateByUrl('/admin/target');
    } catch (e: Error | any) {
      console.log('Error logging in:', e);
      this.error.set( `${e?.response?.statusText ?? e.name} ${e.response?.data?.detail ?? e.message} (${e?.response?.status ?? e?.code}) `);
    } finally {
      this.loading.set(false);
    }
  }
}
