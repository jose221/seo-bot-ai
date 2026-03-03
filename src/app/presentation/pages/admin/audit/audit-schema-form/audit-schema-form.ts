import { Component, inject, OnInit, signal } from '@angular/core';
import { ValidationFormBase } from '@/app/presentation/shared/validation-form.base';
import { FormBuilder, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgClass, DatePipe } from '@angular/common';
import { RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { AuditRepository } from '@/app/domain/repositories/audit/audit.repository';
import { AuditSchemaRepository } from '@/app/domain/repositories/audit-schema/audit-schema.repository';
import { CreateAuditSchemaRequestModel } from '@/app/domain/models/audit-schema/request/audit-schema-request.model';
import { CreateAuditSchemaResponseModel } from '@/app/domain/models/audit-schema/response/audit-schema-response.model';
import { SearchAuditResponseModel } from '@/app/domain/models/audit/response/audit-response.model';
import {
  DefaultModal
} from '@/app/presentation/components/general/bootstrap/general-modals/default-modal/default-modal';
import {
  HeaderModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import {
  BodyModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import {
  FooterModalComponent
} from '@/app/presentation/components/general/bootstrap/general-modals/sections/footer-modal/footer-modal.component';

const PROGRAMMING_LANGUAGES = [
  'javascript', 'typescript', 'python', 'java', 'c#', 'php',
  'ruby', 'go', 'rust', 'kotlin', 'swift', 'dart',
];

const SOURCE_TYPES = ['audit_page'];

@Component({
  selector: 'app-audit-schema-form',
  imports: [
    FormsModule,
    ReactiveFormsModule,
    NgClass,
    DatePipe,
    TranslateModule,
    RouterLink,
    DefaultModal,
    HeaderModalComponent,
    BodyModalComponent,
    FooterModalComponent,
  ],
  templateUrl: './audit-schema-form.html',
  styleUrl: './audit-schema-form.scss',
})
export class AuditSchemaForm extends ValidationFormBase implements OnInit {

  readonly languages = PROGRAMMING_LANGUAGES;
  readonly sourceTypes = SOURCE_TYPES;

  showConfirmation = signal<boolean>(false);
  createdItem = signal<CreateAuditSchemaResponseModel>({} as CreateAuditSchemaResponseModel);

  // Audit search
  auditList = signal<SearchAuditResponseModel[]>([]);
  loadingAudits = signal<boolean>(false);

  protected readonly form = inject(FormBuilder).group({
    source_type: ['audit_page', Validators.required],
    source_id: ['', Validators.required],
    modified_schema_json: ['', Validators.required],
    include_ai_analysis: [true],
    programming_language: ['c#', Validators.required],
  });

  private readonly _schemaRepository = inject(AuditSchemaRepository);
  private readonly _auditRepository = inject(AuditRepository);

  constructor() {
    super();
  }

  async ngOnInit(): Promise<void> {
    await this.loadAudits();
  }

  async loadAudits(): Promise<void> {
    this.loadingAudits.set(true);
    try {
      const response = await this._auditRepository.search({ unique_web_page: true });
      this.auditList.set(response);
    } catch (e) {
      this.auditList.set([]);
    } finally {
      this.loadingAudits.set(false);
    }
  }

  messages(name: string): string[] {
    return this.formMessages(name);
  }

  async onSubmit(): Promise<void> {
    this.submitted.set(true);
    if (this.form.invalid) return;
    await this.create();
  }

  async create(): Promise<void> {
    this.error.set('');
    this.loading.set(true);
    try {
      const response = await this._schemaRepository.create(
        this.form.value as CreateAuditSchemaRequestModel
      );
      this.createdItem.set(response);
      this.showConfirmation.set(true);
    } catch (e: any) {
      this.catchError(e);
    } finally {
      this.loading.set(false);
    }
  }

  isJsonValid(): boolean {
    const val = this.form.get('modified_schema_json')?.value;
    if (!val) return false;
    try {
      JSON.parse(val as string);
      return true;
    } catch {
      return false;
    }
  }

  formatJson(): void {
    const ctrl = this.form.get('modified_schema_json');
    if (!ctrl?.value) return;
    try {
      const parsed = JSON.parse(ctrl.value as string);
      ctrl.setValue(JSON.stringify(parsed, null, 2));
    } catch { /* ignore */ }
  }
}

