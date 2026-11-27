import httpx
import streamlit as st

from study_buddy.frontend.api_client import error_message, upload_file

st.title("Upload")
st.caption("Add your study material. For now: .txt and .md files.")

uploaded = st.file_uploader("Pick a file", type=["txt", "md"])

if uploaded and st.button("Upload"):
    # spinner so people know something is happening
    with st.spinner(f"Reading {uploaded.name}..."):
        try:
            result = upload_file(uploaded.name, uploaded.getvalue())
            st.success(
                f"Uploaded **{result['filename']}** (document id {result['document_id']})"
            )
        except httpx.HTTPError as error:
            st.error(error_message(error))
