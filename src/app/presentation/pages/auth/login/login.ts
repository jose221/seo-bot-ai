import {Component, inject, signal} from '@angular/core';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {Router} from '@angular/router';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {NgClass} from '@angular/common';
import {TranslateModule} from '@ngx-translate/core';
import {LanguageSelector} from '@/app/presentation/components/general/language-selector/language-selector';
import {SweetAlertUtil} from '@/app/presentation/utils/sweetAlert.util';
import {AuthRepository} from '@/app/domain/repositories/auth/auth.repository';

@Component({
  selector: 'app-login',
  imports: [
    ReactiveFormsModule,
    NgClass,
    TranslateModule,
    LanguageSelector
  ],
  templateUrl: './login.html',
  styleUrl: './login.scss',
})
export class Login extends ValidationFormBase{
  protected readonly form = inject(FormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });
  private readonly authService = inject(AuthRepository);

  constructor() {
    super();
  }
  messages(name: string){
    return this.formMessages(name)
  }
  async onSubmit() {
    this.submitted.set(true);
    if (this.form.invalid) return;
    await this.login();
  }
  async login(){
    this.error.set('');
    this.loading.set(true);
    try {
      await this.authService.login(
        {
          email: this.form.value.email!,
          password: this.form.value.password!
        }
      );
      await this.router.navigateByUrl('/admin');
    } catch (e: Error | any) {
      console.log('Error logging in:', e);
      this.error.set( `${e?.response?.statusText ?? e.name} ${e.response?.data?.detail ?? e.message} (${e?.response?.status ?? e?.code}) `);
    } finally {
      this.loading.set(false);
    }
  }
}
