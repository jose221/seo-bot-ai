import { Component, inject, OnInit, signal } from '@angular/core';
import { ValidationFormBase } from '@/app/presentation/shared/validation-form.base';
import { FormBuilder, Validators, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { NgClass } from '@angular/common';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { TranslateModule } from '@ngx-translate/core';
import { AuditRepository } from '@/app/domain/repositories/audit/audit.repository';
import { AuditUrlValidationRepository } from '@/app/domain/repositories/audit-url-validation/audit-url-validation.repository';
import { TargetRepository } from '@/app/domain/repositories/target/target.repository';
import { CreateAuditUrlValidationRequestModel } from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import { CreateAuditUrlValidationResponseModel } from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  CompareAuditResponseModel,
  SearchAuditResponseModel,
} from '@/app/domain/models/audit/response/audit-response.model';
import { DefaultModal } from '@/app/presentation/components/general/bootstrap/general-modals/default-modal/default-modal';
import { HeaderModalComponent } from '@/app/presentation/components/general/bootstrap/general-modals/sections/header-modal/header-modal.component';
import { BodyModalComponent } from '@/app/presentation/components/general/bootstrap/general-modals/sections/body-modal/body-modal.component';
import { FooterModalComponent } from '@/app/presentation/components/general/bootstrap/general-modals/sections/footer-modal/footer-modal.component';
import { requiredTrimmed, urlList } from '@/app/presentation/utils/form-validators.util';

const SOURCE_TYPES = ['audit_page', 'audit_comparison'];

@Component({
  selector: 'app-audit-url-validation-form',
  imports: [
    FormsModule,
    ReactiveFormsModule,
    NgClass,
    TranslateModule,
    RouterLink,
    DefaultModal,
    HeaderModalComponent,
    BodyModalComponent,
    FooterModalComponent,
  ],
  templateUrl: './audit-url-validation-form.html',
  styleUrl: './audit-url-validation-form.scss',
})
export class AuditUrlValidationForm extends ValidationFormBase implements OnInit {
  readonly sourceTypes = SOURCE_TYPES;

  showConfirmation = signal<boolean>(false);
  createdItem = signal<CreateAuditUrlValidationResponseModel>(
    {} as CreateAuditUrlValidationResponseModel,
  );

  // Audit search
  auditList = signal<SearchAuditResponseModel[]>([]);
  loadingAudits = signal<boolean>(false);

  // Comparison search
  comparisonList = signal<CompareAuditResponseModel[]>([]);
  loadingComparisons = signal<boolean>(false);

  // Tag filter
  availableTags = signal<string[]>([]);
  selectedTag = signal<string>('');

  protected readonly form = inject(FormBuilder).group({
    source_type: ['audit_page', Validators.required],
    source_id: ['', Validators.required],
    name_validation: ['', [requiredTrimmed(), Validators.minLength(4), Validators.maxLength(120)]],
    description_validation: [
      '',
      [requiredTrimmed(), Validators.minLength(10), Validators.maxLength(300)],
    ],
    ai_instruction: ['', [Validators.maxLength(1200)]],
    urls: ['', [requiredTrimmed(), urlList({ maxUrls: 200 })]],
  });

  private readonly _repository = inject(AuditUrlValidationRepository);
  private readonly _auditRepository = inject(AuditRepository);
  private readonly _targetRepository = inject(TargetRepository);
  private readonly _route = inject(ActivatedRoute);

  constructor() {
    super();
  }

  async ngOnInit(): Promise<void> {
    const sourceType = this._route.snapshot.queryParamMap.get('source_type');
    const sourceId = this._route.snapshot.queryParamMap.get('source_id');
    const rerunData = (history.state?.rerunData ??
      null) as Partial<CreateAuditUrlValidationRequestModel> | null;

    if (sourceType) {
      this.form.patchValue({ source_type: sourceType });
    }

    try {
      const tags = await this._targetRepository.getTags();
      this.availableTags.set(tags);
    } catch {
      this.availableTags.set([]);
    }

    await this.loadAudits();
    await this.loadComparisons();

    if (sourceId) {
      this.form.patchValue({ source_id: sourceId });
    }

    if (rerunData) {
      this.form.patchValue({
        source_type: rerunData.source_type ?? this.form.get('source_type')?.value ?? 'audit_page',
        source_id: rerunData.source_id ?? '',
        name_validation: rerunData.name_validation ?? '',
        description_validation: rerunData.description_validation ?? '',
        ai_instruction: rerunData.ai_instruction ?? '',
        urls: rerunData.urls ?? '',
      });
    }
  }

  async loadAudits(tag?: string): Promise<void> {
    this.loadingAudits.set(true);
    try {
      const params: any = { unique_web_page: true };
      if (tag) params.tag = tag;
      const response = await this._auditRepository.search(params);
      this.auditList.set(response);
    } catch {
      this.auditList.set([]);
    } finally {
      this.loadingAudits.set(false);
    }
  }

  async onTagFilter(tag: string): Promise<void> {
    this.selectedTag.set(tag);
    this.form.patchValue({ source_id: '' });
    await this.loadAudits(tag || undefined);
  }

  async loadComparisons(): Promise<void> {
    this.loadingComparisons.set(true);
    try {
      const response = await this._auditRepository.getComparisons();
      this.comparisonList.set(response);
    } catch {
      this.comparisonList.set([]);
    } finally {
      this.loadingComparisons.set(false);
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
      const response = await this._repository.create(
        this.form.value as CreateAuditUrlValidationRequestModel,
      );
      this.createdItem.set(response);
      this.showConfirmation.set(true);
    } catch (e: any) {
      this.catchError(e);
    } finally {
      this.loading.set(false);
    }
  }

  countUrls(): number {
    const val = this.form.get('urls')?.value as string;
    if (!val?.trim()) return 0;
    return val.split('\n').filter((u) => u.trim()).length;
  }
}
