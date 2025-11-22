import re

def estimate_rate(details):
    """
    NITISARA Professional Rate Engine
    - Uses real distances provided by LLM Intelligence.
    """
    origin = details.get('origin', 'Unknown')
    destination = details.get('destination', 'Unknown')
    cargo_desc = details.get('cargo', 'General cargo')
    
    # 1. Get Precision Data
    weight = float(details.get('weight', 500))
    
    # ✅ USE REAL DISTANCE (with fallback just in case)
    distance_km = details.get('distance_km')
    if not distance_km:
        distance_km = 5000 # Should ideally not happen with new Agent logic

    # 2. Calculate Totals
    # Sea Rates
    base_sea = 15000
    sea_cost = base_sea + (weight * 25) + (distance_km * 1.2)
    sea_fast = sea_cost * 1.15
    
    # Air Rates
    base_air = 45000
    air_cost = base_air + (weight * 180) + (distance_km * 4.5)

    # Emissions
    co2_sea = (weight * distance_km * 0.000015) / 1000 # tonnes
    co2_air = (weight * distance_km * 0.000285) / 1000 # tonnes

    route = f"{origin} → {destination}"
    
    return f"""
🚢 **Quote: {route}**
📏 **Logistics Distance:** {distance_km:,} km

📊 **Options:**
________________________________________________________
🌊 **Economy Sea** | ₹{sea_cost:,.0f} | {co2_sea:.2f}t CO₂e
⚡ **Express Sea** | ₹{sea_fast:,.0f} | {co2_sea:.2f}t CO₂e
✈️ **Air Freight** | ₹{air_cost:,.0f} | {co2_air:.2f}t CO₂e
________________________________________________________

💡 **Professional Insight:**
Rates calculated based on specific route distance ({distance_km}km) and cargo weight ({weight}kg).
"""