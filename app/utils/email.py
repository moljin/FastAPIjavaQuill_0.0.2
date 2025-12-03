from fastapi_mail import FastMail, ConnectionConfig
from pydantic import EmailStr, TypeAdapter, SecretStr

from app.core.settings import CONFIG

# fastapi-mail==1.5.0 (1.5.8로 해본다.)
# -------------- FastMail 설정 --------------
if not CONFIG.SMTP_FROM:
    raise RuntimeError("SMTP_FROM environment variable is not set")
# 유효한 이메일인지 검증
MAIL_FROM: EmailStr = TypeAdapter(EmailStr).validate_python(CONFIG.SMTP_FROM)
mail_conf = ConnectionConfig(
    MAIL_USERNAME=CONFIG.SMTP_USERNAME,
    MAIL_PASSWORD=SecretStr(CONFIG.SMTP_PASSWORD or ""),
    MAIL_FROM=MAIL_FROM,
    MAIL_PORT=CONFIG.SMTP_PORT,
    MAIL_SERVER=CONFIG.SMTP_HOST,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)

# ----------------- 인증코드 이메일 HTML 템플릿(스트링) -----------------
AUTHCODE_EMAIL_HTML_TEMPLATE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>{{ title }}</title>
  <style>
    /* 이메일에서 간단히 적용되는 스타일 (대부분 이메일 클라이언트에서 지원) 직접 태그에 스타일을 먹여야 네이버에서도 적용된다.*/
    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; margin:0; padding:0; background:#f6f9fc; }
    .container { max-width:600px; margin:30px auto; background:#ffffff; border-radius:8px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }
    .logo { text-align:center; margin-bottom:8px; }
    h1 { font-size:20px; margin:6px 0 14px; color:#111827; }
    p { color:#374151; font-size:15px; line-height:1.5; }
    .code { display:block; text-align:center; font-size:28px; font-weight:700; letter-spacing:4px; background:#f3f4f6; padding:12px 18px; margin:18px auto; border-radius:8px; width:fit-content; color:#111827; }
    .small { font-size:13px; color:#6b7280; margin-top:12px; }
    .footer { font-size:12px; color:#9ca3af; text-align:center; margin-top:18px; }
    .btn { display:inline-block; text-decoration:none; background:#2563eb; color:white; padding:10px 16px; border-radius:6px; }
  </style>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; margin:0; padding:0; background:#f6f9fc;">
  <div class="container" style="max-width:600px; margin:30px auto; background:#ffffff; border-radius:8px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,0.06);">
    <div class="logo" style="text-align:center; margin-bottom:8px;">
      <!-- 로고를 원하면 img 태그 추가 -->
    </div>

    <h1 style="font-size:20px; margin:6px 0 14px; color:#111827;">회원가입을 위한 인증번호</h1>

    <p style="color:#374151; font-size:15px; line-height:1.5;">안녕하세요. 회원가입 절차를 위해 아래 인증번호를 입력해주세요. 인증번호는 <strong>10분</strong> 동안 유효합니다.</p>

    <div class="code" style="display:block; text-align:center; font-size:28px; font-weight:700; letter-spacing:4px; background:#f3f4f6; padding:12px 18px; margin:18px auto; border-radius:8px; width:fit-content; color:#111827;">{{ code }}</div>

    <p class="small" style="font-size:13px; color:#6b7280; margin-top:12px;">인증요청을 직접 하신 적이 없다면 이 메일을 무시하셔도 됩니다.</p>

    <div class="footer" style="font-size:12px; color:#9ca3af; text-align:center; margin-top:18px;">© 2025 Your Company — 안전한 서비스</div>
  </div>
</body>
</html>
"""

fastapi_email = FastMail(mail_conf)