import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Tuple, Optional
from app.config import settings

logger = logging.getLogger("uvicorn.error")

def send_password_reset_email(to_email: str, reset_url: str) -> Tuple[bool, Optional[str]]:
    """
    Sends a password reset email to the recipient.
    If SMTP settings are not provided in environment variables, logs a development banner
    with the reset link and returns the link for developer convenience.
    """
    has_smtp = bool(settings.SMTP_HOST and settings.SMTP_HOST.strip())

    if not has_smtp:
        logger.info("\n" + "=" * 70)
        logger.info("📧 [DEV MODE] PASSWORD RESET EMAIL")
        logger.info(f"To: {to_email}")
        logger.info(f"Reset Link: {reset_url}")
        logger.info("Note: Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD in backend/.env to send real emails.")
        logger.info("=" * 70 + "\n")
        return True, reset_url

    # Create email message
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Reset Your Password - {settings.PROJECT_NAME}"
    msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = to_email

    # Plain text version
    text_content = f"""Hello,

You requested a password reset for your {settings.PROJECT_NAME} account.

Please use the following link to reset your password (valid for 30 minutes):
{reset_url}

If you did not request this, please ignore this email. Your password will remain unchanged.

Best regards,
{settings.PROJECT_NAME} Team
"""

    # Rich HTML version
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; margin: 0; padding: 0; }}
    .container {{ max-width: 560px; margin: 40px auto; background-color: #ffffff; border-radius: 16px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); }}
    .header {{ background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); padding: 32px 24px; text-align: center; color: #ffffff; }}
    .header h1 {{ margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.5px; }}
    .content {{ padding: 32px 28px; line-height: 1.6; font-size: 15px; }}
    .btn-container {{ text-align: center; margin: 32px 0; }}
    .button {{ display: inline-block; background-color: #4f46e5; color: #ffffff !important; padding: 13px 28px; border-radius: 10px; text-decoration: none; font-weight: 600; font-size: 15px; box-shadow: 0 2px 4px rgba(79, 70, 229, 0.25); }}
    .link-alt {{ font-size: 12px; color: #64748b; word-break: break-all; margin-top: 20px; }}
    .footer {{ background-color: #f8fafc; padding: 20px 28px; font-size: 12px; color: #64748b; border-top: 1px solid #f1f5f9; text-align: center; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>🎓 {settings.PROJECT_NAME}</h1>
    </div>
    <div class="content">
      <p>Hello,</p>
      <p>We received a request to reset the password for your account associated with <strong>{to_email}</strong>.</p>
      <div class="btn-container">
        <a href="{reset_url}" target="_blank" class="button">Reset Password</a>
      </div>
      <p>This password reset link will expire in <strong>30 minutes</strong>.</p>
      <p>If you didn't ask for a new password, you can safely ignore this email — your account remains secure.</p>
      <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0;" />
      <p class="link-alt">
        If the button above does not work, copy and paste this URL into your browser:<br />
        <a href="{reset_url}" style="color: #4f46e5;">{reset_url}</a>
      </p>
    </div>
    <div class="footer">
      <p>&copy; 2026 {settings.PROJECT_NAME}. All rights reserved.</p>
    </div>
  </div>
</body>
</html>
"""

    part1 = MIMEText(text_content, "plain")
    part2 = MIMEText(html_content, "html")
    msg.attach(part1)
    msg.attach(part2)

    try:
        if settings.SMTP_PORT == 465:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15)
            if settings.SMTP_USE_TLS:
                server.starttls()

        if settings.SMTP_USER and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        server.send_message(msg)
        server.quit()
        logger.info(f"✅ Successfully sent password reset email to {to_email}")
        return True, None
    except Exception as e:
        logger.error(f"❌ Failed to send password reset email via SMTP: {str(e)}")
        # Fall back to logging the reset link so the user/developer is not locked out
        logger.info(f"📧 Fallback Reset Link for {to_email}: {reset_url}")
        return False, reset_url
