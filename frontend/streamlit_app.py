# frontend/streamlit_app.py
import requests
import streamlit as st

API_BASE = "http://127.0.0.1:8000"


def build_kb_ui():
    st.header("Phase 1: Build Knowledge Base")

    support_docs = st.file_uploader(
        "Upload 3–5 support documents (md, txt, json, pdf, ...)",
        type=["md", "txt", "json", "pdf"],
        accept_multiple_files=True,
    )

    checkout_html = st.file_uploader(
        "Upload checkout.html",
        type=["html", "htm"],
    )

    if st.button("Build Knowledge Base"):
        if not support_docs or not checkout_html:
            st.error("Please upload support documents and checkout.html")
            return

        with st.spinner("Uploading and building knowledge base..."):
            files = []
            for doc in support_docs:
                files.append(
                    (
                        "support_docs",
                        (doc.name, doc.getvalue(), doc.type or "text/plain"),
                    )
                )

            files.append(
                (
                    "checkout_html",
                    (
                        checkout_html.name,
                        checkout_html.getvalue(),
                        checkout_html.type or "text/html",
                    ),
                )
            )

            resp = requests.post(f"{API_BASE}/build_kb", files=files)

        if resp.status_code == 200:
            st.success(resp.json().get("message"))
        else:
            st.error(f"Error: {resp.text}")


def generate_test_cases_ui():
    st.header("Phase 2: Generate Test Cases")

    query = st.text_area(
        "Describe what test cases you want (e.g. 'Generate all positive and negative test cases for the discount code feature.')"
    )

    if st.button("Generate Test Cases"):
        if not query.strip():
            st.error("Enter a query first.")
            return

        with st.spinner("Generating test cases..."):
            resp = requests.post(
                f"{API_BASE}/generate_test_cases",
                json={"query": query},
            )

        if resp.status_code == 200:
            cases_md = resp.json().get("test_cases_markdown", "")
            st.subheader("Generated Test Cases (Markdown)")
            st.markdown(cases_md)
            st.session_state["last_test_cases"] = cases_md
        else:
            st.error(f"Error: {resp.text}")


def generate_selenium_ui():
    st.header("Phase 3: Generate Selenium Script")

    default_text = st.session_state.get("last_test_cases", "").strip()
    st.caption(
        "Paste ONE test case (in Markdown or text) that you want to turn into a Selenium script."
    )

    selected_test_case = st.text_area(
        "Selected Test Case",
        value=default_text,
        height=220,
    )

    if st.button("Generate Selenium Script"):
        if not selected_test_case.strip():
            st.error("Paste a test case first.")
            return

        with st.spinner("Generating Selenium Python script..."):
            resp = requests.post(
                f"{API_BASE}/generate_selenium",
                json={"test_case_markdown": selected_test_case},
            )

        if resp.status_code == 200:
            code = resp.json().get("selenium_code", "")
            st.subheader("Generated Selenium Script")
            st.code(code, language="python")
        else:
            st.error(f"Error: {resp.text}")


def main():
    st.title("Autonomous QA Agent for Test Case & Script Generation")

    tab1, tab2, tab3 = st.tabs(
        ["1️⃣ Build Knowledge Base", "2️⃣ Test Cases", "3️⃣ Selenium Scripts"]
    )

    with tab1:
        build_kb_ui()
    with tab2:
        generate_test_cases_ui()
    with tab3:
        generate_selenium_ui()


if __name__ == "__main__":
    main()
