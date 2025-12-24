import {Component, inject, OnInit, signal} from '@angular/core';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';
import {FormBuilder, Validators} from '@angular/forms';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {
  CompareAuditResponseModel,
  SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {CompareAuditRequestModel, SearchAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';

@Component({
  selector: 'app-compare-audit-form',
  imports: [],
  templateUrl: './compare-audit-form.html',
  styleUrl: './compare-audit-form.scss',
})
export class CompareAuditForm  extends ValidationFormBase implements OnInit {
  public statusAuditUtil = inject(StatusAuditUtil)
  showMessageConfirmation = signal<boolean>(false);
  responseCreateAudit = signal<CompareAuditResponseModel>({} as CompareAuditResponseModel);
  protected readonly form = inject(FormBuilder).group({
    include_ai_analysis: [true],
    web_page_id: ['', Validators.required]
  });
  private readonly formRepository = inject(AuditRepository);
  private readonly targetRepository = inject(AuditRepository)
  public auditSearchList = signal<SearchAuditResponseModel[]>([] as SearchAuditResponseModel[])
  constructor() {
    super();
  }

  async ngOnInit(): Promise<void> {
    const response = await this.auditSearch({
      unique_web_page: true,
      status_filter: 'completed',
    } as SearchAuditRequestModel)
    this.auditSearchList.set(response);
    await this.auditSearchToCompare()
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
      const response = await this.formRepository.compare(
        this.form.value as CompareAuditRequestModel
      );
      console.log(response)
      this.responseCreateAudit.set(response)
      this.showMessageConfirmation.set(true);
    } catch (e: Error | any) {
      this.catchError(e)
    } finally {
      this.loading.set(false);
    }
  }
  public auditSearchListToCompare = signal<SearchAuditResponseModel[]>([] as SearchAuditResponseModel[])
  public formAuditSearchListToCompare = signal<SearchAuditRequestModel>({
    unique_web_page: true,
    web_page_id: null,
    status_filter: 'completed',
    exclude_web_page_id: this.form.value.web_page_id

  } as SearchAuditRequestModel)
  async auditSearchToCompare(){
    const response = await this.auditSearch(this.formAuditSearchListToCompare())
    this.auditSearchListToCompare.set(response);
  }
  async auditSearch(params?: SearchAuditRequestModel): Promise<SearchAuditResponseModel[]>{
    return await this.targetRepository.search(params)
  }
}
