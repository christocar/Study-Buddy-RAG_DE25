import httpx
import streamlit as st

from study_buddy.frontend.api_client import ask, error_message
from study_buddy.frontend.sources import source_label

st.title("Ask your notes")
st.caption(
    "Answers come only from the files you uploaded, with the exact parts they're based on."
)

# every question + answer, newest first, kept between reruns
if "results" not in st.session_state:
    st.session_state.results = []

# a question box. Enter or the button sends it
with st.form("ask", clear_on_submit=True):
    question = st.text_input("Question", label_visibility="collapsed")
    submitted = st.form_submit_button("Ask", type="primary")

if submitted and question.strip():
    try:
        with st.spinner("Looking through your notes..."):
            answer = ask(question)
        st.session_state.results.insert(0, {"question": question, **answer})
    except httpx.HTTPError as error:
        st.error(error_message(error))

# one card per question
for result in st.session_state.results:
    with st.container(border=True):
        st.markdown(f"#### {result['question']}")
        st.markdown(result["answer"])

        sources = result["sources"]
        if sources:
            st.caption(f"Based on {len(sources)} source(s)")
            for number, source in enumerate(sources, start=1):
                with st.expander(source_label(number, source)):
                    st.markdown(source["content"])
        else:
            st.caption("No sources: your uploaded material doesn't cover this.")

if st.session_state.results and st.button("Clear"):
    st.session_state.results = []
    st.rerun()
