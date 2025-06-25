from flask import Blueprint, jsonify, request
from app.model.predictor import predict_matchup
from app.data.database import get_fighter_by_id, get_name_by_id

predict_api = Blueprint('predict_api', __name__)

def implied_moneyline(prob):
    if prob >= 0.5:
        odds = -round((prob / (1 - prob)) * 100)
        direction = ">"
    return f"{direction} {odds}"

def clean_and_validate_odds(odds_str: str) -> int | None:
    # Remove all whitespace and any leading '+'
    cleaned = odds_str.replace(' ', '').lstrip('+')

    if cleaned.startswith(('+', '-')):
        sign = cleaned[0]
        number_part = cleaned[1:]
    else:
        sign = ''
        number_part = cleaned

    # Check if the remaining string is all digits (and thus a valid integer)
    if number_part.isdigit():
        return int(sign + number_part)
    else:
        print(f"BAD ODDS!: [{odds_str}], [{cleaned}]")
        return None  # or raise ValueError("Invalid odds")

@predict_api.route('/predict', methods=['POST'])
def predict():
    print("Received POST /api/predict")

    data = request.get_json()  # Parse JSON body
    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    fighter_a_id = data.get('fighter_a_id')
    fighter_b_id = data.get('fighter_b_id')

    fighter_a_name = get_name_by_id(fighter_a_id)[0]
    fighter_b_name = get_name_by_id(fighter_b_id)[0]

    fighter_a_data = get_fighter_by_id(fighter_a_id)
    fighter_b_data = get_fighter_by_id(fighter_b_id)

    # Before sending the odds data over, let's clean them up and make sure they're usable
    fighter_a_odds = clean_and_validate_odds(data.get('fighter_a_odds'))
    fighter_b_odds = clean_and_validate_odds(data.get('fighter_b_odds'))

    fighter_a_data['odds'] = fighter_a_odds
    fighter_b_data['odds'] = fighter_b_odds

    pred_a, no_odds = predict_matchup(fighter_a_data, fighter_b_data)
    pred_b = 1 - pred_a
    winner_prob = pred_a if pred_a > pred_b else pred_b
    winner_name = fighter_a_name if pred_a > pred_b else fighter_b_name
    winner_last_name = winner_name.split(' ')[1 if len(winner_name.split(' ')) > 1 else 0]
    good_odds = implied_moneyline(winner_prob)

    response = {
        'fighter_a_name': fighter_a_name,
        'fighter_b_name': fighter_b_name,
        'prediction_a': pred_a,
        'prediction_b': pred_b,
        'good_odds': good_odds,
        'no_odds': no_odds,
        'winner_name': winner_name,
        'winner_last_name': winner_last_name
    }

    return jsonify(response)