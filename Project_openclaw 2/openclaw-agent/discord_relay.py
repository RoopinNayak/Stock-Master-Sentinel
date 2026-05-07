#!/usr/bin/env python3
import os
import time

import requests


def load_webhook_url():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("DISCORD_WEBHOOK_URL="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("DISCORD_WEBHOOK_URL", "")


def load_env_value(name):
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get(name, "")


WEBHOOK_URL = load_webhook_url()
TELEGRAM_BOT_TOKEN = load_env_value("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = load_env_value("TELEGRAM_CHAT_ID")
FEED_FILE = os.path.join(os.path.dirname(__file__), "reasoning_feed.txt")
SETTINGS_API_URL = "http://localhost:8080/api/settings"


def fetch_alert_settings():
    try:
        response = requests.get(SETTINGS_API_URL, timeout=5)
        if response.ok:
            return response.json()
    except Exception as e:
        print(f"Unable to fetch alert settings: {e}", flush=True)
    return {}


def send_to_discord(block_text, webhook_url=None):
    """Parse a reasoning block and send a rich embed to Discord."""
    lines = [line.strip() for line in block_text.split("\n") if line.strip()]
    if not lines:
        return

    is_critical = "[CRITICAL ALERT]" in block_text

    issue_text = ""
    analysis_text = ""
    action_text = ""

    for line in lines:
        if "Issue:" in line:
            issue_text = line.split("Issue:", 1)[1].strip()
        elif "Analysis:" in line:
            analysis_text = line.split("Analysis:", 1)[1].strip()
        elif "Action:" in line:
            action_text = line.split("Action:", 1)[1].strip()

    if not issue_text and not analysis_text:
        return

    color = 16711680 if is_critical else 65280
    embed = {
        "title": "CRITICAL STOCK ALERT" if is_critical else "Stock Intelligence Update",
        "color": color,
        "fields": [
            {"name": "Issue", "value": issue_text or "N/A", "inline": False},
            {"name": "AI Analysis", "value": analysis_text or "N/A", "inline": False},
            {"name": "Recommended Action", "value": action_text or "N/A", "inline": False},
        ],
        "footer": {"text": "StockMaster Sentinel - Autonomous Operations"},
    }

    try:
        response = requests.post(webhook_url or WEBHOOK_URL, json={"embeds": [embed]}, timeout=20)
        if response.status_code in (200, 204):
            print(f"Posted to Discord: {issue_text}", flush=True)
        else:
            print(
                f"Failed to post to Discord: {response.status_code} {response.text}",
                flush=True,
            )
    except Exception as e:
        print(f"Exception posting to Discord: {e}", flush=True)


def send_to_telegram(block_text, chat_id=None):
    """Send a reasoning block to Telegram when configured."""
    chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return

    lines = [line.strip() for line in block_text.split("\n") if line.strip()]
    if not lines:
        return

    issue_text = ""
    analysis_text = ""
    action_text = ""

    for line in lines:
        if "Issue:" in line:
            issue_text = line.split("Issue:", 1)[1].strip()
        elif "Analysis:" in line:
            analysis_text = line.split("Analysis:", 1)[1].strip()
        elif "Action:" in line:
            action_text = line.split("Action:", 1)[1].strip()

    if not issue_text and not analysis_text:
        return

    message = (
        "Stock Intelligence Update\n\n"
        f"Issue: {issue_text or 'N/A'}\n"
        f"Analysis: {analysis_text or 'N/A'}\n"
        f"Action: {action_text or 'N/A'}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=20,
        )
        if response.ok:
            print(f"Posted to Telegram: {issue_text}", flush=True)
        else:
            print(
                f"Failed to post to Telegram: {response.status_code} {response.text}",
                flush=True,
            )
    except Exception as e:
        print(f"Exception posting to Telegram: {e}", flush=True)


def tail_feed():
    print(f"Starting Discord Relay. Watching {FEED_FILE}...", flush=True)

    if not os.path.exists(FEED_FILE):
        open(FEED_FILE, "a", encoding="utf-8").close()

    with open(FEED_FILE, "r", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)

        current_block = []
        while True:
            current_pos = f.tell()
            line = f.readline()

            if not line:
                time.sleep(0.5)
                if os.path.getsize(FEED_FILE) < current_pos:
                    f.seek(0)
                continue

            line = line.strip()
            if "----------------------------------------" in line:
                if current_block:
                    block_text = "\n".join(current_block)
                    settings = fetch_alert_settings()
                    channel = settings.get("channel", "discord").lower()
                    destination = settings.get("channelId")

                    if channel == "discord":
                        send_to_discord(block_text, destination)
                    elif channel == "telegram":
                        send_to_telegram(block_text, destination)
                    current_block = []
            else:
                current_block.append(line)


if __name__ == "__main__":
    tail_feed()
