from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pydantic import BaseModel, EmailStr
from typing import List
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent
from dotenv import load_dotenv
load_dotenv(ROOT_DIR / '.env')

class EmailSchema(BaseModel):
    email: List[EmailStr]
    body: dict

conf = ConnectionConfig(
    MAIL_USERNAME=os.environ['MAIL_USERNAME'],
    MAIL_PASSWORD=os.environ['MAIL_PASSWORD'],
    MAIL_FROM=os.environ['MAIL_FROM'],
    MAIL_PORT=int(os.environ['MAIL_PORT']),
    MAIL_SERVER=os.environ['MAIL_SERVER'],
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fm = FastMail(conf)

async def send_email(subject: str, recipients: List[str], template_body: str):
    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=template_body,
        subtype="html"
    )
    await fm.send_message(message)