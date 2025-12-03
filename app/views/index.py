from typing import Optional

from fastapi import APIRouter, Request, Depends, Response
from fastapi.openapi.docs import get_redoc_html
from fastapi.responses import HTMLResponse, JSONResponse

from app.core.settings import templates
from app.dependencies.auth import get_optional_current_user
from app.models.users import User
from app.utils.accounts import is_admin
from app.utils.commons import get_times, render_with_times

router = APIRouter()

@router.get("/")
def index(request: Request,
          current_user: Optional[User] = Depends(get_optional_current_user)):
    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    template = "common/index.html"
    context={"request": request, "message":"AdvanDOG 개발의 주요 내용",
             "now_time_utc": _NOW_TIME_UTC,
             "now_time": _NOW_TIME,
             'current_user': current_user,
             'admin': is_admin(current_user)
             }

    return templates.TemplateResponse(template,context)


@router.get("/server", response_class=HTMLResponse,
            summary="서버 개발 페이지", description="여기는 서버 셋팅관련 페이지입니다.")
async def related_server(request: Request,
                   current_user: Optional[User] = Depends(get_optional_current_user)):
    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    extra = {
        'current_user': current_user,
        'admin': is_admin(current_user)}
    return await render_with_times(request, "common/server.html", extra)


@router.get("/docker", response_class=HTMLResponse,
            summary="도커 개발 페이지", description="여기는 우분투 서버에 도커 셋팅관련 페이지입니다.")
async def related_server(request: Request,
                   current_user: Optional[User] = Depends(get_optional_current_user)):
    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    extra = {
        'current_user': current_user,
        'admin': is_admin(current_user)}
    return await render_with_times(request, "common/docker.html", extra)


@router.get("/etc", response_class=HTMLResponse,
            summary="기타 개발관련 기록", description="여기는 개발과 관련된 기타 기록을 남기는 페이지입니다.")
async def related_etc(request: Request,
                   current_user: Optional[User] = Depends(get_optional_current_user)):
    now_time_utc, now_time = get_times()
    _NOW_TIME_UTC = now_time_utc.strftime('%Y-%m-%d %H:%M:%S.%f')
    _NOW_TIME = now_time.strftime('%Y-%m-%d %H:%M:%S.%f')

    extra = {
        'current_user': current_user,
        'admin': is_admin(current_user)}
    return await render_with_times(request, "common/etc.html", extra)


SWAGGER_JS = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js"
SWAGGER_CSS = "https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css"
SWAGGER_FAV = "https://fastapi.tiangolo.com/img/favicon.png"
COOKIE_NAME = "csrf_token"
HEADER_NAME = "X-CSRF-Token"
open_api_url = "/swagger/custom/openapi.json"

@router.get("/swagger/custom/docs", include_in_schema=False)
async def custom_docs():
    """여기에 html 문서자체를 커스텀 마이징하는 로직을 추가하면 된다.
    CSRF_TOKEN을 주입하는 경우 등...
    csrf_token을 header에 추가하는 커스텀 Swagger UI 페이지를 반환합니다.
    """
    from main import app
    openapi_url = app.openapi_url or open_api_url
    html = f"""<!doctype html>
                        <html>
                        <head>
                          <meta charset="utf-8" />
                          <meta name="viewport" content="width=device-width, initial-scale=1">
                          <title>Swagger Custom Docs</title>
                          <link rel="stylesheet" href="{SWAGGER_CSS}" />
                          <link rel="icon" type="image/png" href="{SWAGGER_FAV}" />
                          <style>
                            html {{ box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }}
                            *, *:before, *:after {{ box-sizing: inherit; }}
                            body {{ margin:0; background: #fafafa; }}
                          </style>
                        </head>
                        <body>
                          <div id="swagger-ui"></div>

                          <script src="{SWAGGER_JS}"></script>
                          <script>
                          window.onload = function() {{
                            // 쿠키에서 값 읽는 유틸 (안정적인 방법)
                            function getCookie(name) {{
                              const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
                              return m ? decodeURIComponent(m[2]) : null;
                            }}

                            // Swagger UI 초기화
                            const ui = SwaggerUIBundle({{
                              url: "{openapi_url}",
                              dom_id: '#swagger-ui',
                              deepLinking: true,
                              presets: [SwaggerUIBundle.presets.apis],
                              layout: "BaseLayout",

                              // requestInterceptor - 모든 요청이 전송되기 전에 호출됩니다.
                              requestInterceptor: function (req) {{
                                try {{
                                  // 안전한 메서드에는 CSRF를 추가하지 않습니다.
                                  const safeMethods = ['GET','HEAD','OPTIONS','TRACE'];
                                  if (!safeMethods.includes((req.method || '').toUpperCase())) {{
                                    const csrf = getCookie("{COOKIE_NAME}");
                                    if (csrf) {{
                                      // 헤더 추가 (대소문자 무관)
                                      req.headers["{HEADER_NAME}"] = csrf;
                                    }}
                                    // 쿠키 전송이 필요하면 credentials 설정 (CORS 허용 필요)
                                    // 'include' 는 cross-site에서도 쿠키를 전송합니다. same-origin이면 'same-origin' 사용 가능.
                                    req.credentials = 'include';
                                  }}
                                }} catch (e) {{
                                  console.warn('requestInterceptor error:', e);
                                }}
                                return req;
                              }},
                            }});

                            window.ui = ui;
                          }};
                          </script>
                        </body>
                        </html>"""

    # return get_swagger_ui_html(
    #     openapi_url=open_api_url,  # openapi 스펙 파일 URL
    #     title="Custom API Docs",
    # )
    return HTMLResponse(html)


@router.get("/swagger/custom/redoc", include_in_schema=False)
async def custom_redoc():
    """여기에 html 문서자체를 커스텀 마이징하는 로직을 추가하면 된다."""
    return get_redoc_html(
        openapi_url=open_api_url,   # 스펙 파일 경로
        title="Custom ReDoc",          # 페이지 제목
        redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )