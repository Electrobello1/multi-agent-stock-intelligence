import os

import resend

from dotenv import load_dotenv


load_dotenv()


class EmailService:

    def __init__(self):

        self.api_key = os.getenv(
            "RESEND_API_KEY"
        )

        self.from_email = os.getenv(
            "EMAIL_FROM"
        )

        if not self.api_key:
            raise RuntimeError(
                "RESEND_API_KEY is not configured."
            )

        if not self.from_email:
            raise RuntimeError(
                "EMAIL_FROM is not configured."
            )

        resend.api_key = self.api_key

    def send_email(
        self,
        to_email: str,
        subject: str,
        html: str
    ):
        """
        Send a transactional email through Resend.
        """

        if not to_email:
            raise ValueError(
                "Recipient email is required."
            )

        if not subject:
            raise ValueError(
                "Email subject is required."
            )

        if not html:
            raise ValueError(
                "Email body is required."
            )

        try:

            response = resend.Emails.send(
                {
                    "from": self.from_email,
                    "to": [to_email],
                    "subject": subject,
                    "html": html
                }
            )

            return response

        except Exception as e:

            raise RuntimeError(
                f"Failed to send email: {e}"
            ) from e

    def send_verification_otp(
        self,
        to_email: str,
        otp: str
    ):
        """
        Send an email verification OTP.
        """

        subject = "Verify your email"

        html = f"""
        <html>
            <body>
                <h2>Email Verification</h2>

                <p>
                    Your verification code is:
                </p>

                <h1>{otp}</h1>

                <p>
                    This code expires in 10 minutes.
                </p>

                <p>
                    If you did not create this account,
                    you can ignore this email.
                </p>
            </body>
        </html>
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html=html
        )

    def send_password_reset_email(
            self,
            to_email: str,
            token: str,
    ):
        """
        Send a password-reset email.
        """

        reset_url = (
            f"http://localhost:3000/reset-password" ## replace with front end password reset page
            f"?email={to_email}&token={token}"
        )

        subject = "Reset your password"

        html = f"""
        <html>
            <body>
                <h2>Password Reset</h2>

                <p>
                    We received a request to reset your password.
                </p>

                <p>
                    Click the link below to choose a new password:
                </p>

                <p>
                    <a href="{reset_url}">
                        Reset Password
                    </a>
                </p>

                <p>
                    This link expires in 15 minutes.
                </p>

                <p>
                    If you did not request a password reset,
                    you can ignore this email.
                </p>
            </body>
        </html>
        """

        return self.send_email(
            to_email=to_email,
            subject=subject,
            html=html,
        )