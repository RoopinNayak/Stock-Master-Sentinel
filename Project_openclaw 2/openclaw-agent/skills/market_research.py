#!/usr/bin/env python3
"""
Market Research Skill for OpenClaw
Checks external market conditions for inventory items
"""

import sys
import json
import random
from datetime import datetime

# Mock market data for hackathon demo
# In production, this would call real APIs (Google Trends, commodity prices, news)
MARKET_DATA = {
    "coffee": {
        "trend": "rising",
        "price_change": "+15%",
        "shortage_risk": "high",
        "reason": "Brazil drought affecting coffee bean supply"
    },
    "milk": {
        "trend": "stable",
        "price_change": "+3%",
        "shortage_risk": "medium",
        "reason": "Seasonal demand increase, dairy strike possible"
    },
    "sugar": {
        "trend": "rising",
        "price_change": "+8%",
        "shortage_risk": "low",
        "reason": "Global sugar shortage due to climate issues"
    },
    "tea": {
        "trend": "stable",
        "price_change": "+2%",
        "shortage_risk": "low",
        "reason": "Steady supply from Indian plantations"
    },
    "cups": {
        "trend": "falling",
        "price_change": "-5%",
        "shortage_risk": "low",
        "reason": "Overcapacity in plastic manufacturing"
    }
}

def get_market_data(product_name):
    """Get market data for a product"""
    product_lower = product_name.lower()
    
    # Check for keyword matches
    for key, data in MARKET_DATA.items():
        if key in product_lower:
            return data
    
    # Default response for unknown products
    return {
        "trend": "stable",
        "price_change": "0%",
        "shortage_risk": "unknown",
        "reason": "No market data available"
    }

def generate_summary(product_name, market_data):
    """Generate a 1-sentence market intelligence summary"""
    risk = market_data["shortage_risk"]
    trend = market_data["trend"]
    change = market_data["price_change"]
    reason = market_data["reason"]
    
    if risk == "high":
        return f"⚠️ URGENT: {product_name} has {risk} shortage risk with {trend} prices ({change}) due to {reason}."
    elif risk == "medium":
        return f"⚡ {product_name} market shows {trend} trend ({change}) - {reason}."
    else:
        return f"✓ {product_name} market is stable ({change}) - {reason}."

def main():
    """Main entry point for the skill"""
    # Get product name from command line argument
    if len(sys.argv) < 2:
        print(json.dumps({
            "error": "Usage: python3 market_research.py <product_name>"
        }))
        sys.exit(1)
    
    product_name = sys.argv[1]
    
    # Get market data
    market_data = get_market_data(product_name)
    
    # Generate summary
    summary = generate_summary(product_name, market_data)
    
    # Create result JSON
    result = {
        "product": product_name,
        "timestamp": datetime.now().isoformat(),
        "market_data": market_data,
        "summary": summary
    }
    
    # Output as JSON
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()