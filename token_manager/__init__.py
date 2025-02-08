import streamlit.components.v1 as components

def get_token(key=None):
    return components.declare_component(
        "token_manager",
        path="./token_manager/frontend"
    )(key=key)