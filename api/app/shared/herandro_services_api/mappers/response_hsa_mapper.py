from app.shared.herandro_services_api.herandro_services_api_models import (
    HsaResponsesOutputContentModel,
    HsaResponsesResponseModel,
)


class ResponseHsaMapper:
    @staticmethod
    def map_output_text(response: HsaResponsesResponseModel) -> str:
        for output_item in response.output:
            if output_item.role != "assistant":
                continue

            for content_item in output_item.content:
                if ResponseHsaMapper._is_output_text(content_item):
                    return content_item.text

        raise ValueError("HSA_RESPONSE_OUTPUT_TEXT_NOT_FOUND")

    @staticmethod
    def _is_output_text(content: HsaResponsesOutputContentModel) -> bool:
        return content.type == "output_text"
