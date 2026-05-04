#!/usr/bin/env python3
"""
Execute Restock Skill for OpenClaw
Updates inventory when the agent receives restock commands
"""

import sys
import json
import requests
from datetime import datetime

API_URL = "http://localhost:8080/api/inventory"

def execute_restock(product_id, quantity):
    """Execute a restock operation via the API"""
    payload = {
        "productId": product_id,
        "quantity": quantity
    }

    try:
        response = requests.post(f"{API_URL}/restock",
                               json=payload,
                               headers={"Content-Type": "application/json"},
                               timeout=10)

        if response.status_code == 200:
            result = response.json()
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
    # Simple parsing for demo - in production, use NLP
    text = command_text.lower()

    # Look for patterns like "restock X units of Y" or "I have restocked X Y"
    import re

    # Pattern 1: "restock X units of Y"
    pattern1 = r"restock (\d+) units? of (.+)"
    match1 = re.search(pattern1, text)
    if match1:
        quantity = int(match1.group(1))
        product_name = match1.group(2).strip()
        return quantity, product_name

    # Pattern 2: "I have restocked X Y"
    pattern2 = r"(?:I have )?restocked (\d+) (.+)"
    match2 = re.search(pattern2, text)
    if match2:
        quantity = int(match2.group(1))
        product_name = match2.group(2).strip()
        return quantity, product_name

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

    # Parse the command
    quantity, product_name = parse_restock_command(command_text)

    if not quantity or not product_name:
        print(json.dumps({
            "status": "error",
            "message": f"Could not parse restock command: {command_text}",
            "example": "Try: 'restock 50 units of Milk' or 'I have restocked 25 Coffee Beans'"
        }))
        sys.exit(1)

    # Get product ID
    product_id = get_product_id_by_name(product_name)
    if not product_id:
        print(json.dumps({
            "status": "error",
            "message": f"Product '{product_name}' not found in inventory"
        }))
        sys.exit(1)

    # Execute restock
    result = execute_restock(product_id, quantity)

    # Add timestamp and command info
    result["timestamp"] = datetime.now().isoformat()
    result["command"] = command_text
    result["parsed"] = {
        "product_name": product_name,
        "product_id": product_id,
        "quantity": quantity
    }

    # Output result
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()