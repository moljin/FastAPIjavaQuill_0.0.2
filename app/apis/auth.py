from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/csrf_token", summary="CSRF_TOKEN End Point",)
def csrf_token_endpoint(request: Request):
    # middleware sets cookie 'csrf_token' and possibly request.state.csrf_token
    token = request.cookies.get("csrf_token")
    if not token:
        token = getattr(request.state, "csrf_token", "")
    return {"csrf_token": token}


