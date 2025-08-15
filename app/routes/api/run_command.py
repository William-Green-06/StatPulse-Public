from flask import Blueprint, request, jsonify
from app.data.database import reset_matchup_preds
from app.routes.admin import admin_required
from app.data.update_fighters import update_fighter_data, update_matchups, update_odds
import threading

run_command_api = Blueprint('run_command_api', __name__)

def update_upcoming_odds(odds_site, odds_link):
    # data = request.json
    # print(data)
    # odds_site = data.get("odds_site", "BestFightOdds")
    # odds_link = data.get("odds_link")
    #print(f"{odds_link} + {odds_site}")
    
    t = threading.Thread(target=run_update_upcoming_odds, args=(odds_site, odds_link))
    t.start()
    
    return jsonify({"message": "Update started in background.  Check render for more info."})

def update_upcoming_matchups():
    t = threading.Thread(target=run_update_upcoming_matchups)
    t.start()
    
    return jsonify({"message": "Update started in background.  Check render for more info."})

# Define your actual commands
def run_update_upcoming_matchups(): 
    try:
        update_fighter_data()
        update_matchups(clean=True)
        #update_odds(website=odds_site, link=odds_link)
    except Exception as e:
        return f"An error occured while updating: {e}"

    return f"Matchups have been updated."

def run_update_upcoming_odds(odds_site, odds_link): 
    if odds_site != 'BestFightOdds' and odds_site != 'FightOdds.io':
        return f"Invalid odds site."

    try:
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
    "updateUpcomingOdds": update_upcoming_odds
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