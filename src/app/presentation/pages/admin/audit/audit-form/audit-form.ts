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
import {DefaultModal} from '@/app/presentation/components/general/bootstrap/general-modals/default-modal/default-modal';
import {
  HeaderModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import {
  BodyModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import {
  FooterModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/footer-modal/footer-modal.component';
import {ActivatedRoute, RouterLink} from '@angular/router';
import {CreateAuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';

@Component({
  selector: 'app-audit-form',
  imports: [
    ReactiveFormsModule,
    NgClass,
    TranslatePipe,
    DefaultModal,
    HeaderModalComponent,
    BodyModalComponent,
    FooterModalComponent,
    RouterLink
  ],
  templateUrl: './audit-form.html',
  styleUrl: './audit-form.scss',
})
export class AuditForm extends ValidationFormBase implements OnInit {
  public statusAuditUtil = inject(StatusAuditUtil)
  private readonly route = inject(ActivatedRoute);
  showMessageConfirmation = signal<boolean>(false);
  responseCreateAudit = signal<CreateAuditResponseModel>({} as CreateAuditResponseModel);
  protected readonly form = inject(FormBuilder).group({
    include_ai_analysis: [true],
    web_page_id: ['', Validators.required]
  });
  private readonly formRepository = inject(AuditRepository);
  private readonly targetRepository = inject(TargetRepository)
  public targetSearchList = signal<SearchTargetResponseModel[]>([] as SearchTargetResponseModel[])

  // Tag filter
  availableTags = signal<string[]>([]);
  selectedTag = signal<string>('');

  constructor() {
    super();
  }

  async ngOnInit(): Promise<void> {
    const webPageId = this.route.snapshot.queryParamMap.get('web_page_id');
    const rerunAuditId = this.route.snapshot.queryParamMap.get('rerun_audit_id');
    if (webPageId) {
      this.form.patchValue({ web_page_id: webPageId });
    }

    const rerunData = (history.state?.rerunData ?? null) as Partial<CreateAuditRequestModel> | null;
    if (rerunData) {
      this.form.patchValue({
        web_page_id: rerunData.web_page_id ?? '',
        include_ai_analysis: rerunData.include_ai_analysis ?? true,
      });
    }

    if (rerunAuditId) {
      try {
        const audit = await this.formRepository.find(rerunAuditId);
        this.form.patchValue({
          web_page_id: audit.web_page_id ?? this.form.get('web_page_id')?.value ?? '',
          include_ai_analysis: (audit as any)?.include_ai_analysis ?? this.form.get('include_ai_analysis')?.value ?? true,
        });
      } catch (e) {
        // No bloquea el formulario: se mantiene el fallback con query params/state.
        console.error('No se pudo hidratar la re-ejecucion desde rerun_audit_id:', e);
      }
    }

    // Cargar tags disponibles
    try {
      const tags = await this.targetRepository.getTags();
      this.availableTags.set(tags);
    } catch {
      this.availableTags.set([]);
    }

    try {
      await this.targetSearch();
    } catch (e) {
      console.error('No se pudieron cargar paginas objetivo:', e);
      this.targetSearchList.set([]);
    }
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
      const response = await this.formRepository.create(
        this.form.value as CreateAuditRequestModel
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

  async onTagFilter(tag: string): Promise<void> {
    this.selectedTag.set(tag);
    this.form.patchValue({ web_page_id: '' });
    await this.targetSearch({ tag: tag || undefined });
  }

  async targetSearch(params?: SearchTargetRequestModel): Promise<void>{
    const response = await this.targetRepository.search(params)
    this.targetSearchList.set(response);
  }

}
