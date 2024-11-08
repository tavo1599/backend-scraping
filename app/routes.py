from flask import Blueprint, jsonify
from .scraping import scrape_tvsur
from .firebase_manager import upload_to_firebase

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return jsonify({"message": "Bienvenido a la API de scraping"})