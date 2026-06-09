from typing import Any, Dict, TypedDict

from fastapi import status
from fastapi.responses import JSONResponse
from typing_extensions import NotRequired


class ResponseExample(TypedDict):
    successful: bool
    detail: NotRequired[str]
    code: NotRequired[str]


class ResponseSchema(dict):  # noqa: WPS600
    def __init__(
        self,
        status_code: int,
        description: str,
        example: ResponseExample,
    ) -> None:
        self.example = example
        self.status_code = status_code
        self.description = description
        super().__init__(
            self.schema(
                example=example,
                status_code=status_code,
                description=description,
            )
        )

    def __call__(self, detail: str = "", description: str = ""):
        example = self.example.copy()
        example["detail"] = detail or example["detail"]
        return self.schema(
            example=example,
            status_code=self.status_code,
            description=description or self.description,
        )

    @classmethod
    def schema(cls, status_code: int, description: str, example: ResponseExample) -> Dict[int, Dict[str, Any]]:
        return {
            status_code: {
                "description": description,
                "content": {
                    "application/json": {
                        "example": example,
                    },
                },
            },
        }


class SuccessfulResponse(JSONResponse):
    def __init__(self, status_code: int = status.HTTP_200_OK, **kwargs) -> None:
        kwargs |= {
            "content": {"successful": True},
            "status_code": status_code,
        }
        super().__init__(**kwargs)

    @classmethod
    def schema(cls, status_code: int = status.HTTP_200_OK) -> ResponseSchema:
        return ResponseSchema(
            status_code=status_code,
            description="Successful Response",
            example=ResponseExample(successful=True),
        )


def error_response_schema(
    status_code: int,
    example_detail: str = "Error",
    *,
    code: str | None = None,
    description: str = "Error Response",
) -> ResponseSchema:
    example: ResponseExample = {"successful": False, "detail": example_detail}
    if code is not None:
        example["code"] = code
    return ResponseSchema(status_code=status_code, description=description, example=example)


def custom_exception_response_schema(
    exc_type: type,
    example_detail: str = "Error",
    *,
    description: str | None = None,
) -> ResponseSchema:
    status_code = getattr(exc_type, "status_code", None) or status.HTTP_400_BAD_REQUEST
    return error_response_schema(
        status_code=status_code,
        example_detail=example_detail,
        code=exc_type.__name__,
        description=description or f"{exc_type.__name__} Response",
    )


class FailedResponse(JSONResponse):
    def __init__(
        self,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        **kwargs,
    ) -> None:
        kwargs |= {
            "content": {"successful": False},
            "status_code": status_code,
        }
        super().__init__(**kwargs)

    @classmethod
    def schema(cls, status_code: int = status.HTTP_400_BAD_REQUEST) -> ResponseSchema:
        return ResponseSchema(
            status_code=status_code,
            description="Failed Response",
            example=ResponseExample(successful=False),
        )
