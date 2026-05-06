#!/usr/bin/env python3
"""
StockMaster Sentinel Agent
Simulates an AI agent that monitors inventory via heartbeat
"""

import requests
import json
import time
from datetime import datetime
import subprocess
import sys
import os
import argparse

API_URL = "http://localhost:8080/api/inventory"
AGENT_CONTEXT_URL = "http://localhost:8080/api/inventory/agent/context"
CHECK_INTERVAL = 60  # seconds
DEMO_MODE = False  # Set to True for demo presentations
SYSTEM_HEALTHY = True

def check_api_health():
    """Check if the API is responding"""
    try:
        response = requests.get(f"{API_URL}/products", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def notify_system_health_alert(message):
    """Send system health alert via notifier skill"""
    try:
        result = subprocess.run([
            sys.executable,
            os.path.join(os.path.dirname(__file__), "skills", "notifier.py"),
            product['name'],
            str(product['quantity']),
            str(product['threshold']),
            "urgent" if product['quantity'] < product['threshold'] / 2 else "normal"
        ], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ System health alert sent")
        else:
            print(f"❌ Failed to send health alert: {result.stderr}")
    except Exception as e:
        print(f"❌ Error sending health alert: {e}")

def get_agent_context(retry=False):
    """Get context with error handling and retry mechanism"""
    global SYSTEM_HEALTHY
    try:
        response = requests.get(AGENT_CONTEXT_URL, timeout=5)
        if response.status_code == 200:
            if not SYSTEM_HEALTHY:
                SYSTEM_HEALTHY = True
                notify_system_health_alert("✅ System Health Restored: Nervous System back online")
            return response.json()
        elif response.status_code >= 500:
            if not retry:
                time.sleep(1)
                return get_agent_context(retry=True)
            if SYSTEM_HEALTHY:
                SYSTEM_HEALTHY = False
                notify_system_health_alert("🚨 System Health Alert: Nervous System offline - API returning 500 errors")
                log_reasoning_feed("Backend Offline")
            return None
        else:
            print(f"Warning: API returned status {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        if not retry:
            time.sleep(1)
            return get_agent_context(retry=True)
        if SYSTEM_HEALTHY:
            SYSTEM_HEALTHY = False
            notify_system_health_alert("🚨 System Health Alert: Nervous System offline - Connection failed")
            log_reasoning_feed("Backend Offline")
        print(f"Error connecting to API: {e}")
        return None

def check_all_products():
    """Get all products with error handling"""
    try:
        response = requests.get(f"{API_URL}/products", timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return []

def log_audit(product_id, action):
    """Log audit entry (simulated)"""
    timestamp = datetime.now().isoformat()
    print(f"[{timestamp}] AUDIT: Product {product_id} - {action}")

def format_alert(products):
    """Format low-stock alert message"""
    if not products:
        return "✅ All stock levels are normal"
    
    message = "⚠️ **LOW STOCK ALERT**\n\n"
    for p in products:
        urgency = "🔴" if p['quantity'] < p['threshold'] / 2 else "🟡"
        message += f"{urgency} **{p['name']}** (ID: {p['id']})\n"
        message += f"   Quantity: {p['quantity']} | Threshold: {p['threshold']}\n"
        message += f"   Price: ${p['price']:.2f}\n\n"
    
    return message

def log_reasoning_feed(message):
    """Log agent's thoughts to reasoning feed"""
    try:
        timestamp = datetime.now().isoformat()
        feed_entry = f"[{timestamp}] {message}\n"
        
        with open(os.path.join(os.path.dirname(__file__), "reasoning_feed.txt"), "a") as f:
            f.write(feed_entry)
        
        # Keep only last 20 entries
        with open(os.path.join(os.path.dirname(__file__), "reasoning_feed.txt"), "r") as f:
            lines = f.readlines()
        
        if len(lines) > 20:
            with open(os.path.join(os.path.dirname(__file__), "reasoning_feed.txt"), "w") as f:
                f.writelines(lines[-20:])
                
    except Exception as e:
        print(f"Error logging reasoning: {e}")

def heartbeat():
    """Main heartbeat loop with self-healing capabilities"""
    # Demo mode check
    demo_interval = 10 if DEMO_MODE else CHECK_INTERVAL
    
    print("=" * 50)
    print("StockMaster Sentinel Agent Started")
    print(f"API: {API_URL}")
    print(f"Check Interval: {demo_interval} seconds")
    if DEMO_MODE:
        print("🎭 DEMO MODE ACTIVE - Accelerated heartbeat for presentations")
    print("=" * 50)
    
    iteration = 1
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] Heartbeat #{iteration}")
        
        # Check API health first
        api_healthy = check_api_health()
        if not api_healthy:
            log_reasoning_feed("🔍 Scanning system health... API connection issues detected")
        else:
            log_reasoning_feed("🔍 Scanning inventory levels and market conditions...")
        
        # Check context
        context = get_agent_context()
        if context:
            low_stock = context.get('lowStock', [])
            audit_logs = context.get('auditLogs', [])
            
            print(f"Low stock items: {len(low_stock)}")
            
            # Display alert
            alert = format_alert(low_stock)
            print(alert)
            
            # Process low-stock items with intelligence
            if low_stock:
                log_reasoning_feed(f"📊 Analyzing {len(low_stock)} low-stock items for market intelligence...")
                for product in low_stock:
                    # Look at audit logs for context
                    relevant_logs = [log for log in audit_logs if str(product['id']) in log]
                    reason = "Unknown"
                    if relevant_logs:
                        last_log = relevant_logs[-1]
                        if "Missing Shipment" in last_log:
                            reason = "Missing Shipment"
                        elif "Damage" in last_log:
                            reason = "Damage"
                        elif "High Sales" in last_log:
                            reason = "High Sales"
                        else:
                            reason = "Gradual Depletion"
                    
                    # Call market research skill
                    market_data = {}
                    try:
                        result = subprocess.run([
                            sys.executable,
                            os.path.join(os.path.dirname(__file__), "skills", "market_research.py"),
                            product['name']
                        ], capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            market_data = json.loads(result.stdout)
                    except Exception as e:
                        print(f"Error getting market research: {e}")
                    
                    # Formatting output
                    is_critical = product['quantity'] < product['threshold'] / 2
                    critical_prefix = "[CRITICAL ALERT]\n" if is_critical else ""
                    
                    analysis = f"Audit logs indicate '{reason}'. "
                    if 'market_data' in market_data:
                        md = market_data['market_data']
                        analysis += f"Market data shows {md.get('shortage_risk')} shortage risk with {md.get('trend')} prices due to {md.get('reason')}."
                    
                    whatsapp_msg = f"Hi Team, our {product['name']} stock is at {product['quantity']}. "
                    if 'market_data' in market_data and market_data['market_data'].get('trend') == 'rising':
                        whatsapp_msg += "Noticing rising market prices. Can we lock in a bulk order soon?"
                    else:
                        whatsapp_msg += "Please expedite the next shipment."
                    
                    reasoning_output = (
                        f"{critical_prefix}"
                        f"Issue: {product['name']} is at {product['quantity']}.\n"
                        f"Analysis: {analysis}\n"
                        f"Action: {whatsapp_msg}\n"
                        f"----------------------------------------"
                    )
                    log_reasoning_feed(reasoning_output)
                    
                    # Send notification
                    try:
                        subprocess.run([
                            sys.executable,
                            os.path.join(os.path.dirname(__file__), "skills", "notifier.py"),
                            f"Low stock alert: {product['name']} at {product['quantity']} units"
                        ], capture_output=True, text=True, timeout=10)
                    except Exception as e:
                        print(f"Error sending notification: {e}")
            else:
                log_reasoning_feed("✅ All inventory levels within acceptable ranges")
        
        # Run business intelligence analysis every 3 heartbeats
        if iteration % 3 == 0:
            log_reasoning_feed("🧠 Running business intelligence analysis...")
            try:
                result = subprocess.run([
                    sys.executable,
                    os.path.join(os.path.dirname(__file__), "skills", "analyze_performance.py")
                ], capture_output=True, text=True, timeout=15)
                if result.returncode == 0:
                    bi_data = json.loads(result.stdout)
                    top_insight = bi_data["insights"][0] if bi_data["insights"] else None
                    if top_insight and top_insight["recommendations"]:
                        log_reasoning_feed(f"💡 BI Insight: {top_insight['product_name']} - {top_insight['recommendations'][0]}")
                    else:
                        log_reasoning_feed("📊 Business intelligence analysis complete - no critical insights")
                else:
                    print(f"Error running BI analysis: {result.stderr}")
            except Exception as e:
                print(f"Error in BI analysis: {e}")
        
        iteration += 1
        time.sleep(demo_interval)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='StockMaster Sentinel Agent')
    parser.add_argument('--demo', action='store_true', help='Enable demo mode (10-second heartbeat)')
    args = parser.parse_args()
    
    # Set demo mode from command line
    if args.demo:
        DEMO_MODE = True
    
    try:
        heartbeat()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")