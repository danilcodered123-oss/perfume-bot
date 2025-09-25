import json, os
from pathlib import Path

DATA_FILE = Path(__file__).parent / 'data' / 'products.json'

def load_products():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []
