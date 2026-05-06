import {Directive, inject, Injectable, signal} from '@angular/core';
import {ValidationMessagesUtil} from '@/app/presentation/utils/validationMessages.util';
import {Router} from '@angular/router';
import {SweetAlertUtil} from '@/app/presentation/utils/sweetAlert.util';
import {ToastService} from '@/app/helper/toast.service';

@Directive()
export abstract class ValidationFormBase {
  protected readonly router = inject(Router);
  protected readonly error = signal('');
  protected readonly submitted = signal(false);
  protected readonly loading = signal(false);
  protected readonly _sweetAlertUtil = inject(SweetAlertUtil)
  protected readonly toastService = inject(ToastService);
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
  protected async successMessage(description?: string){
    this.toastService.success(description ?? 'La operación se realizó correctamente');
  }
  protected catchError(e: Error | any){
    console.log('Error logging in:', e);
    this.error.set( `${e?.response?.statusText ?? e.name} ${e.response?.data?.detail ?? e.message} (${e?.response?.status ?? e?.code}) `);

  }
}
