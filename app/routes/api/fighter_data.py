from flask import Blueprint, request, jsonify
from app.data.database import get_fighter_by_id, set_fighter_value
from app.routes.admin import admin_required

fighter_data_api = Blueprint('fighter_data_api', __name__)

@fighter_data_api.route('/fighter-data', methods=['GET'])
def get_fighter_data():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])
    id = int(query)
    # Example: search fighters from DB whose names contain the query (case-insensitive)
    results = get_fighter_by_id(id)
    return jsonify(results)

@fighter_data_api.route('/set-fighter-stat', methods=['POST'])
@admin_required
def set_fighter_stat():
    data = request.get_json()
    fighter_id = data.get('id')
    field = data.get('field')
    value = data.get('value')
    
    set_fighter_value(fighter_id, field, value)
    return jsonify({'status': 'ok'})