"""
FastAPI authentication middleware and decorators
"""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from functools import wraps
from typing import Optional
from lib import auth_manager

# Bearer token security scheme
bearer_scheme = HTTPBearer()

def get_current_store(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    """
    Verify Bearer token and return the store_id
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    store_id = auth_manager.verify_session(token)
    
    if not store_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return store_id

def require_store_auth(store_id_param: str = "store_id"):
    """
    Decorator to require authentication for a specific store
    
    Args:
        store_id_param: Name of the path parameter containing store_id
    
    Usage:
        @app.get("/api/store/{store_id}/protected")
        @require_store_auth()
        def protected_endpoint(store_id: str):
            # This will only execute if user is authenticated for this store
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get the authenticated store_id
            auth_store_id = kwargs.get("auth_store_id")
            
            # Get the requested store_id from path
            requested_store_id = kwargs.get(store_id_param)
            
            if not auth_store_id or not requested_store_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Authentication configuration error"
                )
            
            # Verify user has access to this specific store
            if auth_store_id != requested_store_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not authorized to access store {requested_store_id}"
                )
            
            # Remove auth_store_id from kwargs before calling original function
            kwargs.pop("auth_store_id", None)
            
            return await func(*args, **kwargs)
        
        # Inject the auth dependency
        wrapper.__annotations__["auth_store_id"] = str
        defaults = wrapper.__defaults__ or ()
        wrapper.__defaults__ = (*defaults, Depends(get_current_store))
        
        return wrapper
    return decorator

def get_optional_auth() -> Optional[str]:
    """
    Get the current store_id if authenticated, None otherwise
    
    This is useful for endpoints that behave differently when authenticated
    """
    def _get_optional_auth(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
    ) -> Optional[str]:
        if not credentials:
            return None
        
        try:
            token = credentials.credentials
            return auth_manager.verify_session(token)
        except:
            return None
    
    return Depends(_get_optional_auth)

# Compatibility function for gradual migration
def check_store_auth_or_editable(store_id: str, is_authenticated: bool = False) -> bool:
    """
    Check if store access is allowed via auth OR editable flag
    
    This allows gradual migration from editable to auth system
    
    Args:
        store_id: The store to check
        is_authenticated: Whether user is authenticated for this store
    
    Returns:
        True if access is allowed
    """
    if is_authenticated:
        return True
    
    # Fall back to checking editable flag during transition
    try:
        from main import load_store_yaml
        data = load_store_yaml(store_id)
        return data.get("editable", False)
    except:
        return False