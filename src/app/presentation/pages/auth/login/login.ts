import {Component, inject, signal} from '@angular/core';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {AuthService} from '@/app/infrastructure/services/auth/auth.service';
import {Router} from '@angular/router';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {NgClass} from '@angular/common';
import {TranslateModule} from '@ngx-translate/core';
import {LanguageSelector} from '@/app/presentation/components/language-selector/language-selector';

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
  protected readonly error = signal('');
  protected readonly form = inject(FormBuilder).group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required]
  });
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  constructor() {
    super();
  }
  messages(name: string){
    return this.formMessages(name)
  }
  async onSubmit() {
    this.submitted.set(true);
    if (this.form.invalid) return;
    this.loading.set(true);
    this.error.set('');
    try {
      await this.authService.login(
        {
          email: this.form.value.email!,
          password: this.form.value.password!
        }
      );
      await this.router.navigateByUrl('/admin');
    } catch (e) {
      this.error.set('login.errors.invalidCredentials');
    } finally {
      this.loading.set(false);
    }
  }
}
