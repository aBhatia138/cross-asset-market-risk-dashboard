import streamlit as st
import refinitiv.data as rd

@st.cache_resource
def open_lseg_session():
    return rd.open_session()