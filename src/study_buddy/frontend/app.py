import httpx
import streamlit as st

from study_buddy.frontend.api_client import check_health, error_message

st.title("Study Buddy")
st.caption("Upload your study material, ask questions, get answers with sources.")
st.write("Pick **Upload** or **Chat** in the sidebar.")

if st.button("Check backend"):
    try:
        st.success(f"Backend says: {check_health()['status']}")
    except httpx.HTTPError as error:
        st.error(error_message(error))
