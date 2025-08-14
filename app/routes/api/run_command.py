from flask import Blueprint, request, jsonify
from app.data.database import reset_matchup_preds
from app.routes.admin import admin_required
from app.data.update_fighters import update_fighter_data, update_matchups, update_odds
import threading

run_command_api = Blueprint('run_command_api', __name__)

def update_upcoming_matchups():
    data = request.json
    odds_site = data.get("odds_site", "BestFightOdds")
    odds_link = data.get("odds_link")
    
    t = threading.Thread(target=run_update_upcoming_matchups, args=(odds_site, odds_link))
    t.start()
    
    return jsonify({"message": "Update started in background.  Check render for more info."})

# Define your actual commands
def run_update_upcoming_matchups(odds_site='BestFightOdds', odds_link=None):
    if odds_site != 'BestFightOdds' and odds_site != 'FightOdds.io':
        return "Error: invalid odds site."
    
    if odds_site == 'FightOdds.io' and odds_link == None:
        return "Error: invalid odds link."
    
    try:
        update_fighter_data()
        update_matchups(clean=True)
        update_odds(website=odds_site, link=odds_link)
    except Exception as e:
        return f"An error occured while updating: {e}"

    return f"Matchups have been updated."

def clear_matchup_preds():
    reset_matchup_preds()
    print("Predictions have been reset in the matchups table.")
    return "Preds reset!"

# Map command names to functions
COMMANDS = {
    "updateUpcomingMatchups": update_upcoming_matchups,
    "clearMatchupPreds": clear_matchup_preds,
}

@run_command_api.route('/run-command', methods=['POST'])
@admin_required
def run_command():
    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"error": "Missing command"}), 400

    cmd_name = data["command"]
    args = data.get("args", [])

    if cmd_name not in COMMANDS:
        return jsonify({"error": f"Unknown command '{cmd_name}'"}), 400

    cmd_func = COMMANDS[cmd_name]

    try:
        # Call the function with the args array, works for zero or multiple arguments
        result = cmd_func(*args)
        return jsonify({"message": str(result)})
    except Exception as e:
        # You could also log e somewhere for debugging
        return jsonify({"error": str(e)}), 500