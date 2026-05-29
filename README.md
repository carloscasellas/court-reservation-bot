# Court Reservation Bot

Automated Playwright bot that reserves a tennis court 8 days in advance on a daily schedule.

## How it works

The bot runs every day at **12:30 PM PST** via a cron job on an EC2 instance. It launches a Chromium browser, logs into the reservation site, navigates to the date 8 days out, and attempts to book a 1.5-hour court slot ($18) at the earliest available PM time:

- 7:00 PM → 8:30 PM
- 7:30 PM → 9:00 PM
- 8:00 PM → 9:30 PM
- 8:30 PM → 10:00 PM

It tries each time slot in order and stops as soon as one succeeds. The bot runs twice per cron execution (`instructions.sh` calls the script back-to-back) to improve the chance of securing a slot if the first attempt fails.

## Debugging

Every run is recorded as a video (1280×720) saved to the `videos/` directory and uploaded to the S3 bucket `goldman-bot-video-retrieval` with a **90-day TTL**. Logs are written to `log/instructions.log` and cleared at the start of each run.

## Infrastructure

- **Host:** AWS EC2 instance
- **Schedule:** Cron job at 12:30 PM daily
- **Video storage:** S3 (`goldman-bot-video-retrieval`), 90-day TTL
- **Runtime:** Python + Playwright (Chromium)

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Copy `.env.example` to `.env` and fill in your credentials before running.

## Running manually

```bash
bash instructions.sh
```
