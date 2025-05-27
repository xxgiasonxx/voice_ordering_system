from pydantic import BaseModel, Field
from typing import Generic, Optional, TypeVar

DataT = TypeVar('DataT')

class UnifiedResponse(BaseModel, Generic[DataT]):
    code: int = Field(default=200, description="狀態碼")
    message: str = Field(default="success", description="回應訊息")
    data: Optional[DataT] = Field(default=None, description="實際資料")