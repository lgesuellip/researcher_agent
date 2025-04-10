from langgraph_sdk import Auth

auth = Auth()

# TODO: Improve this function
@auth.authenticate
async def authenticate(request, path, headers, method):
    return None
