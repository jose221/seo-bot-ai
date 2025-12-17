import {Directive, inject, Injectable, signal} from '@angular/core';
import {ValidationMessagesUtil} from '@/app/presentation/utils/validationMessages.util';

@Directive()
export abstract class ValidationFormBase {
  protected readonly submitted = signal(false);
  protected readonly loading = signal(false);
  private readonly vm = inject(ValidationMessagesUtil);
  private errorPriority: string[] = [];
  protected abstract readonly form: any
  constructor(errorPriority: string[] = ['required', 'email', 'minlength', 'maxlength', 'pattern']) {
    this.errorPriority = errorPriority;
  }


  protected formMessages(name: string): string[] {
    let msgs = this.vm.getMessages(this.form.get(name), {
      mode: 'submitted',
      submitted: this.submitted(),
      fieldLabel: name,
      errorPriority: this.errorPriority,
    }, name);
    return msgs
  }
}
