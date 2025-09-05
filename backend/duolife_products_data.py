"""
DUOLIFE Product Catalog Data
Extracted from DUOLIFE Ingredients.xlsx - Products sheet
First 5 products for Voice Agent Product Showcase Tool
"""

from typing import List, Dict

# Product data extracted from Excel
DUOLIFE_PRODUCTS = [
    {
        "id": "D1",
        "name": "DuoLife Day and Night",
        "category": "Dietary Supplement",
        "price": "29$",
        "type": "Set",
        "description": "100% natural dietary supplements, created for people wishing to stay in a good physical and mental shape. This comprehensive set provides complete daily nutrition support.",
        "health_effects": "Supports antioxidant processes, immune function, gastrointestinal and liver health, cardiovascular function",
        "key_features": [
            "100% natural ingredients",
            "Day and night formula optimization", 
            "Complete daily nutrition support",
            "Antioxidant protection",
            "Immune system boost"
        ],
        "intended_use": "Daily dietary supplementation for overall health and wellness",
        "image": "duolife_day_night.jpg"
    },
    {
        "id": "D2", 
        "name": "DuoLife Vita C",
        "category": "Dietary Supplement",
        "price": "39$",
        "type": "Liquid",
        "description": "A 100% natural, complete vitamin C that meets the needs of people searching for a product improving their immunity and overall health condition.",
        "health_effects": "Supports antioxidant processes, immune function, collagen synthesis, connective tissue health, skin health",
        "key_features": [
            "100% natural vitamin C",
            "Enhanced bioavailability",
            "Liquid formulation for better absorption",
            "Collagen synthesis support",
            "Immune system strengthening"
        ],
        "intended_use": "Daily vitamin C supplementation for immune support and collagen health",
        "image": "duolife_vita_c.jpg"
    },
    {
        "id": "D3",
        "name": "DuoLife Collagen", 
        "category": "Dietary Supplement",
        "price": "55$",
        "type": "Liquid",
        "description": "100% natural dietary supplement, intended for people wishing to be 'forever young'. A unique composition supporting skin, joint, and bone health.",
        "health_effects": "Supports antioxidant processes, bone and joint health, articular cartilage function, collagen synthesis",
        "key_features": [
            "Premium collagen formula",
            "Anti-aging properties",
            "Joint and bone support",
            "Skin elasticity improvement",
            "Liquid format for optimal absorption"
        ],
        "intended_use": "Daily collagen supplementation for anti-aging and joint health",
        "image": "duolife_collagen.jpg"
    },
    {
        "id": "D4",
        "name": "DuoLife Aloes",
        "category": "Dietary Supplement", 
        "price": "25$",
        "type": "Liquid",
        "description": "100% natural food supplement, created for people caring for their condition, vitality, youthful look and health. Premium aloe vera formulation.",
        "health_effects": "Supports antioxidant processes, immune function, gastrointestinal health, detoxification, cardiovascular health",
        "key_features": [
            "Pure aloe vera extract",
            "Digestive system support",
            "Natural detoxification",
            "Antioxidant protection",
            "Cardiovascular wellness"
        ],
        "intended_use": "Daily supplementation for digestive health and detoxification",
        "image": "duolife_aloes.jpg"
    },
    {
        "id": "D5",
        "name": "DuoLife Chlorofil",
        "category": "Dietary Supplement",
        "price": "25$", 
        "type": "Liquid",
        "description": "A natural dietary supplement, created for people wishing to stay in a good shape and maintain their health. Rich chlorophyll content for cellular health.",
        "health_effects": "Supports antioxidant processes, immune function, hematopoiesis, detoxification, cardiovascular health",
        "key_features": [
            "High chlorophyll content",
            "Blood purification support",
            "Natural detoxification",
            "Cellular oxygenation",
            "Energy and vitality boost"
        ],
        "intended_use": "Daily supplementation for blood health and detoxification",
        "image": "duolife_chlorofil.jpg"
    }
]

# Product categories for easy filtering
PRODUCT_CATEGORIES = {
    "dietary_supplements": ["D1", "D2", "D3", "D4", "D5"],
    "liquid_formulas": ["D2", "D3", "D4", "D5"],
    "sets": ["D1"],
    "anti_aging": ["D1", "D3"],
    "immune_support": ["D1", "D2", "D4", "D5"],
    "detoxification": ["D4", "D5"],
    "joint_health": ["D3"],
    "digestive_health": ["D1", "D4"]
}

# Price tiers for recommendation logic
PRICE_TIERS = {
    "premium": ["D1", "D3"],  # Set and anti-aging products
    "standard": ["D2", "D4", "D5"]  # Individual supplements
}

def get_product_by_id(product_id: str) -> Dict:
    """Get product details by ID"""
    for product in DUOLIFE_PRODUCTS:
        if product["id"] == product_id:
            return product
    return None

def get_products_by_category(category: str) -> List[Dict]:
    """Get products by category"""
    if category in PRODUCT_CATEGORIES:
        product_ids = PRODUCT_CATEGORIES[category]
        return [get_product_by_id(pid) for pid in product_ids]
    return []

def get_product_recommendation(customer_needs: str = None, budget: str = "standard") -> Dict:
    """Get product recommendation based on customer needs and budget"""
    
    # Simple recommendation logic
    if customer_needs:
        needs_lower = customer_needs.lower()
        
        if "anti-aging" in needs_lower or "young" in needs_lower or "collagen" in needs_lower:
            return get_product_by_id("D3")  # DuoLife Collagen
        elif "immune" in needs_lower or "vitamin c" in needs_lower:
            return get_product_by_id("D2")  # DuoLife Vita C
        elif "digestive" in needs_lower or "detox" in needs_lower:
            return get_product_by_id("D4")  # DuoLife Aloes
        elif "energy" in needs_lower or "blood" in needs_lower:
            return get_product_by_id("D5")  # DuoLife Chlorofil
        elif "complete" in needs_lower or "daily" in needs_lower:
            return get_product_by_id("D1")  # DuoLife Day and Night
    
    # Default recommendation based on budget
    if budget == "premium":
        return get_product_by_id("D1")  # Complete set
    else:
        return get_product_by_id("D2")  # Vita C as popular choice
