import {Component, inject, OnInit, signal} from '@angular/core';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';
import {FormBuilder, Validators, FormsModule, ReactiveFormsModule, FormControl} from '@angular/forms';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {
  CreateCompareAuditRequestModel,
  SearchAuditRequestModel
} from '@/app/domain/models/audit/request/audit-request.model';
import {StatusType} from '@/app/domain/types/status.type';
import {DatePipe, DecimalPipe, NgClass} from '@angular/common';
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
import {TranslateModule} from '@ngx-translate/core';
import {CreateCompareAuditResponseModel} from '@/app/domain/models/audit/response/audit-response.model';

@Component({
  selector: 'app-compare-audit-form',
  imports: [FormsModule, ReactiveFormsModule, NgClass, DefaultModal, HeaderModalComponent, BodyModalComponent, FooterModalComponent, TranslateModule, DecimalPipe, DatePipe],
  templateUrl: './compare-audit-form.html',
  styleUrl: './compare-audit-form.scss',
})
export class CompareAuditForm  extends ValidationFormBase implements OnInit {
  public statusAuditUtil = inject(StatusAuditUtil)
  showMessageConfirmation = signal<boolean>(false);
  responseCompareAudit = signal<CreateCompareAuditResponseModel>({} as CreateCompareAuditResponseModel);
  protected readonly form = inject(FormBuilder).group({
    web_page_id_to_compare: new FormControl<string[]>([], Validators.required),
    web_page_id: ['', Validators.required],
    include_ai_analysis: [true]
  });
  private readonly formRepository = inject(AuditRepository);
  private readonly targetRepository = inject(TargetRepository)
  public targetSearchList = signal<SearchTargetResponseModel[]>([] as SearchTargetResponseModel[])
  public loadingCompareList = signal<boolean>(false);

  constructor() {
    super();

    // Suscribirse a cambios del campo web_page_id
    this.form.get('web_page_id')?.valueChanges.subscribe(value => {
      this.formTargetSearchListToCompare.update(current => ({
        ...current,
        exclude_web_page_id: value || undefined
      }));
      // Actualizar la lista cuando cambie web_page_id
      setTimeout(() => this.targetSearchToCompare());
    });
  }

  async ngOnInit(): Promise<void> {
    const response = await this.targetSearch({
      only_page_with_audits_completed: true,
    } as SearchTargetRequestModel)
    this.targetSearchList.set(response);

    // Cargar la lista inicial después del ciclo de detección de cambios
    setTimeout(async () => {
      await this.targetSearchToCompare();
    });
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
        this.form.value as CreateCompareAuditRequestModel
      );
      console.log(response)
      this.responseCompareAudit.set(response)
      this.showMessageConfirmation.set(true);
    } catch (e: Error | any) {
      this.catchError(e)
    } finally {
      this.loading.set(false);
    }
  }
  public targetSearchListToCompare = signal<SearchTargetResponseModel[]>([] as SearchTargetResponseModel[])
  public formTargetSearchListToCompare = signal<SearchTargetRequestModel>({
    only_page_with_audits_completed: true,
    query: ''

  } as SearchTargetRequestModel)
  async targetSearchToCompare(){
    this.loadingCompareList.set(true);
    try {
      const response = await this.targetSearch(this.formTargetSearchListToCompare())
      this.targetSearchListToCompare.set(response);
    } catch (e) {
      this.targetSearchListToCompare.set([]);
    } finally {
      this.loadingCompareList.set(false);
    }
  }
  async targetSearch(params?: SearchAuditRequestModel): Promise<SearchTargetResponseModel[]>{
    return await this.targetRepository.search(params)
  }

  updateStatusFilter(value: string) {
    this.formTargetSearchListToCompare.update(current => ({
      ...current,
      status_filter: value as StatusType
    }));
    // Actualizar la lista después de cambiar el filtro
    setTimeout(() => this.targetSearchToCompare());
  }

  updateUniqueWebPage(value: boolean) {
    this.formTargetSearchListToCompare.update(current => ({
      ...current,
      unique_web_page: value
    }));
    // Actualizar la lista después de cambiar el filtro
    setTimeout(() => this.targetSearchToCompare());
  }

  updateQuery(value: string) {
    this.formTargetSearchListToCompare.update(current => ({
      ...current,
      query: value
    }));
    // Actualizar la lista después de cambiar el filtro
    setTimeout(() => this.targetSearchToCompare());
  }

  // Método para manejar el cambio de checkboxes de páginas web a comparar
  onComparePageChange(auditId: string, event: Event) {
    const checkbox = event.target as HTMLInputElement;
    const currentValues = this.form.get('web_page_id_to_compare')?.value || [];

    if (checkbox.checked) {
      // Agregar el ID si no existe
      if (!currentValues.includes(auditId)) {
        this.form.patchValue({
          web_page_id_to_compare: [...currentValues, auditId]
        });
      }
    } else {
      // Remover el ID
      this.form.patchValue({
        web_page_id_to_compare: currentValues.filter((id: string) => id !== auditId)
      });
    }
  }

  // Método para verificar si una página está seleccionada
  isPageSelected(auditId: string): boolean {
    const currentValues = this.form.get('web_page_id_to_compare')?.value || [];
    return currentValues.includes(auditId);
  }
}
