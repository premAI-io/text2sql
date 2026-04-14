import streamlit as st
from pydantic import ValidationError

from premsql.playground.backend.api.pydantic_models import SessionCreationRequest
from premsql.playground.backend.backend_client import BackendAPIClient

additional_link_markdown = """
Here are some quick links to get you started with Prem:

- Head over to [Prem App](https://app.premai.io/projects/) to start building on Gen AI.
- [Prem AI documentation](https://docs.premai.io/get-started/why-prem)
- [PremSQL documentation](https://docs.premai.io/premsql/introduction)
"""


class SessionComponent:
    def __init__(self) -> None:
        self.backend_client = BackendAPIClient()

    def _refresh_sessions(self):
        """Force refresh session list by clearing cache"""
        st.rerun()

    def render_session_list_with_actions(self):
        """Render session list with delete buttons for each session"""
        with st.sidebar:
            st.title("Sessions")
            all_sessions = self.backend_client.list_sessions(page_size=100).sessions or []

            if all_sessions:
                # Session selector for chat
                selected_session = st.selectbox(
                    label="Select a session to chat",
                    options=[session.session_name for session in all_sessions],
                    key="session_selector",
                )

                st.divider()

                # Session management section
                st.subheader("Manage Sessions")

                # Create a container for session list with delete buttons
                for session in all_sessions:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(session.session_name)
                    with col2:
                        if st.button("Delete", key=f"del_{session.session_name}", type="secondary"):
                            response = self.backend_client.delete_session(
                                session_name=session.session_name
                            )
                            if response.status_code == 200:
                                st.success(f"Deleted: {session.session_name}")
                                st.rerun()
                            else:
                                st.error(response.error_message or "Failed to delete")

                return selected_session
            else:
                st.info("No sessions found. Create a new session below.")
                return None

    def render_register_session(self):
        with st.sidebar:
            st.divider()
            st.subheader("Create New Session")
            with st.form(
                key="session_creation",
                clear_on_submit=True,
                border=100,
                enter_to_submit=False,
            ):
                base_url = st.text_input(
                    label="AgentServer URL",
                    placeholder="http://127.0.0.1:8100",
                    help="Enter the base URL where AgentServer is running",
                )
                button = st.form_submit_button(label="Create Session")

            if button:
                if not base_url:
                    st.error("Please enter a base URL")
                    return None

                try:
                    request = SessionCreationRequest(base_url=base_url)
                except ValidationError as exc:
                    st.error(str(exc))
                    return None

                response = self.backend_client.create_session(request=request)
                if response.status_code == 200:
                    st.success(f"Session '{response.session_name}' created successfully")
                    st.rerun()
                else:
                    st.error(response.error_message or "Unable to create session")
                return response

    def render_additional_links(self):
        with st.sidebar:
            st.divider()
            with st.expander("Help & Resources", expanded=False):
                st.markdown(additional_link_markdown)

    def render_list_sessions(self):
        """Legacy method - now combined with actions"""
        return self.render_session_list_with_actions()

    def render_delete_session_view(self):
        """Legacy method - delete buttons now integrated in session list"""
        pass