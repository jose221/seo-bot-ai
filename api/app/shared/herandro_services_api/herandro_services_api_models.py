from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class HsaChatCompletionsFilePayloadModel(BaseModel):
    filename: str
    file_data: str


class HsaChatCompletionsFileContentPartModel(BaseModel):
    type: Literal["file"]
    file: HsaChatCompletionsFilePayloadModel


class HsaChatCompletionsImageUrlPayloadModel(BaseModel):
    url: str
    detail: str | None = None


class HsaChatCompletionsImageContentPartModel(BaseModel):
    type: Literal["image_url"]
    image_url: HsaChatCompletionsImageUrlPayloadModel


class HsaChatCompletionsTextContentPartModel(BaseModel):
    type: Literal["text"]
    text: str


HsaChatCompletionsMessageContentPartModel = (
    HsaChatCompletionsTextContentPartModel
    | HsaChatCompletionsImageContentPartModel
    | HsaChatCompletionsFileContentPartModel
)


class HsaChatCompletionsMessageModel(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str | list[HsaChatCompletionsMessageContentPartModel]
    isContext: bool | None = None


class HsaResponseFormatModel(BaseModel):
    type: Literal["json_object", "text"]


class HsaChatCompletionsRequestModel(BaseModel):
    messages: list[HsaChatCompletionsMessageModel]
    session_id: str
    length_history: int
    auto_save: bool
    collection_name: list[str]
    model: str
    provider: str
    mode_debug: bool
    stream: bool
    tools: list[str]
    mcp_tools: list[Any]
    response_format: HsaResponseFormatModel | None = None


class HsaChatCompletionsChoiceMessageModel(BaseModel):
    role: str
    content: str | list[Any]
    refusal: str | None = None


class HsaChatCompletionsChoiceModel(BaseModel):
    index: int
    message: HsaChatCompletionsChoiceMessageModel | None = None
    delta: HsaChatCompletionsChoiceMessageModel | None = None
    finish_reason: str | None
    logprobs: Any | None = None


class HsaChatCompletionsUsageModel(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class HsaChatCompletionsResponseModel(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: list[HsaChatCompletionsChoiceModel]
    usage: HsaChatCompletionsUsageModel


class HsaCreditsModel(BaseModel):
    ok: bool
    request_id: str
    credits_cost: float
    balance_after: float
    cost_usd: float
    status_text: str
    message: str


class HsaUsageExtModel(BaseModel):
    credits: HsaCreditsModel


class HsaUsageContextModel(BaseModel):
    input_tokens_new: int
    input_tokens_cache_read: int
    output_tokens_visible: int
    output_tokens_reasoning: int
    total_tokens_reported: int
    streaming_tokens_counted: int
    chunk_count: int
    input_tokens_billed: int
    output_tokens_billed: int
    total_tokens_billed: int
    timer: float
    ext: HsaUsageExtModel


class HsaUsageModel(BaseModel):
    context: str
    usage_context: HsaUsageContextModel


class HsaDataCopilotExtraUsageModel(BaseModel):
    usage: HsaUsageModel


class HsaDataCopilotExtraModel(BaseModel):
    timer: float
    usage: HsaDataCopilotExtraUsageModel


class HsaDataCopilotRequestModel(BaseModel):
    data: Any
    format: str
    system: str
    language: str
    parent_key: str
    exclude_keys: list[str] = Field(default_factory=list)
    cache: bool
    collection_name: str
    mode_debug: bool
    model: str
    context: str
    type_response: str


class HsaDataCopilotResponseModel(BaseModel):
    code: int
    message: str
    length: int
    data: str
    extra: HsaDataCopilotExtraModel


class HsaResponsesRequestModel(BaseModel):
    input: str
    session_id: str | None = None
    collection_name: str | list[str] | None = None
    model: str = "deepseek-v4-flash"
    mode_debug: bool | None = False
    stream: bool | None = False


class HsaResponsesUsageModel(BaseModel):
    total_tokens: int = 0
    completion_tokens: int = 0
    prompt_tokens: int = 0


class HsaResponsesOutputContentModel(BaseModel):
    type: str
    text: str
    annotations: list[Any] = Field(default_factory=list)


class HsaResponsesOutputModel(BaseModel):
    type: str | list[str]
    id: str
    role: str
    content: list[HsaResponsesOutputContentModel]
    status: str


class HsaResponsesResponseModel(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: str | None = None
    object: str | None = None
    model: str | None = None
    created: int | None = None
    usage: HsaResponsesUsageModel | None = None
    rag_context: Any | None = None
    output: list[HsaResponsesOutputModel] = Field(default_factory=list)
