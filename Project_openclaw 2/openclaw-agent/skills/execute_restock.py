#!/usr/bin/env python3
"""
Execute Restock Skill for OpenClaw
Updates inventory when the agent receives restock commands
"""

import sys
import json
import requests
import subprocess
import os
from datetime import datetime

API_URL = "http://localhost:8080/api/inventory"


def execute_restock(product_id, quantity):
    """Execute a restock operation via the API"""
    payload = {
        "productId": product_id,
        "quantity": quantity
    }

    try:
        response = requests.post(
            f"{API_URL}/restock",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()

            # 🔥 SEND DISCORD NOTIFICATION AFTER SUCCESS
            try:
                subprocess.run([
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), "notifier.py"),
                    result['name'],
                    str(result['quantity']),
                    str(result.get('threshold', 10)),
                    "normal"
                ], timeout=5)
            except Exception as e:
                print("Notification error:", e)

            return {
                "status": "success",
                "product": result,
                "message": f"Successfully restocked {quantity} units of {result['name']}"
            }

        else:
            return {
                "status": "error",
                "code": response.status_code,
                "message": f"API error: {response.text}"
            }

    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": f"Connection error: {str(e)}"
        }


def parse_restock_command(command_text):
    """Parse natural language restock commands"""
    text = command_text.lower()
    import re

    pattern1 = r"restock (\d+) units? of (.+)"
    match1 = re.search(pattern1, text)
    if match1:
        return int(match1.group(1)), match1.group(2).strip()

    pattern2 = r"(?:I have )?restocked (\d+) (.+)"
    match2 = re.search(pattern2, text)
    if match2:
        return int(match2.group(1)), match2.group(2).strip()

    return None, None


def get_product_id_by_name(product_name):
    """Get product ID by name from the API"""
    try:
        response = requests.get(f"{API_URL}/products", timeout=5)
        if response.status_code == 200:
            products = response.json()
            for product in products:
                if product['name'].lower() == product_name.lower():
                    return product['id']
        return None
    except Exception as e:
        print(f"Error getting product ID: {e}")
        return None


def main():
    """Main entry point for the execute_restock skill"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python3 execute_restock.py <command_text>"
        }))
        sys.exit(1)

    command_text = " ".join(sys.argv[1:])

    quantity, product_name = parse_restock_command(command_text)

    if not quantity or not product_name:
        print(json.dumps({
            "status": "error",
            "message": f"Could not parse restock command: {command_text}",
            "example": "Try: 'restock 50 units of Milk'"
        }))
        sys.exit(1)

    product_id = get_product_id_by_name(product_name)
    if not product_id:
        print(json.dumps({
            "status": "error",
            "message": f"Product '{product_name}' not found"
        }))
        sys.exit(1)

    result = execute_restock(product_id, quantity)

    result["timestamp"] = datetime.now().isoformat()
    result["command"] = command_text
    result["parsed"] = {
        "product_name": product_name,
        "product_id": product_id,
        "quantity": quantity
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()