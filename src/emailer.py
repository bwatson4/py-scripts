import os
import smtplib
from email.message import EmailMessage
from typing import List, Optional
from config import from_email_addr, from_email_pass, to_email_addr, PDF_FILE


class EmailSender:
    def __init__(
        self,
        from_address: str = from_email_addr,
        password: str = from_email_pass,
        to_addresses: List[str] = to_email_addr,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        pdf_path: Optional[str] = PDF_FILE,
        subject: str = "KVA Schedule Updated",
    ):
        self.from_address = from_address
        self.password = password
        self.to_addresses = to_addresses
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.pdf_path = pdf_path
        self.subject = subject

    def _build_body(self, events):
        if events:
            event = events[0]
            return (
                f"Event Summary: {event['summary']}\n"
                f"Details: {event['description']}\n\n"
                f"Start: {event['start'].strftime('%Y-%m-%d %H:%M')}\n"
                f"End:   {event['end'].strftime('%Y-%m-%d %H:%M')}\n"
            )

        return ""

    def _attach_pdf(self, msg: EmailMessage):
        if not self.pdf_path:
            return

        with open(self.pdf_path, "rb") as f:
            pdf_data = f.read()

        msg.add_attachment(
            pdf_data,
            maintype="application",
            subtype="pdf",
            filename=os.path.basename(self.pdf_path),
        )

    def send(self, events=None):
        msg = EmailMessage()
        msg.set_content(self._build_body(events))
        msg["From"] = self.from_address
        msg["To"] = ", ".join(self.to_addresses)
        msg["Subject"] = self.subject

        self._attach_pdf(msg)

        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.from_address, self.password)
            server.send_message(msg)
