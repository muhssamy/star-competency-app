# star_competency_app/auth/azure_sso.py
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

import msal
import requests
from flask import redirect, request, session, url_for

from star_competency_app.config.settings import get_settings
from star_competency_app.database.db_manager import DatabaseManager
from star_competency_app.database.models import User

logger = logging.getLogger(__name__)


class AzureSSO:
    def __init__(self, db_manager: DatabaseManager = None):
        self.settings = get_settings()
        self.client_id = self.settings.AZURE_CLIENT_ID
        self.client_secret = self.settings.AZURE_CLIENT_SECRET
        self.tenant_id = self.settings.AZURE_TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["User.Read"]
        self.redirect_path = "/auth/callback"

        self.db_manager = db_manager or DatabaseManager()

        # Initialize MSAL app
        self.app = msal.ConfidentialClientApplication(
            client_id=self.client_id,
            # client_credential=self.client_secret,
            authority=self.authority,
        )

    def get_auth_url(self, redirect_uri: Optional[str] = None) -> str:
        """Generate the authorization URL for Azure SSO login."""
        if not redirect_uri:
            redirect_uri = f"{self.settings.APP_URL}{self.redirect_path}"

        # Generate auth URL
        auth_url = self.app.get_authorization_request_url(
            scopes=self.scope, redirect_uri=redirect_uri, state=self._generate_state()
        )
        return auth_url

    def _generate_state(self) -> str:
        """Generate a random state for CSRF protection."""
        import uuid

        state = str(uuid.uuid4())
        session["state"] = state
        return state

    def validate_state(self, received_state: str) -> bool:
        """Validate the state parameter to prevent CSRF attacks."""
        expected_state = session.pop("state", None)
        return expected_state == received_state

    def get_token_from_code(self, auth_code: str, redirect_uri: str) -> Dict:
        """Get access token from authorization code."""
        try:
            result = self.app.acquire_token_by_authorization_code(
                code=auth_code, scopes=self.scope, redirect_uri=redirect_uri
            )
            return result
        except Exception as e:
            logger.error(f"Error acquiring token: {e}")
            return {"error": str(e)}

    def get_user_info(self, access_token: str) -> Dict:
        """Get user information from Microsoft Graph API."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            graph_data = requests.get(
                "https://graph.microsoft.com/v1.0/me", headers=headers
            ).json()
            return graph_data
        except Exception as e:
            logger.error(f"Error getting user info: {e}")
            return {"error": str(e)}

    def process_login(self, request_args) -> Tuple[bool, Optional[Dict], Optional[str]]:
        """Process the login callback from Azure AD."""
        if "error" in request_args:
            logger.error(f"Login error: {request_args['error']}")
            return False, None, f"Login error: {request_args['error']}"

        if "code" not in request_args:
            logger.error("No authorization code received")
            return False, None, "No authorization code received"

        if "state" not in request_args or not self.validate_state(
            request_args["state"]
        ):
            logger.error("Invalid state parameter")
            return False, None, "Invalid state parameter"

        # Get redirect URI
        redirect_uri = f"{self.settings.APP_URL}{self.redirect_path}"

        # Exchange code for token
        token_result = self.get_token_from_code(request_args["code"], redirect_uri)

        if "error" in token_result:
            logger.error(f"Token error: {token_result['error']}")
            return False, None, f"Token error: {token_result['error']}"

        # Get user info
        user_info = self.get_user_info(token_result["access_token"])

        if "error" in user_info:
            logger.error(f"User info error: {user_info['error']}")
            return False, None, f"User info error: {user_info['error']}"

        # Use session_scope to ensure all database operations occur within an active session
        user_data = {}
        with self.db_manager.session_scope() as db_session:
            # Check if user exists
            user = (
                db_session.query(User).filter(User.azure_id == user_info["id"]).first()
            )

            if not user:
                # Extract user details from Graph API response
                email = user_info.get("mail", user_info.get("userPrincipalName"))
                display_name = user_info.get("displayName", "New User")

                logger.info(f"Creating new user account for {display_name} ({email})")

                # Determine if this user should be an admin
                # Make the first user an admin, or users with specific emails
                admin_emails = (
                    self.settings.ADMIN_EMAILS.split(",")
                    if hasattr(self.settings, "ADMIN_EMAILS")
                    else []
                )
                is_first_user = self.db_manager.count_users() == 0
                is_admin_email = email.lower() in [
                    admin.lower() for admin in admin_emails
                ]

                # Create user directly in this session
                user = User(
                    azure_id=user_info["id"],
                    email=email,
                    display_name=display_name,
                    is_admin=is_first_user or is_admin_email,
                    is_active=True,
                )
                db_session.add(user)
                db_session.flush()  # Get the ID without committing

                logger.info(
                    f"New user created: {display_name} (Admin: {is_first_user or is_admin_email})"
                )
            else:
                # We can safely access user attributes within this session
                logger.info(f"Existing user logged in: {user.display_name}")

                # Optionally update user information if changed in Azure AD
                email = user_info.get("mail", user_info.get("userPrincipalName"))
                display_name = user_info.get("displayName")

                changes = False
                if email and user.email != email:
                    user.email = email
                    changes = True

                if display_name and user.display_name != display_name:
                    user.display_name = display_name
                    changes = True

                if changes:
                    user.updated_at = datetime.utcnow()

            # Commit changes
            db_session.commit()

            # Create a dictionary with user data that's safe to use outside the session
            user_data = {
                "id": user.id,
                "azure_id": user.azure_id,
                "name": user.display_name,
                "email": user.email,
                "is_admin": user.is_admin,
            }

        # Store user data in Flask session (outside the db session)
        session["user"] = user_data
        session["access_token"] = token_result["access_token"]

        # Log the successful login
        self.db_manager.log_audit(
            user_id=user_data["id"],
            action="login",
            entity_type="user",
            entity_id=user_data["id"],
            details=f"User logged in via Azure SSO from {request.remote_addr}",
        )

        return True, user_info, None

    def logout(self):
        """Log out the user and clear session."""
        # Log the logout if user is in session
        if "user" in session and "id" in session["user"]:
            self.db_manager.log_audit(
                user_id=session["user"]["id"],
                action="logout",
                entity_type="user",
                entity_id=session["user"]["id"],
                details=f"User logged out from {request.remote_addr}",
            )

        session.clear()
        logout_url = f"{self.authority}/oauth2/v2.0/logout?post_logout_redirect_uri={self.settings.APP_URL}"
        return logout_url
