"""
Authentication and authorization module.

This module provides:
- JWT token generation and verification
- Password hashing and verification
- User authentication
- Firebase authentication integration (optional)
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from .config import settings


# Configure logging
logger = logging.getLogger(__name__)


# ============================================
# PASSWORD HASHING
# ============================================

# Password context for hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


# ============================================
# JWT TOKEN MANAGEMENT
# ============================================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in token (should include 'sub' for user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_EXPIRATION_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })

    # Encode token
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {e}", exc_info=True)
        raise


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT refresh token with longer expiration.

    Args:
        data: Data to encode in token (should include 'sub' for user ID)
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()

    # Set longer expiration for refresh tokens (default 7 days)
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })

    # Encode token
    try:
        encoded_jwt = jwt.encode(
            to_encode,
            settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating refresh token: {e}", exc_info=True)
        raise


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token_type(payload: Dict[str, Any], expected_type: str):
    """
    Verify token type matches expected type.

    Args:
        payload: Decoded token payload
        expected_type: Expected token type ('access' or 'refresh')

    Raises:
        HTTPException: If token type doesn't match
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected {expected_type}, got {token_type}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ============================================
# AUTHENTICATION DEPENDENCIES
# ============================================

# HTTP Bearer security scheme
security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify JWT token and return user ID.

    This is a FastAPI dependency for protected endpoints.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid

    Example:
        @app.get("/protected")
        def protected_route(user_id: str = Depends(verify_token)):
            return {"user_id": user_id}
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)

    # Verify token type
    verify_token_type(payload, "access")

    # Extract user ID
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def verify_refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify JWT refresh token and return user ID.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        User ID from token

    Raises:
        HTTPException: If token is invalid
    """
    token = credentials.credentials

    # Decode token
    payload = decode_token(token)

    # Verify token type
    verify_token_type(payload, "refresh")

    # Extract user ID
    user_id: Optional[str] = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_id


async def optional_verify_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
    """
    Optionally verify JWT token.

    Returns None if no token provided, otherwise verifies and returns user ID.

    Args:
        credentials: Optional HTTP authorization credentials

    Returns:
        User ID from token or None
    """
    if credentials is None:
        return None

    return await verify_token(credentials)


# ============================================
# FIREBASE AUTHENTICATION (OPTIONAL)
# ============================================

_firebase_app = None


def init_firebase():
    """
    Initialize Firebase Admin SDK for authentication.

    Only called if Firebase credentials are configured.
    """
    global _firebase_app

    if not settings.FIREBASE_PROJECT_ID:
        logger.info("Firebase not configured, skipping initialization")
        return

    try:
        import firebase_admin
        from firebase_admin import credentials

        # Initialize Firebase app
        if not _firebase_app:
            _firebase_app = firebase_admin.initialize_app(
                credentials.ApplicationDefault(),
                {
                    "projectId": settings.FIREBASE_PROJECT_ID,
                }
            )
            logger.info(f"Firebase initialized for project: {settings.FIREBASE_PROJECT_ID}")

    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}", exc_info=True)
        raise


def verify_firebase_token(token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token.

    Args:
        token: Firebase ID token

    Returns:
        Decoded token with user information

    Raises:
        HTTPException: If token is invalid
    """
    if not _firebase_app:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase authentication not configured"
        )

    try:
        from firebase_admin import auth

        decoded_token = auth.verify_id_token(token)
        return decoded_token

    except Exception as e:
        logger.warning(f"Firebase token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Firebase token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def verify_firebase_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Verify Firebase authentication token.

    This is a FastAPI dependency for Firebase-protected endpoints.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Decoded Firebase token with user info

    Example:
        @app.get("/protected")
        def protected_route(user: dict = Depends(verify_firebase_auth)):
            return {"user_id": user["uid"]}
    """
    token = credentials.credentials
    return verify_firebase_token(token)


# ============================================
# API KEY AUTHENTICATION
# ============================================

def verify_api_key(api_key: str) -> bool:
    """
    Verify an API key.

    Args:
        api_key: API key to verify

    Returns:
        True if valid, False otherwise

    Note:
        In production, API keys should be stored in a database or secret manager.
    """
    # TODO: Implement actual API key verification
    # This is a placeholder implementation
    logger.warning("API key verification not fully implemented")
    return False


async def get_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and verify API key from request.

    Args:
        credentials: HTTP authorization credentials

    Returns:
        Verified API key

    Raises:
        HTTPException: If API key is invalid
    """
    api_key = credentials.credentials

    if not verify_api_key(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_user_tokens(user_id: str, **extra_data) -> Dict[str, Any]:
    """
    Create both access and refresh tokens for a user.

    Args:
        user_id: User identifier
        **extra_data: Additional data to include in token

    Returns:
        Dictionary with access_token, refresh_token, and metadata
    """
    token_data = {"sub": user_id, **extra_data}

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token({"sub": user_id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.JWT_EXPIRATION_MINUTES * 60,
    }


def extract_user_info(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract user information from token payload.

    Args:
        payload: Decoded token payload

    Returns:
        Dictionary with user information
    """
    return {
        "user_id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "roles": payload.get("roles", []),
        "issued_at": payload.get("iat"),
        "expires_at": payload.get("exp"),
    }


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Password functions
    "hash_password",
    "verify_password",
    # JWT functions
    "create_access_token",
    "create_refresh_token",
    "decode_token",
    "create_user_tokens",
    "extract_user_info",
    # Dependencies
    "verify_token",
    "verify_refresh_token",
    "optional_verify_token",
    # Firebase
    "init_firebase",
    "verify_firebase_token",
    "verify_firebase_auth",
    # API Key
    "verify_api_key",
    "get_api_key",
]
