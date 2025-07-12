from flask import Blueprint, request, jsonify
from app.data.database import get_fighters_by_string

fighter_search_api = Blueprint('fighter_search_api', __name__)

@fighter_search_api.route('/fighter-search', methods=['GET'])
def fighter_search():
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    # Example: search fighters from DB whose names contain the query (case-insensitive)
    results = get_fighters_by_string(query)
    return jsonify(results)