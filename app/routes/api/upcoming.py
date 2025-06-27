from flask import Blueprint, jsonify
from app.model.predictor import predict_matchup
from app.data.database import get_upcoming_matchups_from_db, get_fighter_by_id, get_name_by_id, get_matchup_prediction, set_matchup_prediction

upcoming_api = Blueprint('upcoming_api', __name__)

def implied_moneyline(prob):
    if prob >= 0.5:
        odds = -round((prob / (1 - prob)) * 100)
        direction = ">"
    return f"{direction} {odds}"

@upcoming_api.route('/upcoming')
def upcoming():
    matchups = get_upcoming_matchups_from_db()
    response = []
    for matchup in matchups:
        fighter_a_name = get_name_by_id(matchup[0])[0]
        fighter_b_name = get_name_by_id(matchup[1])[0]
        
        fighter_a_data = get_fighter_by_id(matchup[0])
        fighter_b_data = get_fighter_by_id(matchup[1])

        preds = get_matchup_prediction(matchup[0], matchup[1])
        if preds != None:
            if preds[0] != None and preds[1] != None:
                no_odds = (fighter_a_data['odds'] == None or fighter_b_data['odds'] == None)
                winner_prob = preds[0] if preds[0] > preds[1] else preds[1]
                winner_name = fighter_a_name if preds[0] > preds[1] else fighter_b_name
                winner_last_name = winner_name.split(' ')[1 if len(winner_name.split(' ')) > 1 else 0]
                good_odds = implied_moneyline(winner_prob)
    
                response.append({
                    'fighter_a_id': matchup[0],
                    'fighter_b_id': matchup[1],
                    'fighter_a_name': fighter_a_name,
                    'fighter_b_name': fighter_b_name,
                    'prediction_a': preds[0],
                    'prediction_b': preds[1],
                    'good_odds': good_odds,
                    'no_odds': no_odds,
                    'winner_last_name': winner_last_name
                })
        else:
            pred_a, no_odds = predict_matchup(fighter_a_data, fighter_b_data)
            pred_b = 1 - pred_a
            winner_prob = pred_a if pred_a > pred_b else pred_b
            winner_name = fighter_a_name if pred_a > pred_b else fighter_b_name
            winner_last_name = winner_name.split(' ')[1 if len(winner_name.split(' ')) > 1 else 0]
            good_odds = implied_moneyline(winner_prob)

            response.append({
                'fighter_a_id': matchup[0],
                'fighter_b_id': matchup[1],
                'fighter_a_name': fighter_a_name,
                'fighter_b_name': fighter_b_name,
                'prediction_a': pred_a,
                'prediction_b': pred_b,
                'good_odds': good_odds,
                'no_odds': no_odds,
                'winner_last_name': winner_last_name
            })

            set_matchup_prediction(matchup[0], matchup[1], float(pred_a), float(pred_b))

    return jsonify(response)