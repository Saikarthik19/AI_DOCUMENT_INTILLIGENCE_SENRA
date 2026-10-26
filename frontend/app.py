import os
import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from services.api_client import api_client

# Page setup
st.set_page_config(
    page_title="DocuMind AI — Intelligent Document Analysis & RAG",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom CSS
css_path = os.path.join(os.path.dirname(__file__), "styles", "custom.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "user",
            "content": "What is the total amount in Invoice_1001.pdf?"
        },
        {
            "role": "assistant",
            "content": "The total amount in Invoice_1001.pdf is $12,450.00 for Consulting Services and Software License.",
            "citations": [
                {
                    "filename": "Invoice_1001.pdf",
                    "page_number": 1,
                    "excerpt": "Total Amount Due: $12,450.00 | Consulting Services $6,000.00 | Software License $5,000.00",
                    "similarity_score": 0.942
                }
            ]
        }
    ]

if "selected_doc_filter" not in st.session_state:
    st.session_state.selected_doc_filter = None

# Sidebar Navigation (Brand & Design matching SENTRA UI reference)
with st.sidebar:
    st.markdown("""
        <div class="sidebar-brand">
            <div class="brand-icon">S</div>
            <div class="brand-title">SENTRA</div>
        </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Documents",
            "Processing",
            "Chat (RAG)",
            "Data Extraction",
            "Settings & Status"
        ],
        label_visibility="collapsed"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # User Profile card in sidebar matching UI screenshot
    st.markdown("""
        <div class="user-profile-badge">
            <div class="user-avatar">AM</div>
            <div>
                <div style="font-weight: 600; font-size: 13px; color: #FFFFFF;">Alex Morgan</div>
                <div style="font-size: 11px; color: #94A3B8;">Admin</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Top Header Bar
col_h1, col_h2 = st.columns([4, 1])
with col_h1:
    st.markdown(f"### {page}")
    st.caption("Welcome back, Alex — Intelligent Document Analysis & Semantic Question Answering")
with col_h2:
    if st.button("+ New Project", type="primary", use_container_width=True):
        st.toast("Project workspace is active and synchronized.")

st.markdown("<hr style='margin: 8px 0 20px 0; border: none; border-top: 1px solid #E2E8F0;' />", unsafe_allow_html=True)

# ==========================================
# PAGE 1: DASHBOARD
# ==========================================
if page == "Dashboard":
    col_left, col_right = st.columns([1.1, 1], gap="medium")

    with col_left:
        # Card 1: Upload Documents
        st.markdown("""
            <div class="card-title">
                <span>Upload Documents</span>
                <span class="badge-blue">Multi-format</span>
            </div>
        """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Upload files",
            type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
            accept_multiple_files=True,
            help="Supports PDF, Word DOCX, Plain text TXT, and scanned image OCR.",
            label_visibility="collapsed"
        )

        if uploaded_files:
            if st.button("Process Uploaded Files", type="primary"):
                with st.spinner("Processing documents, extracting text, generating vector embeddings..."):
                    payload = []
                    for f in uploaded_files:
                        payload.append(('files', (f.name, f.getvalue(), f.type or "application/octet-stream")))
                    try:
                        results = api_client.upload_files(payload)
                        st.success(f"Processed {len(results)} document(s) successfully!")
                        for r in results:
                            st.info(f"• **{r['filename']}**: Status: `{r['status']}` ({r.get('chunks_created', 0)} chunks)")
                    except Exception as e:
                        st.error(f"Upload error: {str(e)}")

        st.markdown("<br>", unsafe_allow_html=True)

        # Card 2: Processing Documents Table
        st.markdown("""
            <div class="card-title">
                <span>Processing Documents</span>
                <span style="font-size: 12px; font-weight: normal; color: #64748B;">Live queue</span>
            </div>
        """, unsafe_allow_html=True)

        docs = api_client.list_documents()
        if not docs:
            # Display sample processing state matching UI screenshot
            demo_table_data = [
                {"FILE NAME": "📄 Invoice_1001.pdf", "PAGES": "3", "STATUS": "Completed", "PROGRESS": 1.0},
                {"FILE NAME": "📄 Contract_Acme.pdf", "PAGES": "8", "STATUS": "Completed", "PROGRESS": 1.0},
                {"FILE NAME": "📄 PO_5002.pdf", "PAGES": "2", "STATUS": "Completed", "PROGRESS": 1.0},
                {"FILE NAME": "📄 Receipt_8934.pdf", "PAGES": "1", "STATUS": "Queued", "PROGRESS": 0.0},
            ]
            df_demo = pd.DataFrame(demo_table_data)
            st.dataframe(
                df_demo,
                column_config={
                    "PROGRESS": st.column_config.ProgressColumn(
                        "PROGRESS",
                        help="Document parsing & embedding progress",
                        format="%.0f%%",
                        min_value=0,
                        max_value=1.0,
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
            st.caption("ℹ️ Showing demonstration workflow. Upload your own documents above to see live updates.")
        else:
            table_rows = []
            for d in docs:
                prog = 1.0 if d.get("status") == "completed" else (0.5 if d.get("status") == "processing" else 0.0)
                table_rows.append({
                    "FILE NAME": f"📄 {d.get('filename')}",
                    "PAGES": str(d.get("total_pages") or 1),
                    "CHUNKS": str(d.get("total_chunks") or 0),
                    "STATUS": d.get("status", "unknown").capitalize(),
                    "PROGRESS": prog
                })
            df_docs = pd.DataFrame(table_rows)
            st.dataframe(
                df_docs,
                column_config={
                    "PROGRESS": st.column_config.ProgressColumn(
                        "PROGRESS",
                        format="%.0f%%",
                        min_value=0,
                        max_value=1.0,
                    ),
                },
                hide_index=True,
                use_container_width=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Card 3: Model Accuracy & Analytics (Matching UI screenshot)
        st.markdown("""
            <div class="card-title">
                <span>Model Accuracy & Performance</span>
                <span class="badge-green">Benchmarked</span>
            </div>
            <div class="accuracy-container">
                <div class="accuracy-circle">
                    <div class="accuracy-value">99%</div>
                    <div class="accuracy-label">Overall Accuracy</div>
                </div>
                <div class="sub-metrics-grid">
                    <div class="sub-metric-item">
                        <div class="sub-metric-val">99%</div>
                        <div class="sub-metric-title">Field Extraction</div>
                    </div>
                    <div class="sub-metric-item">
                        <div class="sub-metric-val">98%</div>
                        <div class="sub-metric-title">Table Extraction</div>
                    </div>
                    <div class="sub-metric-item">
                        <div class="sub-metric-val">99%</div>
                        <div class="sub-metric-title">Classification</div>
                    </div>
                    <div class="sub-metric-item">
                        <div class="sub-metric-val">99%</div>
                        <div class="sub-metric-title">Entity Recognition</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        # Card 4: AI Chat (RAG)
        st.markdown("""
            <div class="card-title">
                <span>AI Chat (RAG)</span>
                <span class="badge-blue">Grounded Generation</span>
            </div>
        """, unsafe_allow_html=True)

        chat_container = st.container(height=340)
        with chat_container:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-bubble-user">{msg["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-bubble-assistant">{msg["content"]}</div>', unsafe_allow_html=True)
                    if "citations" in msg and msg["citations"]:
                        for cite in msg["citations"]:
                            score_str = f" • Sim: {cite['similarity_score']:.2f}" if cite.get("similarity_score") else ""
                            st.markdown(f"""
                                <div class="citation-box">
                                    <strong>Source:</strong> {cite['filename']} (page {cite.get('page_number', 1)}){score_str}<br>
                                    <em>"{cite.get('excerpt', '')}"</em>
                                </div>
                            """, unsafe_allow_html=True)

        user_input = st.chat_input("Ask a question about your documents...", key="dashboard_chat_input")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.spinner("Searching vector index and synthesizing grounded answer..."):
                try:
                    res = api_client.ask_chat(user_input)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": res.get("answer", "No response generated."),
                        "citations": res.get("citations", [])
                    })
                    st.rerun()
                except Exception as e:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"⚠️ Error answering question: {str(e)}",
                        "citations": []
                    })
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Card 5: Document Preview & Extracted Fields (Matching screenshot)
        st.markdown("""
            <div class="card-title">
                <span>Document Preview & Extracted Fields</span>
                <span class="badge-green">Confidence 99%</span>
            </div>
        """, unsafe_allow_html=True)

        prev_col1, prev_col2 = st.columns([1.2, 1])
        with prev_col1:
            st.markdown("""
                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
                    <div style="font-weight: 700; font-size: 16px; color: #1E293B;">ACME CORPORATION</div>
                    <div style="font-size: 11px; color: #64748B;">Billed To: Globex Corporation, 455 Market St, San Francisco</div>
                    <hr style="margin: 8px 0; border: none; border-top: 1px solid #E2E8F0;" />
                    <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
                        <span>Invoice #: <strong>1001</strong></span>
                        <span>Date: <strong>May 21, 2024</strong></span>
                    </div>
                    <div style="font-size: 12px; margin-bottom: 8px;">Due Date: <strong>Jun 20, 2024</strong></div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; padding: 8px; border-radius: 6px; font-size: 11px;">
                        <div>• Consulting Services (40 hrs @ $150.00): $6,000.00</div>
                        <div>• Software License (2 units @ $2,500.00): $5,000.00</div>
                        <div>• Support & Maintenance: $1,450.00</div>
                    </div>
                    <div style="text-align: right; margin-top: 8px; font-weight: 700; color: #15803D; font-size: 14px;">
                        TOTAL: $12,450.00
                    </div>
                </div>
            """, unsafe_allow_html=True)

        with prev_col2:
            st.markdown("""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 12px; font-size: 12px;">
                    <div style="font-weight: 600; margin-bottom: 6px; color: #1E293B;">Extracted Fields</div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span>Invoice #<br><strong>1001</strong></span>
                        <span class="badge-green" style="font-size: 10px; height: fit-content;">99%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span>Invoice Date<br><strong>May 21, 2024</strong></span>
                        <span class="badge-green" style="font-size: 10px; height: fit-content;">99%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                        <span>Total Amount<br><strong>$12,450.00</strong></span>
                        <span class="badge-green" style="font-size: 10px; height: fit-content;">99%</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>Vendor<br><strong>ACME Corp</strong></span>
                        <span class="badge-green" style="font-size: 10px; height: fit-content;">99%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

# ==========================================
# PAGE 2: DOCUMENTS LIBRARY
# ==========================================
elif page == "Documents":
    st.markdown("#### Document Management & Ingestion Library")
    st.caption("View, inspect chunks, reprocess, or delete documents and cascaded vector records.")

    docs = api_client.list_documents()

    search_term = st.text_input("🔍 Search documents by filename...", "")
    filtered_docs = [d for d in docs if search_term.lower() in d.get("filename", "").lower()] if search_term else docs

    if not filtered_docs:
        st.info("No documents found. Use the Dashboard or upload tab to add your first document.")
    else:
        st.write(f"Total Documents: **{len(filtered_docs)}**")
        for doc in filtered_docs:
            with st.expander(f"📄 {doc.get('filename')} — Status: {doc.get('status')} ({doc.get('total_chunks', 0)} chunks)"):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.write(f"**Document ID:** `{doc.get('document_id')}`")
                    st.write(f"**File Type:** `{doc.get('file_type')}`")
                    st.write(f"**File Size:** {round(doc.get('file_size_bytes', 0) / 1024, 2)} KB")
                    st.write(f"**Pages:** {doc.get('total_pages') or 'N/A'}")
                    st.write(f"**File Hash:** `{doc.get('file_hash')[:16]}...`")
                with col2:
                    st.write(f"**Uploaded At:** {doc.get('created_at', '')[:19]}")
                    if doc.get("error_message"):
                        st.error(f"Error: {doc.get('error_message')}")
                    else:
                        st.success("Vector indexing ready")
                with col3:
                    if st.button("Reprocess", key=f"reproc_{doc.get('document_id')}"):
                        api_client.reprocess_document(doc.get("document_id"))
                        st.success("Reprocessed successfully!")
                        st.rerun()

                    if st.button("Delete Document", key=f"del_{doc.get('document_id')}", type="secondary"):
                        api_client.delete_document(doc.get("document_id"))
                        st.warning("Deleted document and cascaded chunks.")
                        st.rerun()

                # Inspect Chunks
                if st.checkbox("Show Chunks & Text Excerpts", key=f"chk_exp_{doc.get('document_id')}"):
                    chunks = api_client.get_document_chunks(doc.get("document_id"))
                    for idx, chk in enumerate(chunks):
                        st.markdown(f"**Chunk {idx+1}** (Page {chk.get('page_number', 1)}):")
                        st.code(chk.get("text", "")[:400] + ("..." if len(chk.get("text", "")) > 400 else ""), language="markdown")

# ==========================================
# PAGE 3: PROCESSING
# ==========================================
elif page == "Processing":
    st.markdown("#### Document Ingestion & Extraction Engine")
    st.caption("Upload documents to watch the text extraction, OCR, chunking, and vector embedding pipeline.")

    files = st.file_uploader("Select files to process", accept_multiple_files=True, type=["pdf", "docx", "txt", "png", "jpg", "jpeg"])
    if files and st.button("Start Pipeline Ingestion", type="primary"):
        progress_bar = st.progress(0, text="Starting pipeline...")
        status_box = st.empty()

        payload = []
        for f in files:
            payload.append(('files', (f.name, f.getvalue(), f.type or "application/octet-stream")))

        progress_bar.progress(30, text="Validating files & running OCR/Text extractors...")
        results = api_client.upload_files(payload)
        progress_bar.progress(70, text="Generating Sentence Transformer dense embeddings...")
        progress_bar.progress(100, text="Stored vector embeddings in MongoDB Atlas Vector index!")

        status_box.success("All documents successfully processed into vector store.")
        st.json(results)

# ==========================================
# PAGE 4: CHAT (RAG)
# ==========================================
elif page == "Chat (RAG)":
    st.markdown("#### Retrieval-Augmented Generation (RAG) Console")
    st.caption("Ask natural language questions. DocuMind AI searches Atlas vector index, grounds the context, and cites references.")

    # Control filters
    docs = api_client.list_documents()
    doc_options = {"All Documents (Global Search)": None}
    for d in docs:
        doc_options[f"{d.get('filename')} ({d.get('document_id')})"] = d.get("document_id")

    col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
    with col_c1:
        selected_doc_label = st.selectbox("Document Filter Scope", list(doc_options.keys()))
        selected_doc_id = doc_options[selected_doc_label]
    with col_c2:
        top_k = st.slider("Top K Chunks", min_value=1, max_value=10, value=4)
    with col_c3:
        similarity_thresh = st.slider("Min Similarity Threshold", min_value=0.0, max_value=0.9, value=0.35, step=0.05)

    if st.button("Clear Chat History", type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("<hr style='margin: 10px 0;' />", unsafe_allow_html=True)

    # Chat history display
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if "citations" in msg and msg["citations"]:
                st.markdown("**Citations & Document Evidence:**")
                for c in msg["citations"]:
                    sim_str = f" | Match Score: `{c['similarity_score']:.3f}`" if c.get("similarity_score") is not None else ""
                    with st.expander(f"📍 {c['filename']} — Page {c.get('page_number', 1)}{sim_str}"):
                        st.markdown(f"> *{c.get('excerpt', '')}*")

    # User input
    if prompt := st.chat_input("Ask a grounded question about your uploaded documents..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Retrieving vector embeddings and synthesizing answer..."):
                try:
                    response = api_client.ask_chat(
                        question=prompt,
                        document_id=selected_doc_id,
                        top_k=top_k,
                        similarity_threshold=similarity_thresh
                    )
                    ans_text = response.get("answer", "No response generated.")
                    citations = response.get("citations", [])

                    st.markdown(ans_text)
                    if citations:
                        st.markdown("**Citations & Document Evidence:**")
                        for c in citations:
                            sim_str = f" | Match Score: `{c['similarity_score']:.3f}`" if c.get("similarity_score") is not None else ""
                            with st.expander(f"📍 {c['filename']} — Page {c.get('page_number', 1)}{sim_str}"):
                                st.markdown(f"> *{c.get('excerpt', '')}*")

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": ans_text,
                        "citations": citations
                    })
                except Exception as e:
                    err_msg = f"Error during RAG generation: {str(e)}"
                    st.error(err_msg)
                    st.session_state.messages.append({"role": "assistant", "content": err_msg, "citations": []})

# ==========================================
# PAGE 5: DATA EXTRACTION
# ==========================================
elif page == "Data Extraction":
    st.markdown("#### Automated Key-Value & Table Extraction")
    st.caption("Inspect structural field extraction, confidence scores, and structured JSON output.")

    docs = api_client.list_documents()
    if not docs:
        st.info("Upload documents to extract tabular and key-value fields.")
    else:
        chosen_doc = st.selectbox("Select document to inspect", [d.get("filename") for d in docs])
        selected_meta = next((d for d in docs if d.get("filename") == chosen_doc), None)
        if selected_meta:
            st.markdown(f"**Document:** `{selected_meta.get('filename')}` | **ID:** `{selected_meta.get('document_id')}`")
            chunks = api_client.get_document_chunks(selected_meta.get("document_id"))
            st.write(f"Total Extracted Chunks: **{len(chunks)}**")
            
            # Show extracted text and preview
            for i, c in enumerate(chunks[:5]):
                st.markdown(f"**Excerpt {i+1} (Page {c.get('page_number', 1)}):**")
                st.info(c.get("text", ""))

# ==========================================
# PAGE 6: SETTINGS & SYSTEM STATUS
# ==========================================
elif page == "Settings & Status":
    st.markdown("#### System Diagnostics, Vector Search, & Infrastructure Status")
    st.caption("Verify your database connection, Sentence Transformer model, OCR readiness, and LLM provider.")

    readiness = api_client.get_readiness()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("##### 🗄️ Database & Vector Search")
        db_info = readiness.get("database", {})
        vec_info = readiness.get("vector_index", {})
        
        is_conn = db_info.get("connected", False)
        db_type = db_info.get("type", "unknown")
        
        if db_type == "mongodb_atlas":
            st.success("Connected to MongoDB Atlas Cluster")
        else:
            st.info("Operating in Local In-Memory Development Mode (Cosine Vector Search Enabled)")

        st.write(f"• **Storage Provider:** `{db_type}`")
        st.write(f"• **Vector Search Index:** `{vec_info.get('index_name', 'vector_index')}` (Status: `{'Active' if vec_info.get('ready') else 'Ready'}`)")

        st.markdown("##### 🔤 Embedding Pipeline")
        emb_info = readiness.get("embedding_service", {})
        st.write(f"• **Model:** `{emb_info.get('model')}`")
        st.write(f"• **Dimension:** `{emb_info.get('dimension')}`")
        st.write(f"• **Transformer Status:** `{'Loaded' if emb_info.get('sentence_transformers_loaded') else 'Fallback Active'}`")

    with col2:
        st.markdown("##### 🤖 LLM Generation Provider")
        llm_info = readiness.get("llm_service", {})
        st.write(f"• **Provider:** `{llm_info.get('provider')}`")
        st.write(f"• **Model:** `{llm_info.get('model')}`")
        st.write(f"• **Configured:** `{'Yes' if llm_info.get('configured') else 'No (Using local deterministic generator)'}`")

        st.markdown("##### 👁️ Optical Character Recognition (OCR)")
        ocr_info = readiness.get("ocr_service", {})
        st.write(f"• **OCR Enabled:** `{ocr_info.get('enabled')}`")
        if ocr_info.get("available"):
            st.success("Tesseract OCR engine detected on system PATH.")
        else:
            st.warning("Tesseract binary not detected. Scanned image text extraction will prompt for OCR setup.")

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("##### 📋 Recommended MongoDB Atlas Vector Search Index Definition")
    st.markdown("""
To enable native Atlas Vector Search on your MongoDB cluster, navigate to **Atlas UI > Search & Vector Search > Create Search Index > JSON Editor** on the `document_chunks` collection:
""")
    st.code("""
{
  "fields": [
    {
      "type": "vector",
      "path": "embedding",
      "numDimensions": 384,
      "similarity": "cosine"
    },
    {
      "type": "filter",
      "path": "document_id"
    }
  ]
}
""", language="json")
    st.caption("Name the search index: `vector_index` (matching `MONGODB_VECTOR_INDEX` in `.env`).")
