# Mailer from GGSheet
# <3 regisbot@regisbot.iam.gserviceaccount.com

# ## todolist (last update 20220721-1239)
# #- todo - checker
# -todo 1. make sure that checker won't send same mail to mail queue again
# - todo 2. make data formatter read condition and data mapping from file instead of hardcode
# #- todo - All
# - todo 1. make main config file

# | IMPORT SECTION
import base64
import os
import pickle
import shortuuid
import sys
import time

from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from multiprocessing import Process, Queue
from typing import Any, Dict, List, Union
from queue import Empty, Full

from ConfigFile import Config
from googleModule.GG import sheet_management, gmail_management
from HTMLParse import html_parse
from QR import create_qr_code

# | GLOBAL DEFINE
c = Config()
c.fromFile("sheet.cfg")

SHEET_NAME = c["Global"]["SHEET_NAME"]  # main sheet name for reading and writing status

STATUS_COL = c["Global"]["STATUS_COL"]  # status column that this program needed

# read criteria column from file
CRITERIA_COL = c["Global"]["CRITERIA_COL"]

# set up range for google sheet reading and writing
RANGE_LST = [chr(ord("A") + i) for i in range(len(STATUS_COL) + len(CRITERIA_COL))]
RANGE = f"{SHEET_NAME}!{RANGE_LST[0]}:{RANGE_LST[-1]}"


# | FUNCTION SECTION
def checker(mail_q: Queue, status_q: Queue, sheet_id: str) -> None:
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
    SHEET_SCOPES = [c["Google Api"]["SHEET_SCOPE"]]
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.path.split(sys.argv[0])[0], c["Google Api"]["SHEET_SERVICE_ACC_FILE"]
    )

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )
    s = sheet_management(sheet_id, SHEET_CREDS)

    # * mail sending wait list
    waiting_lst = []

    # * Main loop
    run = True
    while run:
        # * check status
        try:
            run = status_q.get_nowait()
        except Empty:
            pass
        else:
            if not run:
                break

        # * read all data from google sheet
        data = s.read_sheet_by_range(RANGE)
        time.sleep(1)

        # * data formatting
        val = [line + [""] * (len(RANGE_LST) - len(line)) for line in data["values"]]

        val_data_formatter_data_map = c["Checker"]["FORMATTER_DATA_MAP"]
        for k, v in val_data_formatter_data_map.copy().items():
            try:
                run = status_q.get_nowait()
            except Empty:
                pass
            else:
                if not run:
                    break
            val_data_formatter_data_map[k] = c["Checker"][v]

        val = data_formatter(
            val,
            c["Checker"]["FORMATTER_IGN_COND"],
            val_data_formatter_data_map,
        )

        # * mail sending loop
        for line in val:
            i = line[0]
            line = line[1:]
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
                for wait_mail in waiting_lst.copy():
                    try:
                        run = status_q.get_nowait()
                    except Empty:
                        pass
                    else:
                        if not run:
                            break

                    if wait_mail[0] == i and datetime.now() - wait_mail[1] >= timedelta(
                        minutes=5
                    ):
                        waiting_lst[1] = datetime.now()
                        mail_q.put_nowait("|".join([str(i)] + line))

                waiting_lst.append([i, datetime.now()])
                mail_q.put_nowait("|".join([str(i)] + line))
    print("Checker process exited")


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
    for i, line in enumerate(data):
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

        res.append([i] + line)

        if first:
            first = False

    return res


# | MAIN
if __name__ == "__main__":
    # * set terminate timer
    START = time.perf_counter()

    # * get sheet id
    sheet_id = c["Global"]["SHEET_ID"]

    # * setup queue for inter-process communication
    mail_q = Queue()
    status_q = Queue()

    # * setup checker process for reading google sheet
    checker_proc = Process(target=checker, args=(mail_q, status_q, sheet_id))

    # * start checker process
    checker_proc.start()

    # * setup google sheet api
    SHEET_SCOPES = [c["Google Api"]["SHEET_SCOPE"]]
    SERVICE_ACCOUNT_FILE = os.path.join(
        os.path.split(sys.argv[0])[0], c["Google Api"]["SHEET_SERVICE_ACC_FILE"]
    )

    SHEET_CREDS = None
    SHEET_CREDS = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SHEET_SCOPES
    )
    s = sheet_management(sheet_id, SHEET_CREDS)

    # * setup gmail api
    GMAIL_SCOPES = [c["Google Api"]["GMAIL_SCOPE"]]

    CREDENTIALS_FILENAME = os.path.join(
        os.path.split(sys.argv[0])[0], c["Google Api"]["GMAIL_CRED_FILE"]
    )
    TOKEN_FILENAME = os.path.join(
        os.path.split(sys.argv[0])[0], c["Google Api"]["GMAIL_TOKEN_FILE"]
    )

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
        if time.perf_counter() - START >= float(c["Global"]["PROGRAM_RUN_TIMER"]) * 60:
            print("Main process close by timer")
            break

        # * get mail information from checker process
        try:
            mail = mail_q.get_nowait()
            mail = mail.split("|")
            row_index = int(mail[0])
            mail = mail[1:]
        except Empty:
            continue

        # * prepare for mail sending
        for k, v in c["Global"]["CRITERIA"].items():
            exec(f"{k} = CRITERIA_COL.index('{v}')")

        # * generate code and qr code image
        uuid_code = shortuuid.uuid()
        qr_data = []

        for content in c["Mail"]["QR_CONTENT_PATTERN"]:
            if content == "uuid_code":
                qr_data.append(globals()[content])
            else:
                qr_data.append(mail[globals()[content]])

        img = create_qr_code(data=base64.b64encode("|".join(qr_data).encode("utf-8")))
        img.save(c["Mail"]["QR_IMAGE_FNAME"])

        # * send mail
        replace_var = {}
        for k, v in c["Mail"]["HTML_REPLACE_VAR"].items():
            if v == "uuid_code":
                replace_var[k] = globals()[v]
            else:
                replace_var[k] = mail[globals()[v]]

        res = g.send_mail(
            mail[globals()[c["Mail"]["ADDRESSEE"]]]
            if "@" not in c["Mail"]["ADDRESSEE"]
            else c["Mail"]["ADDRESSEE"],
            "อีเมลตอบกลับการลงทะเบียนงาน Call for Speaker",
            html_parse(
                c["Mail"]["HTML_MAIL_TEMPLATE"],
                c["Mail"]["HTML_REPLACE_PATTERN"],
                replace_var,
            ),
            c["Mail"]["HTML_ATTCH_FILE"],
        )
        print(f"Result:\n{res}\nWaiting 0.5 s")
        time.sleep(0.5)

        # * update status in google sheet (mail sent and code status)
        s.write_sheet_by_range(
            f"{SHEET_NAME}!{RANGE_LST[len(CRITERIA_COL)]}{row_index+1}:{chr(ord(RANGE_LST[len(CRITERIA_COL)])+1)}{row_index+1}",
            [["=TRUE", uuid_code]],
            "USER_ENTERED",
        )
        print("Sheet status updated\nWaiting 0.5 s")
        time.sleep(0.5)

    # * terminate checker process
    print("Closing checker process")
    while checker_proc.is_alive():
        status_q.put_nowait(False)
        checker_proc.kill()
        time.sleep(1)

    # * before exit clean up
    checker_proc.join()
    mail_q.close()
    mail_q.cancel_join_thread()
    status_q.close()
    status_q.cancel_join_thread()
    print("All Exited!")