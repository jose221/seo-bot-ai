import {Component, inject, OnInit, signal} from '@angular/core';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {FormBuilder, ReactiveFormsModule, Validators} from '@angular/forms';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {CreateAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
import {NgClass} from '@angular/common';
import {TranslatePipe} from '@ngx-translate/core';
import {TargetRepository} from '@/app/domain/repositories/target/target.repository';
import {SearchTargetResponseModel} from '@/app/domain/models/target/response/target-response.model';
import {SearchTargetRequestModel} from '@/app/domain/models/target/request/target-request.model';

@Component({
  selector: 'app-audit-form',
  imports: [
    ReactiveFormsModule,
    NgClass,
    TranslatePipe
  ],
  templateUrl: './audit-form.html',
  styleUrl: './audit-form.scss',
})
export class AuditForm extends ValidationFormBase implements OnInit {
  protected readonly form = inject(FormBuilder).group({
    include_ai_analysis: [true],
    web_page_id: ['', Validators.required]
  });
  private readonly formRepository = inject(AuditRepository);
  private readonly targetRepository = inject(TargetRepository)
  public targetSearchList = signal<SearchTargetResponseModel[]>([] as SearchTargetResponseModel[])
  constructor() {
    super();
  }

  async ngOnInit(): Promise<void> {
    await this.targetSearch()
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
        this.form.value as CreateAuditRequestModel
      );
      //await this.successMessage()
      await this.router.navigateByUrl('/admin/audit');
    } catch (e: Error | any) {
      this.catchError(e)
    } finally {
      this.loading.set(false);
    }
  }

  async targetSearch(params?: SearchTargetRequestModel): Promise<void>{
    const response = await this.targetRepository.search(params)
    this.targetSearchList.set(response);
    console.log("this.targetSearchList", this.targetSearchList())
  }

}
