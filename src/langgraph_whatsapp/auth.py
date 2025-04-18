from langgraph_sdk import Auth

auth = Auth()

@auth.authenticate
async def authenticate(request, path, headers, method):
    # Add production-grade auth into your LangGraph deployments, 
    # no other backend or proxy required. This is the middleware
    # that will be used to authenticate the request.
    # ex  {"identity": "default-user", "permissions": ["read", "write"]}

    # Extract the token from the Authorization header
    auth_header = headers.get("authorization")
    
    if auth_header and auth_header.startswith("Bearer "):
        # When using LangGraph Cloud, we can assume their token validation
        # works and just need to return a valid user object
        return {
            "identity": "langgraph_user",  # Required field
            "is_authenticated": True       # Optional, defaults to True
        }
    else:
        # If no valid Authorization header, deny access
        return None