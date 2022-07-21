# Mailer from GGSheet
# <3 regisbot@regisbot.iam.gserviceaccount.com

# ## todolist (last update 20220721-1239)
# #- todo - checker
# todo 1. make sure that checker won't send same mail to mail queue again
# todo 2. make data formatter read condition and data mapping from file instead of hardcode
# #- todo - All
# todo 1. make main config file

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
from queue import Empty, Full

from googleModule.GG import sheet_management, gmail_management
from HTMLParse import html_parse
from QR import create_qr_code

# | GLOBAL DEFINE
SHEET_NAME = "Mailer" # main sheet name for reading and writing status

STATUS_COL = ["Send", "Code", "Regis", "Arrival Time"] # status column that this program needed

# read criteria column from file
with open("criteria_col.txt", "rt", encoding="utf-8") as file:
    CRITERIA_STRUCT = [
        [i.strip() for i in line.strip().split(":")] for line in file.readlines()
    ]
    CRITERIA_COL = [i for _, i in CRITERIA_STRUCT]

# set up range for google sheet reading and writing
RANGE_LST = [chr(ord("A") + i) for i in range(len(STATUS_COL) + len(CRITERIA_COL))]
RANGE = f"{SHEET_NAME}!{RANGE_LST[0]}:{RANGE_LST[-1]}"


# | FUNCTION SECTION
def checker(mail_q: Queue, status_q: Queue, sheet_id: str):
    """
    The checker process is used to check the submissions from google sheet and send needed information to main process to send an email.

    Parameters
    ----------
    mail_q : Queue
        The checker will send mail information back to main process through this queue.
    status_q : Queue
        The checker will receive terminate signal from main process through this queue.
    sheet_id : str
        The google sheet id that have the Mailer sheet.
    """
    # * setup google sheet api
    SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.path.split(sys.argv[0])[0], "googleModule\key.json"
    )

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )
    s = sheet_management(sheet_id, SHEET_CREDS)

    # * Main loop
    run = True
    while run:
        # * check status
        try:
            run = status_q.get_nowait()
        except Empty:
            pass

        # * read all data from google sheet
        data = s.read_sheet_by_range(RANGE)
        time.sleep(1)

        # * data formatting
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

        # * mail sending loop
        for i, line in enumerate(val):
            # * check terminate status while working (avoid the program not closing while sending mail information)
            try:
                run = status_q.get_nowait()
            except Empty:
                pass
            else:
                if not run:
                    break

            # * send mail information to main process through the queue
            if line[len(CRITERIA_COL)] == "":
                mail_q.put_nowait("|".join([str(i)] + line))


def data_formatter(
    data: List[List[str]],
    ignore_cond: Dict[str, str],
    val_map: Dict[str, Dict[str, Any]],
) -> List[List[Union[str, Any]]]:
    """
    The data_formatter function is used for format raw data from google sheet to data that easier to work with in program.

    Parameters
    ----------
    data : List[List[str]]
        raw data from google sheet
    ignore_cond : Dict[str, str]
        The ignore condition use to ignore some of data by value of some column
    val_map : Dict[str, Dict[str, Any]]
        The dictionary for mapping raw data to another format

    Returns
    -------
    List[List[Union[str, Any]]]
        formatted data
    """

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
    # * set terminate timer
    START = time.perf_counter()

    # * read sheet id from file
    with open("sheet_id.txt", "rt", encoding="utf-8") as file:
        sheet_id = file.read().strip()

    # * setup queue for inter-process communication
    mail_q = Queue()
    status_q = Queue(1)

    # * setup checker process for reading google sheet
    checker_proc = Process(target=checker, args=(mail_q, status_q, sheet_id))

    # * start checker process
    checker_proc.start()

    # * setup google sheet api
    SHEET_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.path.split(sys.argv[0])[0], "googleModule\key.json"
    )

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )
    s = sheet_management(sheet_id, SHEET_CREDS)

    # * setup gmail api
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

    # * main program
    while True:
        # * Terminate Case
        if time.perf_counter() - START >= 0.25 * 60:
            print("Main process close by timer")
            break

        # * get mail information from checker process
        try:
            mail = mail_q.get_nowait()
            mail = mail.split("|")
            row_index = mail[0]
            mail = mail[1:]
        except Empty:
            continue

        # * prepare for mail sending
        for i, line in enumerate(CRITERIA_STRUCT):
            if line[0] == "MAIL":
                MAIL = i

            if line[0] == "FNAME":
                FNAME = i

            if line[0] == "NNAME":
                NNAME = i

        # * generate code and qr code image
        uuid_code = shortuuid.uuid()
        img = create_qr_code(
            data=base64.b64encode(
                f"{mail[MAIL]}|{mail[FNAME]}|{mail[NNAME]}|{uuid_code}".encode("utf-8")
            )
        )
        img.save("qr.jpg")

        # * send mail
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
        print(f"Result:\n{res}\nWaiting 0.5 s")
        time.sleep(0.5)

        # * update status in google sheet (mail sent and code status)
        s.write_sheet_by_range(
            f"{SHEET_NAME}!{RANGE_LST[len(CRITERIA_COL)]}{row_index}:{RANGE_LST[len(CRITERIA_COL)]+1}{row_index}",
            [["=TRUE", uuid_code]],
            "USER_ENTERED",
        )
        print("Sheet status updated\nWaiting 0.5 s")
        time.sleep(0.5)

    # * terminate checker process
    while checker_proc.is_alive():
        print("Closing checker process")
        try:
            status_q.put_nowait(False)
        except Full:
            continue
        time.sleep(0.5)

    # * before exit clean up
    checker_proc.join()
    mail_q.close()
    mail_q.cancel_join_thread()
    status_q.close()
    status_q.cancel_join_thread()
