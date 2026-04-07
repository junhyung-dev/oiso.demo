from pydantic import BaseModel

class FileUploadResponse(BaseModel):
    original_filename: str
    saved_filename: str
    content_type: str | None = None
    file_url: str