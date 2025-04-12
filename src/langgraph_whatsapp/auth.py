from langgraph_sdk import Auth

auth = Auth()

@auth.authenticate
async def authenticate(request, path, headers, method):
    # Add production-grade auth into your LangGraph deployments, 
    # no other backend or proxy required. This is the middleware
    # that will be used to authenticate the request.
    # ex  {"identity": "default-user", "permissions": ["read", "write"]}
    return None
