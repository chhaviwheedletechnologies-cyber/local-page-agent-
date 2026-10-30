from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr, Field
from database.mongo import save_contact_message

from models.schemas import (
    LocalPageRequest
)

from agents.local_page_agent import (
    LocalPageAgent
)

from database.mongo import (
    get_local_page
)


app = FastAPI(
    title="Local Page AI Agent",
    description=(
        "Birdeye-style Local Page "
        "Generation Agent"
    ),
    version="1.0.0"
)


agent = LocalPageAgent()


@app.get("/")
def root():

    return {
        "status": "running",
        "agent": "Local Page AI Agent",
        "version": "1.0.0"
    }


@app.post("/local-page/generate")
def generate_local_page(
    request: LocalPageRequest
):

    try:

        result = agent.generate(
            business_name=request.business_name,
            location=request.location,
            website=request.website,
            services=request.services
        )

        return result

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@app.get("/local-page/{page_id}")
def get_local_page_by_id(
    page_id: str
):

    page = get_local_page(
        page_id
    )

    if not page:

        raise HTTPException(
            status_code=404,
            detail="Local page not found"
        )

    return page

@app.get(
    "/local-page/{page_id}/preview",
    response_class=HTMLResponse
)
def preview_local_page(
    page_id: str
):

    page = get_local_page(
        page_id
    )

    if not page:
        raise HTTPException(
            status_code=404,
            detail="Local page not found"
        )

    html_content = page.get(
        "html_content"
    )

    if not html_content:
        raise HTTPException(
            status_code=404,
            detail="HTML content not found for this page"
        )

    return HTMLResponse(
        content=html_content,
        status_code=200
    )
    

class ContactMessageRequest(BaseModel):
    page_id: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)


@app.post("/local-page/contact")
def submit_contact_message(request: ContactMessageRequest):
    page = get_local_page(request.page_id)

    if not page:
        raise HTTPException(
            status_code=404,
            detail="Local page not found"
        )

    message_id = save_contact_message({
        "page_id": request.page_id,
        "business_name": page.get("business_name", ""),
        "name": request.name.strip(),
        "email": str(request.email),
        "message": request.message.strip(),
        "created_at": datetime.now(timezone.utc),
        "status": "new"
    })

    return {
        "success": True,
        "message": "Contact message received successfully",
        "message_id": message_id
    }   