from pydantic import BaseModel

class UploadDoc(BaseModel):
    tenant_id: str
    user_id: str
    scope: str
    group_id: str | None
