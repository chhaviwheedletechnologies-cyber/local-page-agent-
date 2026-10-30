from pydantic import BaseModel, Field
from typing import List, Optional


class LocalPageRequest(BaseModel):
    business_name: str
    location: str
    website: Optional[str] = None
    services: List[str] = Field(default_factory=list)


class LocalPageResponse(BaseModel):
    status: str
    page_id: str
    business_name: str
    location: str
    url_slug: str
    seo: dict
    sections: list
    faqs: list
    schema_markup: dict
    seo_score: int