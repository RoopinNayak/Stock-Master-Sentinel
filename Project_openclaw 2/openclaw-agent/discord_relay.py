#!/usr/bin/env python3
import os
import time
import requests
import json

def load_webhook_url():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("DISCORD_WEBHOOK_URL="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("DISCORD_WEBHOOK_URL", "")

WEBHOOK_URL = load_webhook_url()
FEED_FILE = os.path.join(os.path.dirname(__file__), "reasoning_feed.txt")

def send_to_discord(block_text):
    """Parses a reasoning block and sends a rich embed to Discord."""
    lines = [line.strip() for line in block_text.split('\n') if line.strip()]
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
        return # Not a structured block
        
    color = 16711680 if is_critical else 65280 # Red if critical, Green otherwise (0xFF0000 / 0x00FF00)
    
    embed = {
        "title": "🚨 CRITICAL STOCK ALERT" if is_critical else "📊 Stock Intelligence Update",
        "color": color,
        "fields": [
            {
                "name": "📌 Issue",
                "value": issue_text or "N/A",
                "inline": False
            },
            {
                "name": "🧠 AI Analysis",
                "value": analysis_text or "N/A",
                "inline": False
            },
            {
                "name": "⚡ Recommended Action",
                "value": action_text or "N/A",
                "inline": False
            }
        ],
        "footer": {
            "text": "StockMaster Sentinel - Autonomous Operations"
        }
    }
    
    payload = {
        "embeds": [embed]
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        if response.status_code in (200, 204):
            print(f"✅ Posted to Discord: {issue_text}")
        else:
            print(f"❌ Failed to post to Discord: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Exception posting to Discord: {e}")

def tail_feed():
    print(f"Starting Discord Relay. Watching {FEED_FILE}...")
    
    # Ensure file exists
    if not os.path.exists(FEED_FILE):
        open(FEED_FILE, 'a').close()
        
    with open(FEED_FILE, "r") as f:
        # Seek to the end of the file so we only get new alerts
        f.seek(0, os.SEEK_END)
        
        current_block = []
        while True:
            current_pos = f.tell()
            line = f.readline()
            
            if not line:
                time.sleep(0.5)
                # Check for truncation
                if os.path.getsize(FEED_FILE) < current_pos:
                    f.seek(0)
                continue
                
            line = line.strip()
            if "----------------------------------------" in line:
                if current_block:
                    block_text = "\n".join(current_block)
                    send_to_discord(block_text)
                    current_block = []
            else:
                current_block.append(line)

if __name__ == "__main__":
    tail_feed()
