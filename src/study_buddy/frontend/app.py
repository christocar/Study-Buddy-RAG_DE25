import os

import httpx
import streamlit as st

# in docker this becomes http://backend:8000, locally it's localhost
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("Study Buddy")
st.caption("Upload your study material, ask questions, get answers with sources.")

if st.button("Check backend"):
    try:
        response = httpx.get(f"{API_URL}/health", timeout=5)
        response.raise_for_status()
        st.success(f"Backend says: {response.json()['status']}")
    except httpx.HTTPError as error:
        # backend is down or unreachable, show why
        st.error(f"Can't reach the backend at {API_URL}: {error}")
