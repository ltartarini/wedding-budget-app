import time

import streamlit as st
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from auth.token_manager import AuthTokenManager


class Authenticator:
    def __init__(
        self,
        allowed_users: list,
        client_config: str,
        redirect_uri: str,
        token_key: str,
        cookie_name: str = "auth_jwt",
        token_duration_days: int = 1,
    ):
        st.session_state["connected"] = st.session_state.get("connected", False)
        self.allowed_users = allowed_users
        self.client_config = client_config
        self.redirect_uri = redirect_uri
        self.auth_token_manager = AuthTokenManager(
            cookie_name=cookie_name,
            token_key=token_key,
            token_duration_days=token_duration_days,
        )
        self.cookie_name = cookie_name

    def _initialize_flow(self) -> google_auth_oauthlib.flow.Flow:
        flow = google_auth_oauthlib.flow.Flow.from_client_config(
            self.client_config,
            scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.profile",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
            redirect_uri=self.redirect_uri,
        )
        return flow

    def get_auth_url(self) -> str:
        flow = self._initialize_flow()
        auth_url, _ = flow.authorization_url(
            access_type="offline", include_granted_scopes="true"
        )
        return auth_url

    def login(self):
        if not st.session_state["connected"]:
            auth_url = self.get_auth_url()
            st.link_button("Login with Google", auth_url)

    def check_auth(self):

        if st.session_state["connected"]:
            st.toast(":green[User is authenticated]")
            return

        if st.session_state.get("logout"):
            st.toast(":green[User logged out]")
            return

        token = self.auth_token_manager.get_decoded_token()
        if token is not None:
            st.query_params.clear()
            st.session_state["connected"] = True
            st.session_state["user_info"] = {
                "email": token["email"],
                "oauth_id": token["oauth_id"],
            }
            st.rerun()  # update session state

        time.sleep(1)  # important for the token to be set correctly

        auth_code = st.query_params.get("code")
        st.query_params.clear()
        if auth_code:
            flow = self._initialize_flow()
            flow.fetch_token(code=auth_code)
            creds = flow.credentials

            oauth_service = build(serviceName="oauth2", version="v2", credentials=creds)
            user_info = oauth_service.userinfo().get().execute()
            oauth_id = user_info.get("id")
            email = user_info.get("email")

            if email in self.allowed_users:
                self.auth_token_manager.set_token(email, oauth_id)
                st.session_state["connected"] = True
                st.session_state["user_info"] = {
                    "oauth_id": oauth_id,
                    "email": email,
                }
            else:
                st.toast(":red[Access denied: unauthorized user]")
            # no rerun

    def logout(self):
        st.session_state["logout"] = True
        st.session_state["user_info"] = None
        st.session_state["connected"] = None
        self.auth_token_manager.delete_token()
        # no rerun
