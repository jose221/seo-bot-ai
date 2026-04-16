import { AppMapper } from '../app.mapper';
import {
  CreateAuditUrlValidationRequestModel,
  FilterAuditUrlValidationRequestModel,
  CreatePublicCommentRequestModel,
  AnswerCommentRequestModel,
} from '@/app/domain/models/audit-url-validation/request/audit-url-validation-request.model';
import {
  CreateAuditUrlValidationRequestDto,
  FilterAuditUrlValidationRequestDto,
  CreatePublicCommentRequestDto,
  AnswerCommentRequestDto,
} from '@/app/infrastructure/dto/request/audit-url-validation-request.dto';
import {
  AuditUrlValidationItemResponseModel,
  AuditUrlValidationListResponseModel,
  CreateAuditUrlValidationResponseModel,
  FindAuditUrlValidationResponseModel,
  AuditUrlValidationSchemasResponseModel,
  PublicCommentsResponseModel,
  PublicCommentItemModel,
  CreatePublicCommentResponseModel,
} from '@/app/domain/models/audit-url-validation/response/audit-url-validation-response.model';
import {
  AuditUrlValidationItemResponseDto,
  AuditUrlValidationListResponseDto,
  CreateAuditUrlValidationResponseDto,
  FindAuditUrlValidationResponseDto,
  AuditUrlValidationSchemasResponseDto,
  PublicCommentsResponseDto,
  CreatePublicCommentResponseDto,
} from '@/app/infrastructure/dto/response/audit-url-validation-response.dto';

export class AuditUrlValidationMapper extends AppMapper {
  constructor() {
    super();
  }

  mapCreate(model: CreateAuditUrlValidationRequestModel): CreateAuditUrlValidationRequestDto;
  mapCreate(dto: CreateAuditUrlValidationRequestDto): CreateAuditUrlValidationRequestModel;
  mapCreate(input: CreateAuditUrlValidationRequestModel | CreateAuditUrlValidationRequestDto): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapFilter(model: FilterAuditUrlValidationRequestModel): FilterAuditUrlValidationRequestDto;
  mapFilter(dto: FilterAuditUrlValidationRequestDto): FilterAuditUrlValidationRequestModel;
  mapFilter(input: FilterAuditUrlValidationRequestModel | FilterAuditUrlValidationRequestDto): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseItem(dto: AuditUrlValidationItemResponseDto): AuditUrlValidationItemResponseModel;
  mapResponseItem(model: AuditUrlValidationItemResponseModel): AuditUrlValidationItemResponseDto;
  mapResponseItem(input: AuditUrlValidationItemResponseDto | AuditUrlValidationItemResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseCreate(dto: CreateAuditUrlValidationResponseDto): CreateAuditUrlValidationResponseModel;
  mapResponseCreate(model: CreateAuditUrlValidationResponseModel): CreateAuditUrlValidationResponseDto;
  mapResponseCreate(input: CreateAuditUrlValidationResponseDto | CreateAuditUrlValidationResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseFind(dto: FindAuditUrlValidationResponseDto): FindAuditUrlValidationResponseModel;
  mapResponseFind(model: FindAuditUrlValidationResponseModel): FindAuditUrlValidationResponseDto;
  mapResponseFind(input: FindAuditUrlValidationResponseDto | FindAuditUrlValidationResponseModel): any {
    return this.autoMap<any, any>(input, { except: [] });
  }

  mapResponseList(dto: AuditUrlValidationListResponseDto): AuditUrlValidationListResponseModel {
    return new AuditUrlValidationListResponseModel(
      dto.items.map((item) => this.mapResponseItem(item as AuditUrlValidationItemResponseDto)),
      dto.total,
      dto.page,
      dto.page_size
    );
  }

  mapResponseSchemas(dto: AuditUrlValidationSchemasResponseDto): AuditUrlValidationSchemasResponseModel {
    return this.autoMap<AuditUrlValidationSchemasResponseDto, AuditUrlValidationSchemasResponseModel>(dto, { except: [] });
  }

  mapPublicComment(model: CreatePublicCommentRequestModel): CreatePublicCommentRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }

  mapResponsePublicComments(dto: PublicCommentsResponseDto): PublicCommentsResponseModel {
    return new PublicCommentsResponseModel(
      dto.validation_id,
      dto.items.map(c => new PublicCommentItemModel(
        c.id, c.schema_item_url, c.validation_id, c.username, c.comment, c.status, c.answer, c.answered_at, c.created_at
      )),
      dto.total,
      dto.page,
      dto.page_size
    );
  }

  mapResponseCreatePublicComment(dto: CreatePublicCommentResponseDto): CreatePublicCommentResponseModel {
    return this.autoMap<any, any>(dto, { except: [] });
  }

  mapAnswerComment(model: AnswerCommentRequestModel): AnswerCommentRequestDto {
    return this.autoMap<any, any>(model, { except: [] });
  }
}

