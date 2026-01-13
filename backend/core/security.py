"""Security utilities and future authentication hooks.

This module provides a placeholder for future SSO OAuth integration.
For MVP, all requests pass through without authentication.
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response


class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware.

    MVP: Pass-through, no authentication required.
    Future: Validate OAuth tokens from IDM via SSO.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # MVP: No authentication - pass through all requests
        # TODO: Implement SSO OAuth validation
        #
        # Future implementation:
        # token = request.headers.get("Authorization")
        # if not token or not await self.validate_sso_token(token):
        #     return JSONResponse(
        #         status_code=401,
        #         content={"detail": "Not authenticated"}
        #     )
        # request.state.user = await self.get_user_from_token(token)

        response = await call_next(request)
        return response

    # async def validate_sso_token(self, token: str) -> bool:
    #     """Validate SSO OAuth token against IDM."""
    #     # Implementation will depend on your IDM provider
    #     pass

    # async def get_user_from_token(self, token: str) -> dict:
    #     """Extract user information from validated token."""
    #     pass


def get_current_user(request: Request) -> dict | None:
    """Get current user from request state.

    MVP: Returns None (no auth).
    Future: Returns user dict from SSO token.
    """
    return getattr(request.state, "user", None)
