
import re
import unicodedata

CROP_CATEGORIES = {
    "Cereals and Millets": [
        "Rice (Paddy)", "Wheat", "Maize", "Jowar (Sorghum)",
        "Bajra (Pearl Millet)", "Ragi (Finger Millet)", "Barley",
        "Foxtail Millet", "Little Millet", "Kodo Millet",
        "Barnyard Millet", "Proso Millet", "Browntop Millet",
        "Oats", "Buckwheat", "Amaranth Grain", "Black Rice",
        "Basmati Rice", "Job's Tears"
    ],
    "Pulses and Legumes": [
        "Chickpea (Bengal Gram)", "Pigeon Pea (Toor)", "Green Gram",
        "Black Gram", "Lentil", "Field Pea", "Cowpea", "Horse Gram",
        "Moth Bean", "Kidney Bean (Rajma)", "French Bean", "Lobia",
        "Grass Pea", "White Pea", "Faba Bean", "Hyacinth Bean",
        "Winged Bean", "Rice Bean", "Soybean", "Bambara Groundnut",
        "Adzuki Bean"
    ],
    "Oilseed Crops": [
        "Groundnut", "Mustard", "Rapeseed", "Soybean", "Sunflower",
        "Sesame", "Safflower", "Niger Seed", "Linseed", "Castor",
        "Coconut", "Oil Palm", "Cottonseed", "Pongamia", "Neem Seed",
        "Perilla", "Watermelon Seed", "Pumpkin Seed"
    ],
    "Fibre Crops": [
        "Cotton", "Jute", "Mesta", "Sunn Hemp", "Flax", "Kenaf",
        "Ramie", "Hemp", "Sisal", "Banana Fibre"
    ],
    "Sugar and Commercial Crops": [
        "Sugarcane", "Sugar Beet", "Tobacco", "Tea", "Coffee",
        "Rubber", "Arecanut", "Betel Leaf", "Cocoa", "Guar", "Indigo"
    ],
    "Leafy Vegetables": [
        "Spinach", "Amaranth Leaves", "Fenugreek Leaves",
        "Coriander Leaves", "Mint", "Mustard Greens", "Lettuce",
        "Bathua", "Gongura", "Malabar Spinach", "Drumstick Leaves",
        "Dill Leaves"
    ],
    "Fruit Vegetables": [
        "Tomato", "Brinjal (Eggplant)", "Green Chilli", "Capsicum",
        "Okra (Lady's Finger)", "Cucumber", "Bottle Gourd",
        "Bitter Gourd", "Ridge Gourd", "Sponge Gourd", "Snake Gourd",
        "Pumpkin", "Ash Gourd", "Pointed Gourd", "Ivy Gourd",
        "Chayote", "Zucchini", "Sweet Corn", "Baby Corn"
    ],
    "Root and Tuber Vegetables": [
        "Potato", "Sweet Potato", "Tapioca (Cassava)",
        "Elephant Foot Yam", "Colocasia (Taro)", "Greater Yam",
        "Lesser Yam", "Carrot", "Radish", "Beetroot", "Turnip",
        "Onion", "Garlic", "Shallots", "Lotus Root", "Arrowroot"
    ],
    "Other Vegetables": [
        "Cabbage", "Cauliflower", "Broccoli", "Knol-khol",
        "Brussels Sprouts", "Green Peas", "French Beans",
        "Cluster Beans", "Drumstick Pods", "Raw Banana",
        "Raw Papaya", "Tender Jackfruit", "Mushroom"
    ],
    "Tropical and Subtropical Fruits": [
        "Mango", "Banana", "Papaya", "Guava", "Pineapple", "Jackfruit",
        "Sapota", "Coconut", "Watermelon", "Muskmelon", "Pomegranate",
        "Sweet Lime", "Sweet Orange", "Lemon", "Acid Lime", "Grapefruit",
        "Pomelo", "Custard Apple", "Amla", "Jamun", "Ber", "Bael",
        "Wood Apple", "Tamarind", "Indian Fig", "Phalsa", "Karonda",
        "Avocado", "Passion Fruit", "Dragon Fruit", "Litchi", "Longan",
        "Rambutan", "Mangosteen", "Durian", "Breadfruit", "Bilimbi",
        "Star Fruit", "Mulberry", "Fig", "Date Palm", "Rose Apple",
        "Water Apple", "Soursop", "Persimmon", "Cashew"
    ],
    "Temperate and Hill Fruits": [
        "Apple", "Pear", "Peach", "Plum", "Apricot", "Cherry",
        "Strawberry", "Kiwi", "Almond", "Walnut", "Chestnut",
        "Grapes", "Pistachio", "Quince"
    ],
    "Spices and Condiments": [
        "Black Pepper", "Small Cardamom", "Large Cardamom", "Ginger",
        "Turmeric", "Dry Chilli", "Coriander Seed", "Cumin", "Fennel",
        "Fenugreek", "Mustard Seed", "Ajwain", "Dill Seed", "Nigella",
        "Celery Seed", "Clove", "Cinnamon", "Cassia", "Nutmeg", "Mace",
        "Vanilla", "Saffron", "Curry Leaf", "Bay Leaf", "Kokum",
        "Asafoetida"
    ],
    "Plantation and Beverage Crops": [
        "Tea", "Coffee", "Coconut", "Arecanut", "Rubber", "Cocoa",
        "Oil Palm", "Cashew", "Betel Vine", "Vanilla", "Bamboo",
        "Agarwood"
    ],
    "Medicinal and Aromatic Crops": [
        "Ashwagandha", "Tulsi", "Aloe Vera", "Neem", "Senna",
        "Isabgol", "Sarpagandha", "Safed Musli", "Shatavari",
        "Kalmegh", "Brahmi", "Mandukaparni", "Stevia", "Lemongrass",
        "Citronella", "Vetiver", "Palmarosa", "Menthol Mint",
        "Patchouli", "Sandalwood", "Periwinkle", "Coleus", "Moringa",
        "Licorice", "Chamomile"
    ],
    "Flowers and Ornamental Crops": [
        "Rose", "Jasmine", "Marigold", "Chrysanthemum", "Tuberose",
        "Gerbera", "Gladiolus", "Carnation", "Orchid", "Anthurium",
        "Lotus", "Water Lily", "Crossandra", "China Aster", "Hibiscus",
        "Dahlia", "Petunia", "Sunflower (Ornamental)", "Lilium",
        "Bird of Paradise"
    ],
    "Fodder and Green-Manure Crops": [
        "Berseem", "Lucerne (Alfalfa)", "Fodder Sorghum",
        "Fodder Maize", "Fodder Pearl Millet", "Napier Grass",
        "Guinea Grass", "Para Grass", "Stylo", "Cowpea (Fodder)",
        "Oats (Fodder)", "Dhaincha", "Sunn Hemp", "Sesbania",
        "Pillipesara", "Horse Gram (Green Manure)", "Velvet Bean",
        "Fodder Beet"
    ],
    "Regional and Underutilized Crops": [
        "Kalingda", "Traditional Red Rice", "Indigenous Rice Variety",
        "Finger Millet Landrace", "Foxtail Millet Landrace",
        "Kodo Millet Landrace", "Proso Millet Landrace", "Taro Landrace",
        "Elephant Foot Yam Variety", "Indigenous Cowpea",
        "Indigenous Pigeon Pea", "Indigenous Chilli",
        "Indigenous Mango", "Indigenous Banana", "Indigenous Citrus",
        "Indigenous Jackfruit"
    ]
}


def make_crop_slug(name):
    """Convert a crop label into a stable database/form value."""
    normalized = unicodedata.normalize("NFKD", name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.lower()).strip("_")

    # Preserve existing database/form values.
    legacy_values = {
        "rice_paddy": "rice",
        "maize": "maize",
        "tomato": "tomato",
        "green_chilli": "chilli"
    }

    return legacy_values.get(slug, slug)


CROP_OPTIONS = [
    {
        "category": category,
        "label": crop,
        "value": make_crop_slug(crop)
    }
    for category, crops in CROP_CATEGORIES.items()
    for crop in crops
]

# Maps submitted values back to display labels.
CROP_LABELS = {
    item["value"]: item["label"]
    for item in CROP_OPTIONS
}

# Allow older records and existing values to remain readable.
CROP_LABELS.update({
    "rice": "Rice (Paddy)",
    "maize": "Maize",
    "tomato": "Tomato",
    "chilli": "Green Chilli"
})
