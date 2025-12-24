import {Component, inject, OnInit, signal} from '@angular/core';
import {ValidationFormBase} from '@/app/presentation/shared/validation-form.base';
import {StatusAuditUtil} from '@/app/presentation/utils/status-audit.util';
import {FormBuilder, Validators, FormsModule, ReactiveFormsModule, FormControl} from '@angular/forms';
import {AuditRepository} from '@/app/domain/repositories/audit/audit.repository';
import {
  CompareAuditResponseModel,
  SearchAuditResponseModel
} from '@/app/domain/models/audit/response/audit-response.model';
import {CompareAuditRequestModel, SearchAuditRequestModel} from '@/app/domain/models/audit/request/audit-request.model';
import {StatusType} from '@/app/domain/types/status.type';
import {NgClass} from '@angular/common';

@Component({
  selector: 'app-compare-audit-form',
  imports: [FormsModule, ReactiveFormsModule, NgClass],
  templateUrl: './compare-audit-form.html',
  styleUrl: './compare-audit-form.scss',
})
export class CompareAuditForm  extends ValidationFormBase implements OnInit {
  public statusAuditUtil = inject(StatusAuditUtil)
  showMessageConfirmation = signal<boolean>(false);
  responseCreateAudit = signal<CompareAuditResponseModel>({} as CompareAuditResponseModel);
  protected readonly form = inject(FormBuilder).group({
    web_page_id_compare: new FormControl<string[]>([], Validators.required),
    web_page_id: ['', Validators.required],
    include_ai_analysis: [true]
  });
  private readonly formRepository = inject(AuditRepository);
  private readonly targetRepository = inject(AuditRepository)
  public auditSearchList = signal<SearchAuditResponseModel[]>([] as SearchAuditResponseModel[])

  constructor() {
    super();

    // Suscribirse a cambios del campo web_page_id
    this.form.get('web_page_id')?.valueChanges.subscribe(value => {
      this.formAuditSearchListToCompare.update(current => ({
        ...current,
        exclude_web_page_id: value || undefined
      }));
      // Actualizar la lista cuando cambie web_page_id
      setTimeout(() => this.auditSearchToCompare());
    });
  }

  async ngOnInit(): Promise<void> {
    const response = await this.auditSearch({
      unique_web_page: true,
      status_filter: 'completed',
    } as SearchAuditRequestModel)
    this.auditSearchList.set(response);

    // Cargar la lista inicial después del ciclo de detección de cambios
    setTimeout(async () => {
      await this.auditSearchToCompare();
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

  updateStatusFilter(value: string) {
    this.formAuditSearchListToCompare.update(current => ({
      ...current,
      status_filter: value as StatusType
    }));
    // Actualizar la lista después de cambiar el filtro
    setTimeout(() => this.auditSearchToCompare());
  }

  updateUniqueWebPage(value: boolean) {
    this.formAuditSearchListToCompare.update(current => ({
      ...current,
      unique_web_page: value
    }));
    // Actualizar la lista después de cambiar el filtro
    setTimeout(() => this.auditSearchToCompare());
  }

  // Método para manejar el cambio de checkboxes de páginas web a comparar
  onComparePageChange(auditId: string, event: Event) {
    const checkbox = event.target as HTMLInputElement;
    const currentValues = this.form.get('web_page_id_compare')?.value || [];

    if (checkbox.checked) {
      // Agregar el ID si no existe
      if (!currentValues.includes(auditId)) {
        this.form.patchValue({
          web_page_id_compare: [...currentValues, auditId]
        });
      }
    } else {
      // Remover el ID
      this.form.patchValue({
        web_page_id_compare: currentValues.filter((id: string) => id !== auditId)
      });
    }
  }

  // Método para verificar si una página está seleccionada
  isPageSelected(auditId: string): boolean {
    const currentValues = this.form.get('web_page_id_compare')?.value || [];
    return currentValues.includes(auditId);
  }
}
