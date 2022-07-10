# GGSheet manager
# | IMPORT
import base64
import email.encoders as encoder
import mimetypes
import os
import pickle
import sys

from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from typing import Dict, List, Tuple
from urllib.error import HTTPError


# | CLASSES


class sheet_management:
    def __init__(self, sheet_id: str, creds: service_account.Credentials) -> None:
        self.sheet_id = sheet_id
        self.service = self.build_service(creds)

    def build_service(self, creds):
        return build("sheets", "v4", credentials=creds)

    def read_sheet_by_range(self, _range: str):
        sheet = self.service.spreadsheets()
        return sheet.values().get(spreadsheetId=self.sheet_id, range=_range).execute()

    def write_sheet_by_range(
        self, _range: str, content: List[str], input_mode: str = "RAW"
    ):
        sheet = self.service.spreadsheets()
        return (
            sheet.values()
            .update(
                spreadsheetId=self.sheet_id,
                range=_range,
                valueInputOption=input_mode,
                body={"values": content},
            )
            .execute()
        )


class gmail_management:
    def __init__(self, creds: service_account.Credentials) -> None:
        self.service = self.build_service(creds)

    def build_service(self, creds):
        return build("gmail", "v1", credentials=creds)

    def create_message(self, receiver, subject, text, file):
        message = MIMEMultipart()
        message["to"] = receiver
        message["subject"] = subject

        msg = MIMEText(text, "html")
        message.attach(msg)

        if file is not None:
            content_type, encoding = mimetypes.guess_type(file)
            if content_type is None or encoding is not None:
                content_type = "application/octet-stream"
            main_type, sub_type = content_type.split("/", 1)
            if main_type == "image":
                with open(file, "rb") as fp:
                    msg = MIMEImage(fp.read(), _subtype=sub_type)

            filename = os.path.basename(file)
            msg.add_header("Content-Id", f"<qr>")
            msg.add_header("Content-Disposition", "inline", filename=filename)
            message.attach(msg)

        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode()}

    def send_mail(self, to: str, subject: str, qr: str, ref: str, name: str) -> None:
        r_msg = parseHTML(
            os.path.abspath(os.path.join(".", "content.html")),
            {"REF": ref, "NAME": name},
        )
        content = self.create_message(to, subject, r_msg, qr)
        try:
            res = (
                self.service.users()
                .messages()
                .send(userId="me", body=content)
                .execute()
            )
            return res
        except HTTPError as error:
            print(f"Error\n\n{error}")
            return None


# | FUNCTIONS
def parseHTML(file: str, param: Dict[str, str]) -> str:
    lines = []
    _open = "{{"
    _close = "}}"
    with open(file, "rt", encoding="utf-8") as f:
        lines = f.readlines()

    for index in range(len(lines.copy())):
        line = lines[index]
        if _open in line and _close in line:
            cut_open = [c for c in line.split(_open) if c != ""][1]
            cut_close = [c for c in cut_open.split(_close) if c != ""][0]
            lines[index] = line.replace(f"{_open}{cut_close}{_close}", param[cut_close])

    return "\n".join([l.strip("\n") for l in lines])


def init_creds(
    gmail_creds_file_path: str,
    sheet_service_acc_file_path: str,
    gmail_scopes: List[str] = ["https://mail.google.com/"],
    sheet_creds: List[str] = ["https://www.googleapis.com/auth/spreadsheets"],
) -> Tuple[service_account.Credentials, service_account.Credentials]:
    SHEET_SCOPES = sheet_creds
    SERVICE_ACCOUNT_FILE = sheet_service_acc_file_path

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )

    GMAIL_SCOPES = gmail_scopes
    CREDENTIALS_FILENAME = gmail_creds_file_path
    TOKEN_FILENAME = os.path.join(os.path.split(sys.argv[0])[0], "token.pickle")

    GMAIL_CREDS = None
    if os.path.exists(TOKEN_FILENAME):
        with open(TOKEN_FILENAME, "rb") as token:
            GMAIL_CREDS = pickle.load(token)
    if not GMAIL_CREDS or not GMAIL_CREDS.valid:
        if GMAIL_CREDS and GMAIL_CREDS.expired and GMAIL_CREDS.refresh_token:
            GMAIL_CREDS.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILENAME, GMAIL_SCOPES
            )
            GMAIL_CREDS = flow.run_local_server(port=0)

        with open(TOKEN_FILENAME, "wb") as token:
            pickle.dump(GMAIL_CREDS, token)

    return GMAIL_CREDS, SHEET_CREDS


# | MAIN
if __name__ == "__main__":
    # | GLOBAL EXECUTIONS & GLOBAL VARIABLES
    SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_FILE = os.path.join(os.path.split(sys.argv[0])[0], "key.json")

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )

    GMAIL_SCOPES = ["https://mail.google.com/"]

    CREDENTIALS_FILENAME = os.path.join(
        os.path.split(sys.argv[0])[0], "credentials.json"
    )
    TOKEN_FILENAME = os.path.join(os.path.split(sys.argv[0])[0], "token.pickle")

    GMAIL_CREDS = None
    if os.path.exists(TOKEN_FILENAME):
        with open(TOKEN_FILENAME, "rb") as token:
            GMAIL_CREDS = pickle.load(token)
    if not GMAIL_CREDS or not GMAIL_CREDS.valid:
        if GMAIL_CREDS and GMAIL_CREDS.expired and GMAIL_CREDS.refresh_token:
            GMAIL_CREDS.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILENAME, GMAIL_SCOPES
            )
            GMAIL_CREDS = flow.run_local_server(port=0)

        with open(TOKEN_FILENAME, "wb") as token:
            pickle.dump(GMAIL_CREDS, token)

    g = gmail_management(creds=GMAIL_CREDS)
    print(g.send_mail("ratcahpol.c@ku.th", "Test", "tmp.jpg", "1234"))
