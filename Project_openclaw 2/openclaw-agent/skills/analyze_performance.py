#!/usr/bin/env python3
"""
Business Intelligence Skill: Analyze Performance
Analyzes audit logs to provide business insights and recommendations
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import statistics

API_URL = "http://localhost:8080/api/inventory"

def get_audit_logs():
    """Fetch audit logs from database (simulated for demo)"""
    # In a real implementation, this would query the audit_logs table
    # For demo purposes, we'll simulate some audit data
    return [
        {"product_id": 2, "action": "Restock", "quantity": 25, "timestamp": "2026-05-01T10:00:00"},
        {"product_id": 2, "action": "Sale", "quantity": -5, "timestamp": "2026-05-01T14:00:00"},
        {"product_id": 2, "action": "Sale", "quantity": -3, "timestamp": "2026-05-02T09:00:00"},
        {"product_id": 1, "action": "Sale", "quantity": -2, "timestamp": "2026-05-01T11:00:00"},
        {"product_id": 1, "action": "Sale", "quantity": -4, "timestamp": "2026-05-02T10:00:00"},
        {"product_id": 2, "action": "Sale", "quantity": -7, "timestamp": "2026-05-02T15:00:00"},
    ]

def get_product_info(product_id):
    """Get product information"""
    try:
        response = requests.get(f"{API_URL}/products/{product_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def analyze_product_performance(product_id, audit_logs):
    """Analyze performance for a specific product"""
    product_logs = [log for log in audit_logs if log['product_id'] == product_id]
    product_info = get_product_info(product_id)

    if not product_info:
        return None

    # Calculate weekly sales (simplified)
    now = datetime.now()
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    this_week_sales = []
    last_week_sales = []

    for log in product_logs:
        log_time = datetime.fromisoformat(log['timestamp'])
        if log['action'] == 'Sale' and log['quantity'] < 0:  # Sale quantities are negative
            sale_quantity = abs(log['quantity'])
            if log_time >= week_ago:
                this_week_sales.append(sale_quantity)
            elif week_ago > log_time >= two_weeks_ago:
                last_week_sales.append(sale_quantity)

    this_week_total = sum(this_week_sales)
    last_week_total = sum(last_week_sales)

    # Calculate percentage change
    if last_week_total > 0:
        percent_change = ((this_week_total - last_week_total) / last_week_total) * 100
    else:
        percent_change = 0 if this_week_total == 0 else 100

    # Generate insights
    insights = {
        "product_name": product_info['name'],
        "product_id": product_id,
        "current_stock": product_info['quantity'],
        "threshold": product_info['threshold'],
        "this_week_sales": this_week_total,
        "last_week_sales": last_week_total,
        "percent_change": percent_change,
        "recommendations": []
    }

    # Generate recommendations
    if percent_change > 20:
        new_threshold = int(product_info['threshold'] * 1.3)  # Increase threshold by 30%
        insights["recommendations"].append(
            f"🚀 Sales increased by {percent_change:.1f}%. Consider increasing threshold from {product_info['threshold']} to {new_threshold} to avoid stockouts."
        )
    elif percent_change < -20:
        new_threshold = int(product_info['threshold'] * 0.8)  # Decrease threshold by 20%
        insights["recommendations"].append(
            f"📉 Sales decreased by {abs(percent_change):.1f}%. Consider lowering threshold to {new_threshold} to reduce overstock."
        )

    # Stock level analysis
    stock_ratio = product_info['quantity'] / product_info['threshold']
    if stock_ratio < 0.5:
        insights["recommendations"].append(
            f"⚠️ Stock level is critically low ({stock_ratio:.1f}x threshold). Immediate restock recommended."
        )
    elif stock_ratio > 2.0:
        insights["recommendations"].append(
            f"📦 Overstock detected ({stock_ratio:.1f}x threshold). Consider promotional activities."
        )

    return insights

def generate_business_intelligence_report():
    """Generate comprehensive business intelligence report"""
    audit_logs = get_audit_logs()

    # Get all products
    try:
        response = requests.get(f"{API_URL}/products", timeout=5)
        if response.status_code == 200:
            products = response.json()
        else:
            return {"error": "Could not fetch product data"}
    except Exception as e:
        return {"error": f"Connection error: {e}"}

    report = {
        "timestamp": datetime.now().isoformat(),
        "analysis_period": "Last 2 weeks",
        "products_analyzed": len(products),
        "insights": []
    }

    for product in products:
        analysis = analyze_product_performance(product['id'], audit_logs)
        if analysis:
            report["insights"].append(analysis)

    # Sort by most significant changes
    report["insights"].sort(key=lambda x: abs(x.get('percent_change', 0)), reverse=True)

    return report

def main():
    if len(sys.argv) > 1:
        # Analyze specific product
        try:
            product_id = int(sys.argv[1])
            audit_logs = get_audit_logs()
            analysis = analyze_product_performance(product_id, audit_logs)
            if analysis:
                print(json.dumps(analysis, indent=2))
            else:
                print(json.dumps({"error": f"Could not analyze product {product_id}"}))
        except ValueError:
            print(json.dumps({"error": "Invalid product ID"}))
    else:
        # Generate full report
        report = generate_business_intelligence_report()
        print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()