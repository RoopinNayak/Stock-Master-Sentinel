#!/usr/bin/env python3
"""
Notifier Skill for OpenClaw
Sends alerts via Discord webhook or similar
"""

import sys
import json
import os
import requests
from datetime import datetime

# Configuration
# In production, use environment variables
DISCORD_WEBHOOK_URL = None  # Set your Discord webhook URL here
ENABLE_DISCORD = False
ENABLE_CONSOLE = True  # Always enable console output for demo
SETTINGS_API_URL = "http://localhost:8080/api/settings"


def fetch_owner_settings():
    """Fetch store owner alert routing settings from the backend."""
    try:
        response = requests.get(SETTINGS_API_URL, timeout=8)
        if response.ok:
            return response.json()
        return {}
    except Exception:
        return {}


def send_discord_alert(message, product_name, quantity, threshold, priority="normal"):
    """Send alert via Discord webhook"""
    if not DISCORD_WEBHOOK_URL or not ENABLE_DISCORD:
        return {"status": "skipped", "reason": "Discord not configured"}
    
    # Create Discord embed
    embed = {
        "title": f"⚠️ Low Stock Alert: {product_name}",
        "color": 16711680 if priority == "urgent" else 16776960,  # Red for urgent, Yellow for normal
        "fields": [
            {
                "name": "Current Quantity",
                "value": str(quantity),
                "inline": True
            },
            {
                "name": "Threshold",
                "value": str(threshold),
                "inline": True
            },
            {
                "name": "Priority",
                "value": priority.upper(),
                "inline": True
            },
            {
                "name": "Quick Action",
                "value": "[Click to Restock](http://localhost:3000)"
            }
        ],
        "footer": {
            "text": "StockMaster Sentinel - AI Operations Manager"
        },
        "timestamp": datetime.now().isoformat()
    }
    
    payload = {
        "content": message,
        "embeds": [embed]
    }
    
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        if response.status_code == 204:
            return {"status": "success", "method": "discord"}
        else:
            return {"status": "error", "code": response.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def send_console_alert(message, product_name, quantity, threshold, priority="normal"):
    """Send alert to console (demo mode)"""
    print("\n" + "=" * 60)
    print("📱 NOTIFICATION SENT")
    print("=" * 60)
    print(f"Product: {product_name}")
    print(f"Quantity: {quantity} (Threshold: {threshold})")
    print(f"Priority: {priority.upper()}")
    print(f"Message: {message}")
    print("-" * 60)
    print("Quick Action: [Click to approve restock]")
    print("=" * 60 + "\n")
    
    return {"status": "success", "method": "console"}

def format_message(product_name, quantity, threshold, market_data=None):
    """Format the alert message"""
    shortage = quantity
    needed = threshold - quantity
    
    message = f"🚨 **{product_name}** is running low!\n"
    message += f"Current stock: **{shortage}** units (Min: {threshold})\n"
    message += f"Need to restock: **{needed}** units\n"
    
    if market_data:
        if market_data.get("shortage_risk") == "high":
            message += f"\n⚠️ Market Alert: {market_data.get('summary', '')}"
        else:
            message += f"\n📊 Market: {market_data.get('summary', '')}"
    
    return message

def main():
    """Main entry point for the notifier skill"""
    if len(sys.argv) < 4:
        print(json.dumps({
            "error": "Usage: python3 notifier.py <product_name> <quantity> <threshold> [priority]"
        }))
        sys.exit(1)
    
    product_name = sys.argv[1]
    quantity = int(sys.argv[2])
    threshold = int(sys.argv[3])
    priority = sys.argv[4] if len(sys.argv) > 4 else "normal"
    
    # Parse optional market data from environment
    market_data = None
    if os.getenv("MARKET_DATA"):
        market_data = json.loads(os.getenv("MARKET_DATA", "{}"))
    
    # Format message
    message = format_message(product_name, quantity, threshold, market_data)
    
    # Fetch owner settings to determine alert routing
    settings = fetch_owner_settings()
    channel = settings.get("channel", "console").lower()
    destination = settings.get("channelId") or settings.get("owner") or "owner"
    results = []

    if channel == "discord" and settings.get("channelId"):
        global DISCORD_WEBHOOK_URL
        DISCORD_WEBHOOK_URL = settings.get("channelId")

    if channel == "whatsapp":
        results.append({
            "status": "simulated",
            "method": "whatsapp",
            "destination": destination,
            "note": "WhatsApp routing is simulated in demo mode."
        })
        if ENABLE_CONSOLE:
            send_console_alert(message, product_name, quantity, threshold, priority)
    elif channel == "discord":
        if ENABLE_DISCORD:
            result = send_discord_alert(message, product_name, quantity, threshold, priority)
            results.append(result)
        else:
            results.append({
                "status": "skipped",
                "method": "discord",
                "reason": "Discord not enabled in local config"
            })
            if ENABLE_CONSOLE:
                send_console_alert(message, product_name, quantity, threshold, priority)
    else:
        result = send_console_alert(message, product_name, quantity, threshold, priority)
        results.append(result)
    
    # Output result
    output = {
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "product": product_name,
        "message": message,
        "notifications": results
    }
    
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()