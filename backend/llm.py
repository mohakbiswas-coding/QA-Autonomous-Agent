# backend/llm.py
import os
from typing import List, Dict
from openai import OpenAI

# Reads OPENAI_API_KEY from environment
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_context_block(context_chunks: List[Dict]) -> str:
    """
    Convert retrieved chunks to a single text block with sources.
    """
    blocks = []
    for c in context_chunks:
        meta = c.get("metadata") or {}
        src = meta.get("source", "unknown")
        blocks.append(f"Source: {src}\n{c['text']}")
    return "\n\n---\n\n".join(blocks)


def generate_test_cases_from_context(
    user_query: str,
    context_chunks: List[Dict],
) -> str:
    """
    Use LLM to output test cases as a Markdown table.
    """
    context = build_context_block(context_chunks)

    prompt = f"""
You are a senior QA engineer.

You are given project documentation and HTML text for an e-commerce checkout page.
RULES:
- Use ONLY the provided context.
- If some behavior is not in the context, do not invent it.
- Every test case MUST reference the source document(s) that justify it.

Return test cases in Markdown table format with columns:
Test_ID | Feature | Test_Scenario | Steps | Expected_Result | Grounded_In

User request:
{user_query}

Context:
{context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or another model you have access to
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=800,
        temperature=0.2,
    )

    return response.choices[0].message.content


def generate_selenium_from_context(
    selected_test_case_markdown: str,
    context_chunks: List[Dict],
) -> str:
    """
    Use LLM to generate a runnable Selenium Python script for one test case.
    """
    context = build_context_block(context_chunks)

    prompt = f"""
You are a Python Selenium expert.

You will receive:
1. A single test case in Markdown format.
2. Documentation and HTML text as context.

Write a COMPLETE, runnable Python Selenium script that executes ONLY that test case.
REQUIREMENTS:
- Use realistic locators (id, name, CSS selector) based on the HTML text in the context.
- Open the local file "checkout.html" from disk (assume it's in the same folder as the script).
- Include clear comments and at least one assertion that checks the expected result.
- Do NOT invent elements that don't exist in the HTML context.

Return ONLY Python code, nothing else.

Test case:
{selected_test_case_markdown}

Context:
{context}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=800,
        temperature=0,
    )

    return response.choices[0].message.content
