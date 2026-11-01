import os
import uuid
from pathlib import Path
from datetime import date

from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
UPLOAD_FOLDER = Path(app.root_path) / "static" / "uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "smart_agriculture"),
}

CROP_VALUES = {
    "rice", "maize", "tomato", "chilli", "wheat", "barley", "oats", "sorghum",
    "pearl_millet", "finger_millet", "foxtail_millet", "little_millet", "chickpea",
    "pigeon_pea", "green_gram", "black_gram", "lentil", "field_pea", "soybean",
    "groundnut", "sunflower", "sesame", "mustard", "castor", "cotton", "jute",
    "sugarcane", "tobacco", "potato", "sweet_potato", "onion", "garlic", "brinjal",
    "okra", "cabbage", "cauliflower", "spinach", "carrot", "radish", "cucumber",
    "pumpkin", "bitter_gourd", "bottle_gourd", "ridge_gourd", "watermelon", "muskmelon",
    "banana", "mango", "papaya", "guava", "orange", "lemon", "grapes", "pomegranate",
    "apple", "pineapple", "jackfruit", "coconut", "arecanut", "tea", "coffee", "pepper",
    "cardamom", "turmeric", "ginger", "coriander", "cumin", "fenugreek", "clove",
    "cinnamon", "saffron", "vanilla", "rubber", "neem", "aloe_vera", "ashwagandha",
    "tulsi", "rose", "jasmine", "marigold", "hibiscus", "berseem", "alfalfa", "dhaincha",
    "sunhemp", "amaranth", "tapioca", "yam", "colocasia", "drumstick", "custard_apple",
    "sapota", "strawberry", "peach", "cherry", "pear", "plum", "kiwi", "avocado",
    "dragon_fruit", "broccoli", "lettuce", "beetroot", "turnip", "peas", "broad_bean",
    "cluster_bean", "snake_gourd", "ash_gourd", "chayote", "capsicum", "bell_pepper",
    "sweet_corn", "safflower", "linseed", "niger_seed", "rapeseed", "horse_gram", "cowpea",
    "moth_bean", "lablab", "tamarind", "fig", "date_palm", "olive", "betel_leaf",
    "lemongrass", "mint", "basil", "lavender", "chrysanthemum", "dahlia", "tuberose",
    "fodder_maize", "napier_grass", "oyster_mushroom",
}
SOIL_MOISTURE_VALUES = {"very_low", "low", "normal", "high", "very_high"}
WEATHER_VALUES = {"hot_dry", "sunny", "cloudy", "mild", "rainy", "heavy_rain", "humid", "windy", "cold", "frost"}
GROWTH_STAGE_VALUES = {"germination", "seedling", "early_vegetative", "vegetative", "late_vegetative", "budding", "flowering", "fruiting", "maturity", "harvesting"}
SYMPTOM_VALUES = {"none", "yellowing", "brown_spots", "black_spots", "leaf_curling", "wilting", "holes_in_leaves", "leaf_edges_browning", "stunted_growth", "root_rot", "stem_lesions", "powdery_growth", "rust_colored_pustules", "mosaic_pattern", "fruit_rot", "flower_drop", "premature_leaf_fall", "discoloration", "insect_damage", "sticky_leaves", "white_patches", "dry_leaves", "spots"}
ALLOWED = {"crop": CROP_VALUES, "soil_moisture": SOIL_MOISTURE_VALUES, "weather": WEATHER_VALUES, "growth_stage": GROWTH_STAGE_VALUES, "symptoms": SYMPTOM_VALUES}


def label_for(value):
    return str(value).replace("_", " ").title()

CROP_OPTIONS = [{"value": crop, "label": label_for(crop)} for crop in sorted(CROP_VALUES, key=label_for)]
_CROP_GROUPS = {
    "Cereals and Millets": {"rice", "maize", "wheat", "barley", "oats", "sorghum", "pearl_millet", "finger_millet", "foxtail_millet", "little_millet", "sweet_corn", "fodder_maize", "napier_grass"},
    "Pulses": {"chickpea", "pigeon_pea", "green_gram", "black_gram", "lentil", "field_pea", "peas", "broad_bean", "horse_gram", "cowpea", "moth_bean", "lablab"},
    "Oilseeds and Fibre": {"soybean", "groundnut", "sunflower", "sesame", "mustard", "castor", "cotton", "jute", "safflower", "linseed", "niger_seed", "rapeseed"},
    "Vegetables": {"tomato", "chilli", "potato", "sweet_potato", "onion", "garlic", "brinjal", "okra", "cabbage", "cauliflower", "spinach", "carrot", "radish", "cucumber", "pumpkin", "bitter_gourd", "bottle_gourd", "ridge_gourd", "broccoli", "lettuce", "beetroot", "turnip", "cluster_bean", "snake_gourd", "ash_gourd", "chayote", "capsicum", "bell_pepper", "tapioca", "yam", "colocasia", "drumstick", "amaranth", "oyster_mushroom"},
    "Fruits": {"watermelon", "muskmelon", "banana", "mango", "papaya", "guava", "orange", "lemon", "grapes", "pomegranate", "apple", "pineapple", "jackfruit", "custard_apple", "sapota", "strawberry", "peach", "cherry", "pear", "plum", "kiwi", "avocado", "dragon_fruit", "tamarind", "fig", "date_palm", "olive"},
    "Spices, Herbs and Other Crops": {"sugarcane", "tobacco", "coconut", "arecanut", "tea", "coffee", "pepper", "cardamom", "turmeric", "ginger", "coriander", "cumin", "fenugreek", "clove", "cinnamon", "saffron", "vanilla", "rubber", "neem", "aloe_vera", "ashwagandha", "tulsi", "rose", "jasmine", "marigold", "hibiscus", "berseem", "alfalfa", "dhaincha", "sunhemp", "betel_leaf", "lemongrass", "mint", "basil", "lavender", "chrysanthemum", "dahlia", "tuberose"},
}
CROP_CATEGORIES = [{"name": name, "label": name, "options": [{"value": crop, "label": label_for(crop)} for crop in sorted(crops & CROP_VALUES, key=label_for)]} for name, crops in _CROP_GROUPS.items()]


def get_connection():
    password = os.getenv("MYSQL_PASSWORD", "")
    if not password:
        raise RuntimeError("MYSQL_PASSWORD is not set.")
    config = DB_CONFIG.copy()
    config["password"] = password
    return mysql.connector.connect(**config)


def analyze_crop(crop, soil_moisture, weather, growth_stage, symptoms):
    """Starter rule-based guidance only; this does not diagnose a disease."""
    wet_soil = soil_moisture in {"high", "very_high"}
    dry_soil = soil_moisture in {"very_low", "low"}
    wet_weather = weather in {"rainy", "heavy_rain", "humid"}
    hot_weather = weather in {"hot_dry", "sunny"}
    symptom_names = SYMPTOM_VALUES - {"none"}
    if dry_soil and hot_weather:
        risk = "Possible water stress"
        recommendation = "Check root-zone moisture and assess whether irrigation is appropriate for this crop."
        reason = "Low reported soil moisture combined with hot or sunny weather can increase water-stress risk."
    elif wet_soil and wet_weather:
        risk = "Possible excess moisture"
        recommendation = "Inspect drainage and soil conditions before adding water."
        reason = "High soil moisture combined with wet weather may increase waterlogging risk."
    elif symptoms in symptom_names:
        risk = "Crop symptoms need investigation"
        recommendation = "Inspect affected plant parts and consult crop-specific agricultural guidance before treatment."
        reason = "The selected symptom can have multiple causes and does not confirm a particular disease."
    else:
        risk = "Continue monitoring"
        recommendation = "Monitor the crop regularly and follow verified guidance for its growth stage."
        reason = "The supplied information did not trigger a specific starter rule. This does not guarantee crop health."
    return {"crop": label_for(crop), "growth_stage": label_for(growth_stage), "risk": risk, "recommendation": recommendation, "reason": reason}


def save_uploaded_crop_image(file_storage):
    if file_storage is None or not file_storage.filename:
        return None, None
    original_name = secure_filename(file_storage.filename)
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Please upload a JPG, JPEG, PNG, or WebP image.")
    unique_name = f"{uuid.uuid4().hex}{extension}"
    destination = UPLOAD_FOLDER / unique_name
    file_storage.save(destination)
    return unique_name, f"uploads/{unique_name}"


def save_analysis(crop, stage, moisture, weather, symptoms, result):
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO crop_analysis
            (crop, growth_stage, soil_moisture, weather, symptoms, risk, recommendation, reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (crop, stage, moisture, weather, symptoms, result["risk"], result["recommendation"], result["reason"]))
        connection.commit()
        return True, "Analysis saved successfully in MySQL."
    except (Error, RuntimeError) as error:
        app.logger.error("Database save error: %s", error)
        return False, "Analysis completed, but saving failed. Check MySQL settings, database, and crop_analysis table."
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


# Load the open-source model only when the first identification request arrives.
# First use requires internet to download model weights. Results are estimates, not diagnosis.
plant_classifier = None

def get_plant_classifier():
    global plant_classifier
    if plant_classifier is None:
        from transformers import pipeline
        plant_classifier = pipeline(
            "image-classification",
            model="domai-tb/OpenPlants-Identification-ViT-Base-Patch16-224",
        )
    return plant_classifier


@app.route("/api/identify-plant", methods=["POST"])
def identify_plant():
    if "crop_image" not in request.files or not request.files["crop_image"].filename:
        return jsonify({"error": "Please choose a crop image first."}), 400
    image_file = request.files["crop_image"]
    extension = Path(secure_filename(image_file.filename)).suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Upload a JPG, JPEG, PNG, or WebP image."}), 400
    try:
        from PIL import Image, UnidentifiedImageError
        image = Image.open(image_file.stream).convert("RGB")
        predictions = get_plant_classifier()(image, top_k=3)
        return jsonify({
            "success": True,
            "predictions": [{"plant": item["label"], "confidence_percent": round(float(item["score"]) * 100, 2)} for item in predictions],
            "note": "AI estimate only. Verify the result, especially when confidence is low. This model does not confirm plant disease.",
        })
    except (UnidentifiedImageError, OSError):
        return jsonify({"error": "The uploaded file is not a valid image."}), 400
    except Exception:
        app.logger.exception("Plant identification failed")
        return jsonify({"error": "Plant identification failed. Install model dependencies and check server logs."}), 500


@app.route("/api/weather", methods=["POST"])
def get_weather():
    """Fetch forecast for coordinates explicitly provided by the consenting browser."""
    data = request.get_json(silent=True) or {}
    try:
        latitude = float(data["latitude"])
        longitude = float(data["longitude"])
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Valid latitude and longitude are required."}), 400
    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({"error": "Coordinates are out of range."}), 400
    try:
        import requests
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": 3,
                "timezone": "auto",
            }, timeout=15,
        )
        response.raise_for_status()
        return jsonify(response.json())
    except Exception:
        app.logger.exception("Weather request failed")
        return jsonify({"error": "Weather service is temporarily unavailable."}), 502


@app.route("/api/farmer-profile", methods=["POST"])
def save_farmer_profile():
    """Create a farmer profile and its crop records; expects JSON."""
    data = request.get_json(silent=True) or {}
    name = str(data.get("farmer_name", "")).strip()
    crops = data.get("crops", [])
    try:
        total_acres = float(data.get("total_acres", 0))
        if not name or not (0 < total_acres <= 1_000_000) or not isinstance(crops, list) or not crops:
            return jsonify({"error": "Enter a farmer name, valid total acres, and at least one crop."}), 400
        clean_crops = []
        crop_total = 0.0
        for crop in crops:
            if not isinstance(crop, dict):
                return jsonify({"error": "Each crop entry must be an object."}), 400
            crop_name = str(crop.get("crop_name", "")).strip()
            acres = float(crop.get("acres", 0))
            if not crop_name or len(crop_name) > 100 or not (0 < acres <= total_acres):
                return jsonify({"error": "Each crop needs a name and a positive acreage not exceeding total land."}), 400
            sowing_date = crop.get("sowing_date") or None
            if sowing_date:
                date.fromisoformat(str(sowing_date))
            clean_crops.append((crop_name, acres, sowing_date, crop.get("growth_stage") or None, crop.get("soil_type") or None, crop.get("irrigation_type") or None))
            crop_total += acres
        if crop_total > total_acres + 0.0001:
            return jsonify({"error": "Combined crop acres cannot exceed the farmer's total land."}), 400
    except (TypeError, ValueError):
        return jsonify({"error": "Acres must be valid numbers and dates must use YYYY-MM-DD."}), 400

    connection = cursor = None
    try:
        connection = get_connection()
        connection.start_transaction()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO farmer_profile (farmer_name, phone, village, district, state, total_acres)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, data.get("phone"), data.get("village"), data.get("district"), data.get("state") or "Andhra Pradesh", total_acres))
        farmer_id = cursor.lastrowid
        cursor.executemany("""
            INSERT INTO farmer_crops (farmer_id, crop_name, acres, sowing_date, growth_stage, soil_type, irrigation_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, [(farmer_id, *crop) for crop in clean_crops])
        connection.commit()
        return jsonify({"success": True, "farmer_id": farmer_id, "message": "Farmer profile and crops saved."}), 201
    except (Error, RuntimeError):
        if connection is not None and connection.is_connected():
            connection.rollback()
        app.logger.exception("Saving farmer profile failed")
        return jsonify({"error": "Could not save profile. Confirm the farmer_profile and farmer_crops tables exist."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/api/farmer-profile/<int:farmer_id>", methods=["GET"])
def get_farmer_profile(farmer_id):
    """Return a profile and crop list for integration/testing; add auth before public deployment."""
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM farmer_profile WHERE farmer_id = %s", (farmer_id,))
        farmer = cursor.fetchone()
        if not farmer:
            return jsonify({"error": "Farmer profile not found."}), 404
        cursor.execute("SELECT * FROM farmer_crops WHERE farmer_id = %s ORDER BY crop_id", (farmer_id,))
        farmer["crops"] = cursor.fetchall()
        return jsonify(farmer)
    except (Error, RuntimeError):
        app.logger.exception("Loading farmer profile failed")
        return jsonify({"error": "Could not load farmer profile. Check MySQL tables."}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/", methods=["GET", "POST"])
def home():
    result = error = db_message = None
    db_saved = False
    uploaded_image_url = None
    if request.method == "POST":
        submitted = {"crop": request.form.get("crop", ""), "soil_moisture": request.form.get("soil_moisture", ""), "weather": request.form.get("weather", ""), "growth_stage": request.form.get("growth_stage", ""), "symptoms": request.form.get("symptoms", "")}
        if any(value not in ALLOWED[key] for key, value in submitted.items()):
            error = "Please select a valid option in every field."
        else:
            try:
                _saved_image_name, uploaded_image_url = save_uploaded_crop_image(request.files.get("crop_image"))
            except ValueError as upload_error:
                error = str(upload_error)
        if error is None:
            result = analyze_crop(submitted["crop"], submitted["soil_moisture"], submitted["weather"], submitted["growth_stage"], submitted["symptoms"])
            db_saved, db_message = save_analysis(submitted["crop"], submitted["growth_stage"], submitted["soil_moisture"], submitted["weather"], submitted["symptoms"], result)
            if uploaded_image_url:
                result["uploaded_image_url"] = uploaded_image_url
    return render_template("index.html", result=result, error=error, db_message=db_message, db_saved=db_saved, crop_categories=CROP_CATEGORIES, crop_options=CROP_OPTIONS)


@app.route("/dashboard")
def dashboard():
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT COUNT(*) AS total_analyses, COUNT(DISTINCT crop) AS crops_analyzed,
            COALESCE(SUM(CASE WHEN LOWER(risk) LIKE '%stress%' OR LOWER(risk) LIKE '%excess%' THEN 1 ELSE 0 END), 0) AS high_risk_count,
            COALESCE(SUM(CASE WHEN LOWER(soil_moisture) IN ('very_low', 'low') THEN 1 ELSE 0 END), 0) AS low_moisture_count,
            COALESCE(SUM(CASE WHEN risk = 'Continue monitoring' THEN 1 ELSE 0 END), 0) AS monitoring_count
            FROM crop_analysis
        """)
        stats = cursor.fetchone() or {}
        cursor.execute("SELECT id, crop, risk, growth_stage, soil_moisture, weather FROM crop_analysis ORDER BY id DESC LIMIT 5")
        recent_analyses = cursor.fetchall()
        cursor.execute("SELECT crop, COUNT(*) AS total FROM crop_analysis GROUP BY crop ORDER BY total DESC, crop ASC")
        crop_stats = cursor.fetchall()
        cursor.execute("SELECT risk, COUNT(*) AS total FROM crop_analysis GROUP BY risk ORDER BY total DESC")
        risk_stats = cursor.fetchall()
        return render_template("dashboard.html", stats=stats, recent_analyses=recent_analyses, crop_stats=crop_stats, risk_stats=risk_stats)
    except (Error, RuntimeError):
        app.logger.exception("Dashboard database error")
        return "Could not load dashboard. Check MySQL settings and the crop_analysis table.", 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.route("/history")
def history():
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM crop_analysis ORDER BY id DESC")
        analyses = cursor.fetchall()
        return render_template("history.html", analyses=analyses)
    except (Error, RuntimeError):
        app.logger.exception("History database error")
        return "Could not load history. Check MySQL settings and confirm crop_analysis has an id column.", 500
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None and connection.is_connected():
            connection.close()


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "Image is too large. Maximum upload size is 5 MB."}), 413
@app.route("/farmer-profile")
def farmer_profile_page():
    return render_template("farmer_profile.html")

if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("PORT", "5003")))
