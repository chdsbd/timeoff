import json
import os
import urllib
from pathlib import Path
from time import time
from typing import List, Optional

import click
import slack
from dotenv import load_dotenv
from flask import Flask, request
from timeoff.pdf_generation import write_fillable_pdf

load_dotenv()

SLACK_TOKEN = os.environ["SLACK_TOKEN"]
ADMITHUB_VACATION_CALENDAR = os.environ["ADMITHUB_VACATION_CALENDAR"]
PORT = int(os.getenv("PORT", 5555))

client = slack.WebClient(token=SLACK_TOKEN)

app = Flask(__name__)


@app.route("/")
def root():
    return "OK"


def get_dialog(fullname: str) -> dict:
    return {
        "callback_id": "46eh782b0",
        "title": "Request time off",
        "submit_label": "Create",
        "elements": [
            {
                "type": "text",
                "label": "Name",
                "placeholder": "Full Name",
                "value": fullname,
                "hint": "Enter your name (e.g. Dolores Abernathy)",
                "name": "employee_name",
            },
            {
                "type": "text",
                "label": "Time off date(s)",
                "placeholder": "Date(s)",
                "hint": "Specify date(s) to take off (e.g. August 17th - September 10th).",
                "name": "employee_requested_dates",
            },
            {
                "type": "text",
                "label": "Signature",
                "placeholder": "Signature",
                "hint": "Write something unique to act as a signature (e.g. ~~Deloris).",
                "name": "employee_signature",
            },
        ],
    }


def get_calender_reminder_blocks(fullname: str) -> List[dict]:
    title = urllib.parse.quote_plus(fullname + " Time Off")
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                # Google Calendar template link information: https://stackoverflow.com/a/23495015
                # Here we create a link that fills in an event with a title and
                # calendar set to the admithub vacation calendar
                "text": f"Make sure to add the vacation time to the *<https://calendar.google.com/calendar/r/eventedit?text={title}&src={ADMITHUB_VACATION_CALENDAR}|vacation calendar>*.",
            },
        }
    ]


@app.route("/slack/<request_kind>", methods=["POST"])
def slack_handler(request_kind: Optional[str] = None):
    if request_kind == "slash-command":
        res = client.users_profile_get(user=request.form["user_id"])
        real_name = res["profile"]["real_name"]
        client.dialog_open(
            dialog=get_dialog(real_name), trigger_id=request.form["trigger_id"]
        )
    if request_kind == "interaction":
        payload: dict = json.loads(request.form["payload"])
        response_url = payload["response_url"]
        channel_id = payload["channel"]["id"]
        user_id = payload["user"]["id"]
        submission = payload["submission"]
        employee_name = submission["employee_name"]
        employee_signature = submission["employee_signature"]
        employee_requested_dates = submission["employee_requested_dates"]

        # run PDF generation in thread pool for good measure
        path = write_fillable_pdf(
            "form.pdf", employee_name, employee_signature, employee_requested_dates
        )

        filename = f"Time off request for {employee_name}.pdf"
        res = client.files_upload(
            file=path,
            filename=filename,
            channels=channel_id,
            initial_comment="Here's a request for time off.",
        )

        # send reminder about updating vacation calendar
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=get_calender_reminder_blocks(employee_name),
        )

    return ""


if __name__ == "__main__":
    app.run(port=PORT)
