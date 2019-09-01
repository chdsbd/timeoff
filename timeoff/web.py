import asyncio
import json
import os
import urllib
from pathlib import Path
from time import time
from typing import List, Optional

import aiohttp
import click
import slack
from aiohttp import web
from dotenv import load_dotenv

from timeoff.pdf_generation import write_fillable_pdf

load_dotenv()

SLACK_TOKEN = os.environ["SLACK_TOKEN"]
ADMITHUB_VACATION_CALENDAR = os.environ["ADMITHUB_VACATION_CALENDAR"]
PORT = int(os.getenv("PORT", 5555))

client = slack.WebClient(token=SLACK_TOKEN, run_async=True)


async def root(request: web.Request) -> web.Response:
    return web.json_response({"status": "OK"})


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


async def slack_handler(request: web.Request) -> web.Response:
    request_kind: Optional[str] = request.match_info.get("request_kind", None)
    if request_kind == "slash-command":
        data = await request.post()
        res = await client.users_profile_get(user=data["user_id"])
        real_name = res["profile"]["real_name"]
        await client.dialog_open(
            dialog=get_dialog(real_name), trigger_id=data["trigger_id"]
        )
    if request_kind == "interaction":
        data = await request.post()
        assert not isinstance(data["payload"], web.FileField)
        payload: dict = json.loads(data["payload"])
        response_url = payload["response_url"]
        channel_id = payload["channel"]["id"]
        user_id = payload["user"]["id"]
        submission = payload["submission"]
        employee_name = submission["employee_name"]
        employee_signature = submission["employee_signature"]
        employee_requested_dates = submission["employee_requested_dates"]

        # run PDF generation in thread pool for good measure
        path = await asyncio.get_event_loop().run_in_executor(
            None,
            write_fillable_pdf,
            "form.pdf",
            employee_name,
            employee_signature,
            employee_requested_dates,
        )

        filename = f"Time off request for {employee_name}.pdf"
        res = await client.files_upload(
            file=path,
            filename=filename,
            channels=channel_id,
            initial_comment="Here's a request for time off.",
        )

        # send reminder about updating vacation calendar
        await client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            blocks=get_calender_reminder_blocks(employee_name),
        )

    return web.Response()


app = web.Application()
app.add_routes([web.get("/", root), web.post("/slack/{request_kind}", slack_handler)])


if __name__ == "__main__":
    web.run_app(app, port=PORT)
