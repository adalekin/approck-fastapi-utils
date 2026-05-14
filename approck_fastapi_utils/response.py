from .responses import ResponseExample, ResponseSchema

HTTP_404_NOT_FOUND = ResponseSchema(
    status_code=404,
    description="Not found",
    example=ResponseExample(successful=False, detail="Not found"),
)
