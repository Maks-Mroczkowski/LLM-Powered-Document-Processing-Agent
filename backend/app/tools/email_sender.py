from typing import Any, Dict, List, Optional
from langchain.tools import BaseTool
from pydantic import Field
from loguru import logger
from app.config import settings
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailSenderTool(BaseTool):
    """Tool to send emails for notifications and workflow actions."""

    name: str = "email_sender"
    description: str = (
        "Send email notifications. "
        "Input should be a JSON string with 'to' (recipient email), "
        "'subject' (email subject), and 'body' (email body). "
        "Optional: 'html' (boolean, default False) for HTML emails."
    )

    def _create_approval_email(
        self,
        document_type: str,
        document_id: int,
        extracted_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """Create an approval notification email."""
        subject = f"Document Approved: {document_type.title()} #{document_id}"

        body = f"""
Document Processing Complete - APPROVED

Document Type: {document_type.title()}
Document ID: {document_id}
Status: APPROVED

Extracted Information:
"""
        for key, value in extracted_data.items():
            body += f"  - {key.replace('_', ' ').title()}: {value}\n"

        body += """
This document has been automatically approved based on validation rules.
No further action is required.

---
Intelligent Document Processor
"""
        return {"subject": subject, "body": body}

    def _create_review_email(
        self,
        document_type: str,
        document_id: int,
        extracted_data: Dict[str, Any],
        reason: str
    ) -> Dict[str, str]:
        """Create a review request email."""
        subject = f"Action Required: Review {document_type.title()} #{document_id}"

        body = f"""
Document Processing Complete - REVIEW REQUIRED

Document Type: {document_type.title()}
Document ID: {document_id}
Status: FLAGGED FOR REVIEW

Reason: {reason}

Extracted Information:
"""
        for key, value in extracted_data.items():
            body += f"  - {key.replace('_', ' ').title()}: {value}\n"

        body += """

Please review this document and take appropriate action.

View Document: [Link would go here]

---
Intelligent Document Processor
"""
        return {"subject": subject, "body": body}

    def _send_smtp_email(
        self,
        to: str,
        subject: str,
        body: str,
        html: bool = False
    ) -> Dict[str, Any]:
        """Send email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.email_from
            msg["To"] = to
            msg["Subject"] = subject

            # Add body
            mime_type = "html" if html else "plain"
            msg.attach(MIMEText(body, mime_type))

            # Connect to SMTP server
            logger.info(f"Connecting to SMTP server: {settings.smtp_host}:{settings.smtp_port}")

            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls()
                if settings.smtp_user and settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to}")
            return {
                "success": True,
                "message": f"Email sent to {to}",
            }

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    def _run(self, input_str: str) -> Dict[str, Any]:
        """Send email notification."""
        try:
            import json
            input_data = json.loads(input_str)

            to = input_data.get("to", "")
            subject = input_data.get("subject", "")
            body = input_data.get("body", "")
            html = input_data.get("html", False)

            if not to or not subject or not body:
                return {
                    "success": False,
                    "error": "Missing required fields: to, subject, or body",
                }

            # Validate email format
            import re
            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, to):
                return {
                    "success": False,
                    "error": f"Invalid email format: {to}",
                }

            # In development, just log the email instead of sending
            if settings.env == "development" and not settings.smtp_user:
                logger.info(f"[DEV MODE] Would send email to: {to}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Body: {body}")
                return {
                    "success": True,
                    "message": "Email logged (dev mode)",
                    "dev_mode": True,
                }

            # Send email via SMTP
            return self._send_smtp_email(to, subject, body, html)

        except Exception as e:
            logger.error(f"Error in email sender: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _arun(self, input_str: str) -> Dict[str, Any]:
        """Async version of _run."""
        return self._run(input_str)
