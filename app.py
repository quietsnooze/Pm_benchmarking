import streamlit as st

from uk_stress_benchmark import __version__

st.set_page_config(page_title="UK stress test benchmarking", layout="wide")

st.title("UK stress test benchmarking")
st.caption(f"v{__version__}")
st.write(
    "Benchmarking UK bank stress-test outcomes against Bank of England ACS scenarios "
    "(2014–2019). Under construction."
)
