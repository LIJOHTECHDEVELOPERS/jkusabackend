
import os
import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Dict, Any
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ==================== EMAIL CONFIGURATION ====================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.zeptomail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "emailapikey")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", "noreply@jkusa.org")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "JKUAT Student Association")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://jkusa.org")

# Brand Colors (from your CSS theme)
COLORS = {
    "primary_deep": "#171C73",
    "primary_medium": "#3258A6",
    "primary_bright": "#29A7D9",
    "primary_light": "#85D3F2",
    "neutral_light": "#F2F2F2",
    "white": "#FFFFFF",
    "gray_700": "#404040",
    "gray_600": "#525252",
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
}


class EmailService:
    """Professional email service with branded templates"""
    
    @staticmethod
    def _get_base_template(content: str, preheader: str = "") -> str:
        """
        Base email template with responsive design and brand styling.
        All emails extend this template.
        """
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>JKUAT Student Association</title>
    <!--[if mso]>
    <style type="text/css">
        body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
    </style>
    <![endif]-->
    <style>
        /* Reset styles */
        body {{
            margin: 0;
            padding: 0;
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        table {{
            border-collapse: collapse;
            mso-table-lspace: 0pt;
            mso-table-rspace: 0pt;
        }}
        img {{
            border: 0;
            height: auto;
            line-height: 100%;
            outline: none;
            text-decoration: none;
            -ms-interpolation-mode: bicubic;
        }}
        
        /* Base styles */
        body, #bodyTable {{
            background-color: {COLORS['neutral_light']};
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            font-size: 16px;
            line-height: 1.6;
            color: {COLORS['gray_700']};
            margin: 0;
            padding: 0;
            width: 100%;
        }}
        
        /* Responsive */
        @media only screen and (max-width: 600px) {{
            .container {{
                width: 100% !important;
                max-width: 100% !important;
            }}
            .mobile-padding {{
                padding-left: 20px !important;
                padding-right: 20px !important;
            }}
            .button {{
                width: 100% !important;
                text-align: center !important;
            }}
            h1 {{
                font-size: 28px !important;
                line-height: 1.2 !important;
            }}
            h2 {{
                font-size: 24px !important;
            }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: {COLORS['neutral_light']};">
    <!-- Preheader text -->
    <div style="display: none; max-height: 0; overflow: hidden; mso-hide: all;">
        {preheader}
    </div>
    
    <!-- Main wrapper table -->
    <table id="bodyTable" role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
        <tr>
            <td align="center" style="padding: 40px 20px;">
                
                <!-- Container -->
                <table class="container" role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width: 600px; width: 100%;">
                    
                    <!-- Header with gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, {COLORS['primary_deep']} 0%, {COLORS['primary_medium']} 50%, {COLORS['primary_bright']} 100%); padding: 40px 40px 30px; text-align: center; border-radius: 16px 16px 0 0;">
                            <h1 style="margin: 0; color: {COLORS['white']}; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">
                                JKUSA
                            </h1>
                            <p style="margin: 8px 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: 500;">
                                JKUAT Student Association
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td class="mobile-padding" style="background-color: {COLORS['white']}; padding: 40px;">
                            {content}
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: {COLORS['gray_700']}; padding: 30px 40px; border-radius: 0 0 16px 16px;">
                            <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="text-align: center;">
                                        <p style="margin: 0 0 12px; color: rgba(255, 255, 255, 0.8); font-size: 14px;">
                                            &copy; {datetime.now().year} JKUAT Student Association. All rights reserved.
                                        </p>
                                        <p style="margin: 0 0 16px; color: rgba(255, 255, 255, 0.6); font-size: 13px;">
                                            Jomo Kenyatta University of Agriculture and Technology
                                        </p>
                                        <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center">
                                            <tr>
                                                <td style="padding: 0 10px;">
                                                    <a href="{FRONTEND_URL}" style="color: {COLORS['primary_light']}; text-decoration: none; font-size: 13px;">Website</a>
                                                </td>
                                                <td style="padding: 0 10px; color: rgba(255, 255, 255, 0.4);">|</td>
                                                <td style="padding: 0 10px;">
                                                    <a href="{FRONTEND_URL}/support" style="color: {COLORS['primary_light']}; text-decoration: none; font-size: 13px;">Support</a>
                                                </td>
                                                <td style="padding: 0 10px; color: rgba(255, 255, 255, 0.4);">|</td>
                                                <td style="padding: 0 10px;">
                                                    <a href="{FRONTEND_URL}/privacy" style="color: {COLORS['primary_light']}; text-decoration: none; font-size: 13px;">Privacy</a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                </table>
                
            </td>
        </tr>
    </table>
</body>
</html>
"""

    @staticmethod
    def _get_button(text: str, url: str, color: str = "primary") -> str:
        """Generate a styled button"""
        bg_colors = {
            "primary": COLORS['primary_medium'],
            "success": COLORS['success'],
            "warning": COLORS['warning'],
            "error": COLORS['error'],
        }
        bg_color = bg_colors.get(color, COLORS['primary_medium'])
        
        return f"""
        <table role="presentation" cellpadding="0" cellspacing="0" border="0" align="center" style="margin: 24px 0;">
            <tr>
                <td style="border-radius: 8px; background: {bg_color}; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
                    <a href="{url}" target="_blank" style="display: inline-block; padding: 14px 32px; font-size: 16px; font-weight: 600; color: {COLORS['white']}; text-decoration: none; border-radius: 8px;">
                        {text}
                    </a>
                </td>
            </tr>
        </table>
        """

    @staticmethod
    def _get_info_box(content: str, type: str = "info") -> str:
        """Generate an info/warning/success box"""
        colors = {
            "info": (COLORS['primary_light'], COLORS['primary_deep']),
            "success": ("#D1FAE5", COLORS['success']),
            "warning": ("#FEF3C7", COLORS['warning']),
            "error": ("#FEE2E2", COLORS['error']),
        }
        bg_color, border_color = colors.get(type, colors["info"])
        
        return f"""
        <div style="background-color: {bg_color}; border-left: 4px solid {border_color}; padding: 16px 20px; margin: 20px 0; border-radius: 8px;">
            <p style="margin: 0; color: {COLORS['gray_700']}; font-size: 14px; line-height: 1.5;">
                {content}
            </p>
        </div>
        """

    @classmethod
    def get_verification_email(cls, user_name: str, verification_url: str) -> tuple[str, str]:
        """Generate email verification email"""
        content = f"""
        <h2 style="color: {COLORS['primary_deep']}; font-size: 26px; font-weight: 700; margin: 0 0 16px;">
            Welcome to JKUSA! 🎓
        </h2>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
            Hi <strong>{user_name}</strong>,
        </p>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
            Thank you for registering with the JKUAT Student Association! We're excited to have you as part of our community.
        </p>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 24px;">
            To complete your registration and activate your account, please verify your email address by clicking the button below:
        </p>
        
        {cls._get_button("Verify Email Address", verification_url, "primary")}
        
        {cls._get_info_box("This verification link will expire in 24 hours for security purposes.", "warning")}
        
        <p style="color: {COLORS['gray_600']}; font-size: 14px; line-height: 1.6; margin: 24px 0 0; padding-top: 20px; border-top: 1px solid {COLORS['neutral_light']};">
            If the button above doesn't work, copy and paste this link into your browser:
        </p>
        <p style="color: {COLORS['primary_medium']}; font-size: 13px; word-break: break-all; margin: 8px 0 0;">
            {verification_url}
        </p>
        
        <p style="color: {COLORS['gray_600']}; font-size: 14px; line-height: 1.6; margin: 24px 0 0;">
            If you didn't create this account, please ignore this email or contact our support team if you have concerns.
        </p>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 32px 0 0;">
            Best regards,<br>
            <strong>The JKUSA Team</strong>
        </p>
        """
        
        html = cls._get_base_template(
            content,
            preheader="Verify your email to activate your JKUSA account"
        )
        
        plain_text = f"""
Welcome to JKUAT Student Association!

Hi {user_name},

Thank you for registering! Please verify your email address by clicking the link below:

{verification_url}

This link will expire in 24 hours.

If you didn't create this account, please ignore this email.

Best regards,
The JKUSA Team
        """
        
        return html, plain_text

    @classmethod
    def get_password_reset_email(cls, user_name: str, reset_url: str) -> tuple[str, str]:
        """Generate password reset email"""
        content = f"""
        <h2 style="color: {COLORS['primary_deep']}; font-size: 26px; font-weight: 700; margin: 0 0 16px;">
            Password Reset Request 🔐
        </h2>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
            Hi <strong>{user_name}</strong>,
        </p>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
            We received a request to reset your password for your JKUSA account. If you made this request, click the button below to set a new password:
        </p>
        
        {cls._get_button("Reset Password", reset_url, "primary")}
        
        {cls._get_info_box("This password reset link will expire in 1 hour for security purposes.", "warning")}
        
        <p style="color: {COLORS['gray_600']}; font-size: 14px; line-height: 1.6; margin: 24px 0 0; padding-top: 20px; border-top: 1px solid {COLORS['neutral_light']};">
            If the button above doesn't work, copy and paste this link into your browser:
        </p>
        <p style="color: {COLORS['primary_medium']}; font-size: 13px; word-break: break-all; margin: 8px 0 0;">
            {reset_url}
        </p>
        
        {cls._get_info_box("If you didn't request a password reset, please ignore this email or contact support immediately if you're concerned about your account security.", "error")}
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 32px 0 0;">
            Best regards,<br>
            <strong>The JKUSA Team</strong>
        </p>
        """
        
        html = cls._get_base_template(
            content,
            preheader="Reset your JKUSA account password"
        )
        
        plain_text = f"""
Password Reset Request

Hi {user_name},

We received a request to reset your password. Click the link below to set a new password:

{reset_url}

This link will expire in 1 hour.

If you didn't request a password reset, please ignore this email.

Best regards,
The JKUSA Team
        """
        
        return html, plain_text

    @classmethod
    def get_welcome_email(cls, user_name: str) -> tuple[str, str]:
        """Generate welcome email after successful verification"""
        content = f"""
        <h2 style="color: {COLORS['primary_deep']}; font-size: 26px; font-weight: 700; margin: 0 0 16px;">
            Welcome Aboard! 🎉
        </h2>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
            Hi <strong>{user_name}</strong>,
        </p>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 0 0 20px;">
            Your email has been successfully verified! Your JKUSA account is now fully activated and ready to use.
        </p>
        
        {cls._get_info_box("You can now access all features and benefits of your JKUSA membership.", "success")}
        
        <h3 style="color: {COLORS['primary_medium']}; font-size: 20px; font-weight: 600; margin: 32px 0 16px;">
            What's Next?
        </h3>
        
        <div style="background-color: {COLORS['neutral_light']}; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <ul style="margin: 0; padding-left: 20px; color: {COLORS['gray_700']};">
                <li style="margin-bottom: 12px;">Explore upcoming events and activities</li>
                <li style="margin-bottom: 12px;">Connect with fellow students</li>
                <li style="margin-bottom: 12px;">Access exclusive member resources</li>
                <li style="margin-bottom: 0;">Stay updated with campus news</li>
            </ul>
        </div>
        
        {cls._get_button("Visit Dashboard", FRONTEND_URL + "/dashboard", "success")}
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 32px 0 0;">
            If you have any questions or need assistance, don't hesitate to reach out to our support team.
        </p>
        
        <p style="color: {COLORS['gray_700']}; font-size: 16px; line-height: 1.6; margin: 32px 0 0;">
            Best regards,<br>
            <strong>The JKUSA Team</strong>
        </p>
        """
        
        html = cls._get_base_template(
            content,
            preheader="Your JKUSA account is now active!"
        )
        
        plain_text = f"""
Welcome Aboard!

Hi {user_name},

Your email has been successfully verified! Your JKUSA account is now fully activated.

What's Next?
- Explore upcoming events and activities
- Connect with fellow students
- Access exclusive member resources
- Stay updated with campus news

Visit your dashboard at: {FRONTEND_URL}/dashboard

Best regards,
The JKUSA Team
        """
        
        return html, plain_text

    @staticmethod
    def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        plain_text_content: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None
    ) -> bool:
        """
        Send an email using the configured SMTP server.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML version of the email
            plain_text_content: Plain text version of the email
            from_email: Sender email (defaults to EMAIL_FROM)
            from_name: Sender name (defaults to EMAIL_FROM_NAME)
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        try:
            # Create message
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = f"{from_name or EMAIL_FROM_NAME} <{from_email or EMAIL_FROM}>"
            msg['To'] = to_email
            
            # Set content (plain text first, then HTML alternative)
            msg.set_content(plain_text_content)
            msg.add_alternative(html_content, subtype='html')
            
            # Send email based on port
            if SMTP_PORT == 465:
                # SSL connection
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.send_message(msg)
            elif SMTP_PORT == 587:
                # TLS connection
                with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                    server.starttls()
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                raise ValueError("SMTP_PORT must be 465 (SSL) or 587 (TLS)")
            
            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False


# ==================== CONVENIENCE FUNCTIONS ====================

def send_verification_email(email: str, user_name: str, token: str) -> bool:
    """Send email verification email"""
    verification_url = f"{FRONTEND_URL}/auth/verify?token={token}"
    html, plain = EmailService.get_verification_email(user_name, verification_url)
    return EmailService.send_email(
        to_email=email,
        subject="Verify Your Email - JKUAT Student Association",
        html_content=html,
        plain_text_content=plain
    )


def send_password_reset_email(email: str, user_name: str, token: str) -> bool:
    """Send password reset email"""
    reset_url = f"{FRONTEND_URL}/auth/reset-password?token={token}"
    html, plain = EmailService.get_password_reset_email(user_name, reset_url)
    return EmailService.send_email(
        to_email=email,
        subject="Reset Your Password - JKUAT Student Association",
        html_content=html,
        plain_text_content=plain
    )


def send_welcome_email(email: str, user_name: str) -> bool:
    """Send welcome email after verification"""
    html, plain = EmailService.get_welcome_email(user_name)
    return EmailService.send_email(
        to_email=email,
        subject="Welcome to JKUSA! Your Account is Active",
        html_content=html,
        plain_text_content=plain
    )