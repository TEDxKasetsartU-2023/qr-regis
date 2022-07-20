# Mailer from GGSheet
# <3 regisbot@regisbot.iam.gserviceaccount.com
# | IMPORT SECTION
import base64
import os
import pickle
import shortuuid
import sys
import time

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from multiprocessing import Process, Queue
from typing import Any, Dict, List, Union
from queue import Empty

from googleModule.GG import sheet_management, gmail_management
from HTMLParse import html_parse
from QR import create_qr_code

# | GLOBAL DEFINE
STATUS_COL = ["Send", "Code", "Regis", "Arrival Time"]

with open("criteria_col.txt", "rt", encoding="utf-8") as file:
    CRITERIA_STRUCT = [
        [i.strip() for i in line.strip().split(":")] for line in file.readlines()
    ]
    CRITERIA_COL = [i for _, i in CRITERIA_STRUCT]

RANGE_LST = [chr(ord("A") + i) for i in range(len(STATUS_COL) + len(CRITERIA_COL))]
RANGE = f"Mailer!{RANGE_LST[0]}:{RANGE_LST[-1]}"


# | FUNCTION SECTION
def checker(mail_q: Queue, status_q: Queue, sheet_id: str):
    SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.path.split(sys.argv[0])[0], "googleModule\key.json"
    )

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )
    s = sheet_management(sheet_id, SHEET_CREDS)

    run = True
    first = True
    while run:
        try:
            run = status_q.get_nowait()
        except Empty:
            pass

        data = s.read_sheet_by_range(RANGE)
        time.sleep(1)
        val = [line + [""] * (len(RANGE_LST) - len(line)) for line in data["values"]]
        val = data_formatter(
            val,
            {"ท่านทำการสมัครเพื่อจุดประสงค์ใด": "ผู้พูดบนเวที Call for Speaker"},
            {
                "2. ข้าพเจ้ายินยอมให้นำเนื้อหาที่ใช้ประกอบการพูด, รูปภาพ, เสียง เเละวิดีโอที่มีภาพเเละ/หรือเสียงของท่าน ทั้งที่ระบุในแบบสอบถาม และเกิดขึ้นในกิจกรรม Call for Speaker 2022 (23 ก.ค. 2565) เพื่อจัดทำสื่อประชาสัมพันธ์ผ่านช่องทางโซเชียลมีเดียของ TEDxKasetsartU": {
                    "ข้าพเจ้ายินยอม": "AV-PDPA-OK",
                    "ข้าพเจ้าไม่ยินยอม": "AV-PDPA-NOT-OK",
                }
            },
        )

        if first:
            # print(val)
            first = False

        for i, line in enumerate(val):
            if line[len(CRITERIA_COL)] == "":
                mail_q.put_nowait("|".join(line))  # send mail information

                s.write_sheet_by_range(f"{RANGE_LST[len(CRITERIA_COL)]}{i}", [["TRUE"]], "RAW")
                time.sleep(1)

def data_formatter(
    data: List[List[str]],
    ignore_cond: Dict[str, str],
    val_map: Dict[str, Dict[str, Any]],
) -> List[List[Union[str, Any]]]:
    res = []
    first = True
    for line in data:
        if not first:
            ignore = False
            for col, val in ignore_cond.items():
                if line[CRITERIA_COL.index(col)] == val:
                    ignore = True
                    break

            if ignore:
                continue

            for col, val in val_map.items():
                line[CRITERIA_COL.index(col)] = val[line[CRITERIA_COL.index(col)]]

        res.append(line)

        if first:
            first = False

    return res


# | MAIN
if __name__ == "__main__":
    START = time.perf_counter()

    with open("sheet_id.txt", "rt", encoding="utf-8") as file:
        sheet_id = file.read().strip()

    mail_q = Queue()
    status_q = Queue(1)
    checker_proc = Process(
        target=checker, args=(mail_q, status_q, sheet_id)
    )

    checker_proc.start()

    GMAIL_SCOPES = ["https://mail.google.com/"]

    CREDENTIALS_FILENAME = os.path.join(
        os.path.split(sys.argv[0])[0], "googleModule\credentials.json"
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

    while True:
        try:
            mail = mail_q.get_nowait()
            mail = mail.split("|")
        except Empty:
            continue

        # send mail

        for i, line in enumerate(CRITERIA_STRUCT):
            if line[0] == "MAIL":
                MAIL = i

            if line[0] == "FNAME":
                FNAME = i

            if line[0] == "NNAME":
                NNAME = i

        uuid_code = shortuuid.uuid()
        img = create_qr_code(
            data=base64.b64encode(
                f"{mail[MAIL]}|{mail[FNAME]}|{mail[NNAME]}|{uuid_code}".encode("utf-8")
            )
        )
        img.save("qr.jpg")

        res = g.send_mail(
            "r.chantarachote@gmail.com",  # mail[MAIL],
            "อีเมลตอบกลับการลงทะเบียนงาน Call for Speaker",
            html_parse(
                "./mail.html", "{{\w*}}", {"name": mail[NNAME], "code": uuid_code}
            ),
            [
                "./qr.jpg",
                "./logo_bluo.png",
                "./tight_TEDxKasetsartU_Logo.png",
                "./c4s_map.jpg",
            ],
        )
        print(res)
        time.sleep(1)

        if time.perf_counter() - START >= 0.25 * 60:  # terminate program case
            break

    status_q.put_nowait(False)

    while checker_proc.is_alive():
        checker_proc.kill()

    checker_proc.join()
    mail_q.close()
    mail_q.cancel_join_thread()
    status_q.close()
    status_q.cancel_join_thread()
