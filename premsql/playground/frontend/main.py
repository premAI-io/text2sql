import os
from pathlib import Path

# Load environment variables from .env file before importing other modules
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent.parent.parent / ".env"
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

import streamlit as st
from premsql.playground.frontend.components.chat import ChatComponent
from premsql.playground.frontend.components.session import SessionComponent
from premsql.playground.frontend.components.uploader import UploadComponent

st.set_page_config(page_title="PremSQL Playground", page_icon="🔍", layout="wide")


def render_main_view():
    session_component = SessionComponent()

    # Render session list with integrated delete buttons
    selected_session = session_component.render_session_list_with_actions()

    # Render create new session form
    session_creation = session_component.render_register_session()

    # Render help links
    session_component.render_additional_links()

    # Render chat for selected or newly created session
    if session_creation is not None and session_creation.status_code == 200:
        ChatComponent().render_chat_env(session_name=session_creation.session_name)
    elif selected_session is not None:
        ChatComponent().render_chat_env(session_name=selected_session)


def main():
    # Header with logo
    _, col2, _ = st.sidebar.columns([1, 2, 1])
    with col2:
        st.image(
            "https://static.premai.io/logo.svg",
            use_container_width=True,
        )
        st.header("PremSQL Playground")

    st.title("PremSQL Playground")

    # Navigation
    selected_page = st.sidebar.selectbox("Navigation", ["Chat", "Upload Data"])

    if selected_page == "Chat":
        st.write("Select or create a session to start chatting with your database.")
        render_main_view()
    else:
        st.write(
            "Upload CSV files or enter a Kaggle dataset ID to create a SQLite database "
            "for natural language powered analysis."
        )
        UploadComponent.render_kaggle_view()
        UploadComponent.render_csv_upload_view()


if __name__ == "__main__":
    main()