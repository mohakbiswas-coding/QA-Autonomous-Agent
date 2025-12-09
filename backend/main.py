# backend/main.py
from typing import List

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .rag import add_document, query_knowledge_base
from .utils import extract_text_from_upload
from .llm import (
    generate_test_cases_from_context,
    generate_selenium_from_context,
)

app = FastAPI(title="Autonomous QA Agent API")

# Allow Streamlit (running on a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # for dev; restrict in real apps
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TestCaseRequest(BaseModel):
    query: str


class SeleniumRequest(BaseModel):
    test_case_markdown: str


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/build_kb")
async def build_kb(
    support_docs: List[UploadFile] = File(...),
    checkout_html: UploadFile = File(...),
):
    """
    Upload support docs + checkout HTML and build vector KB.
    """
    # Support docs
    for f in support_docs:
        data = await f.read()
        text = extract_text_from_upload(
            filename=f.filename,
            content_type=f.content_type or "",
            data=data,
        )
        add_document(text, {"source": f.filename, "type": "support"})

    # checkout.html
    html_bytes = await checkout_html.read()
    html_text = extract_text_from_upload(
        filename=checkout_html.filename,
        content_type=checkout_html.content_type or "text/html",
        data=html_bytes,
    )
    add_document(html_text, {"source": checkout_html.filename, "type": "html"})

    return {
        "message": "Knowledge base built",
        "num_files": len(support_docs) + 1,
    }


@app.post("/generate_test_cases")
async def generate_test_cases(req: TestCaseRequest):
    """
    Given a user query, retrieve docs and ask LLM for test cases.
    """
    context_chunks = query_knowledge_base(req.query, n_results=6)
    test_cases_markdown = generate_test_cases_from_context(
        req.query, context_chunks
    )
    return {"test_cases_markdown": test_cases_markdown}


@app.post("/generate_selenium")
async def generate_selenium(req: SeleniumRequest):
    """
    Given a test case (markdown), generate Selenium Python script.
    """
    # Retrieve some general context to help with selectors
    context_chunks = query_knowledge_base(
        "selectors for checkout page", n_results=10
    )
    selenium_code = generate_selenium_from_context(
        req.test_case_markdown, context_chunks
    )
    return {"selenium_code": selenium_code}
