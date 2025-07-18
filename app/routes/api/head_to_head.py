from flask import Blueprint, jsonify, request
from app.data.database import get_fighter_by_id
from app.routes.api.predict import clean_and_validate_odds

head_to_head_api = Blueprint('head_to_head_api', __name__)

def robust_scale_with_clipping(val, min_val, max_val, median, scale):
    val_clipped = max(min(val, max_val), min_val)
    norm = ((val_clipped - median) / scale) * 100
    return max(0, min(100, norm))

def calculateFighterSpecs(fighter_data):
    # Striking
    reach = 0.7 * robust_scale_with_clipping(float(fighter_data['reach']), 64.0000, 79.0000, 72.0000, 6.0000)
    SLpM = 1.5 * robust_scale_with_clipping(float(fighter_data['slpm']), 0.0000, 6.5489, 3.4359, 1.9960)
    SApM = 1.2 * (100 - robust_scale_with_clipping(float(fighter_data['sapm']), 0.0000, 5.9543, 2.9850, 1.8457))
    StrDef = 1.0 * robust_scale_with_clipping(float(fighter_data['strdef']), 0.0000, 69.6072, 55.7538, 13.3161)
    total_head_strikes = 0.8 * robust_scale_with_clipping(float(fighter_data['total_head_strikes']), 0.0000, 593.0000, 117.0000, 220.0000)
    total_body_strikes = 0.6 * robust_scale_with_clipping(float(fighter_data['total_body_strikes']), 0.0000, 200.0000, 34.0000, 68.0000)
    total_leg_strikes = 0.6 * robust_scale_with_clipping(float(fighter_data['total_leg_strikes']), 0.0000, 168.0000, 23.0000, 53.0000)
    total_strikes_landed = 0.7 * robust_scale_with_clipping(float(fighter_data['total_strikes_landed']), 0.0000, 941.0000, 181.0000, 338.0000)
    total_strikes_missed = 0.7 * (100 - robust_scale_with_clipping(float(fighter_data['total_strikes_missed']), 0.0000, 2109.4500, 398.0000, 759.0000))
    StrAcc = 1.5 * robust_scale_with_clipping(float(fighter_data['stracc']), 0.0000, 61.6040, 45.0704, 12.3999)
    head_strikes_accuracy = 1.0 * robust_scale_with_clipping(float(fighter_data['head_strikes_accuracy']), 0.0000, 35.4735, 26.9266, 6.7514)
    body_strikes_accuracy = 0.8 * robust_scale_with_clipping(float(fighter_data['body_strikes_accuracy']), 0.0000, 47.3684, 40.6530, 6.2962)
    leg_strikes_accuracy = 0.6 * robust_scale_with_clipping(float(fighter_data['leg_strikes_accuracy']), 0.0000, 50.0000, 44.7761, 5.3837)
    aggression_metric = 0.8 * robust_scale_with_clipping(float(fighter_data['aggression_metric']), 0.0000, 20.1341, 11.3333, 6.1340)

    striking_score = round(((reach + SLpM + SApM + StrDef + total_head_strikes + total_body_strikes + total_leg_strikes
                      + total_strikes_landed + total_strikes_missed + StrAcc + head_strikes_accuracy + body_strikes_accuracy
                      + leg_strikes_accuracy + aggression_metric) / 900) * 100)
    striking_score = max(1, min(striking_score, 100))

    # Grappling
    TDAvg = 1.0 * robust_scale_with_clipping(float(fighter_data['tdavg']), 0.0000, 4.5226, 1.0944, 2.0571)
    TDAcc = 1.0 * robust_scale_with_clipping(float(fighter_data['tdacc']), 0.0000, 83.3333, 35.8974, 37.5000)
    TDDef = 1.0 * robust_scale_with_clipping(float(fighter_data['tddef']), 0.0000, 100.0000, 62.5000, 37.4194)
    SubAvg = 0.7 * robust_scale_with_clipping(float(fighter_data['subavg']), 0.0000, 2.3341, 0.2964, 0.9091)
    SubAcc = 0.7 * robust_scale_with_clipping(float(fighter_data['subacc']), 0.0000, 100.0000, 0.0000, 33.3333)
    rel_sub_rate = 0.6 * robust_scale_with_clipping(float(fighter_data['rel_sub_rate']), 0.0000, 80.0000, 0.0000, 28.5714)
    abs_sub_rate = 0.6 * robust_scale_with_clipping(float(fighter_data['abs_sub_rate']), 0.0000, 50.0000, 0.0000, 20.0000)
    sub_wins = 0.6 * robust_scale_with_clipping(float(fighter_data['sub_wins']), 0.0000, 4.0000, 0.0000, 1.0000)
    sub_losses = 0.8 * (100 - robust_scale_with_clipping(float(fighter_data['sub_losses']), 0.0000, 2.0000, 0.0000, 1.0000))
    knockdown_durability = 0.3 * (robust_scale_with_clipping(float(fighter_data['knockdown_durability']), 0.0000, 0.0622, 0.0000, 0.0212) * 100) # Scale up a bit
    win_finish_metric = 0.6 * robust_scale_with_clipping(float(fighter_data['win_finish_metric']), 0.0000, 10000.0000, 3076.9231, 5000.0000)

    grappling_score = round(((TDAvg + TDAcc + TDDef + SubAvg + SubAcc + rel_sub_rate + abs_sub_rate + sub_wins + sub_losses 
                             + knockdown_durability + win_finish_metric) / 790) * 100)
    grappling_score = max(1, min(grappling_score, 100))

    # Finish Threat
    ko_wins = 1.2 * robust_scale_with_clipping(float(fighter_data['ko_wins']), 0.0000, 6.0000, 1.0000, 2.0000)
    sub_wins = 1.2 * sub_wins
    SubAvg = 0.6 * SubAvg
    rel_ko_rate = 1.0 * robust_scale_with_clipping(float(fighter_data['rel_ko_rate']), 0.0000, 100.0000, 20.0000, 50.0000)
    abs_ko_rate = 0.8 * robust_scale_with_clipping(float(fighter_data['abs_ko_rate']), 0.0000, 66.6667, 12.5000, 33.3333)
    rel_sub_rate = 1.0 * rel_sub_rate
    abs_sub_rate = 0.8 * abs_sub_rate
    win_finish_metric = 0.7 * win_finish_metric
    StrAcc = 0.5 * StrAcc
    knockdowns = 0.9 * robust_scale_with_clipping(float(fighter_data['knockdowns']), 0.0000, 8.0000, 1.0000, 3.0000)
    finish_rate = 1.25 * robust_scale_with_clipping(float(fighter_data['finish_rate']), 0.0000, 100.0000, 50.0000, 75.0000)
    win_streak = 0.4 * robust_scale_with_clipping(float(fighter_data['win_streak']), 0.0000, 2.0000, 0.0000, 1.0000)

    finish_threat_score = round(((ko_wins + sub_wins + SubAvg + rel_ko_rate + abs_ko_rate + rel_sub_rate + abs_sub_rate
                                  + win_finish_metric + StrAcc + knockdowns + finish_rate + win_streak) / 900) * 100)
    finish_threat_score = max(1, min(finish_threat_score, 100))

    # Durability
    losses = 0.9 * (100 - robust_scale_with_clipping(float(fighter_data['losses']), 0.0000, 8.0000, 2.0000, 3.0000))
    ko_losses = 0.9 * (100 - robust_scale_with_clipping(float(fighter_data['ko_losses']), 0.0000, 3.0000, 0.0000, 1.0000))
    ko_risk = 0.85 * (100 - robust_scale_with_clipping(float(fighter_data['ko_risk']), 0.0000, 40.0000, 0.0000, 13.6364))
    sub_losses = 0.7 * sub_losses
    sub_risk = 0.7 * (100 - robust_scale_with_clipping(float(fighter_data['sub_risk']), 0.0000, 33.3333, 0.0000, 7.8947))
    finish_rate = 0.6 * finish_rate
    total_fight_time = 0.6 * robust_scale_with_clipping(float(fighter_data['total_fight_time']), 0.0000, 250.3058, 49.9917, 91.7083)
    avg_fight_time = 0.5 * robust_scale_with_clipping(float(fighter_data['avg_fight_time']), 0.0000, 15.0000, 10.5629, 5.1765)
    knockdown_risk =  0.8 * (100 - robust_scale_with_clipping(float(fighter_data['knockdown_risk']), 0.0000, 50.0000, 0.0000, 21.4286))
    knockdown_durability = 0.85 * knockdown_durability
    TDDef = 0.85 * TDDef

    durability_score = round(((losses + ko_losses + ko_risk + sub_losses + sub_risk + knockdown_risk + finish_rate
                               + TDDef + knockdown_durability + total_fight_time + avg_fight_time) / 845) * 100)
    durability_score = max(1, min(durability_score, 100))

    # Recent Performance
    win_rate = 1.00 * robust_scale_with_clipping(float(fighter_data['win_rate']), 0.0000, 100.0000, 63.6364, 27.7778)
    win_streak = 0.80 * min(float(fighter_data['win_streak']), 5.0) # We want the raw value here
    loss_streak = 0.50 * (100 - robust_scale_with_clipping(float(fighter_data['loss_streak']), 0.0000, 5.0000, 1.0000, 2.0000))
    last_five_fight_wins = 0.40 * robust_scale_with_clipping(float(fighter_data['last_five_fight_wins']), 0.0000, 5.0000, 1.0000, 2.0000)
    last_five_fight_losses = 0.50 * (100 - robust_scale_with_clipping(float(fighter_data['last_five_fight_losses']), 0.0000, 5.0000, 2.0000, 2.0000))
    last_five_fight_win_rate = 1.00 * robust_scale_with_clipping(float(fighter_data['last_five_fight_win_rate']), 0.0000, 100.0000, 0.4000, 0.6000)

    recent_performace_score = (win_rate + win_streak + last_five_fight_wins + last_five_fight_win_rate + 
                                     loss_streak + last_five_fight_losses)
    recent_performace_score = round((recent_performace_score / 344) * 100)
    recent_performace_score = max(1, min(recent_performace_score, 100))

    # Prestige Score
    p4p_rank = 1.00 * ((float(fighter_data['p4p_rank']) - 1.0) / (20.0 - 1.0)) * 100
    div_rank = 1.00 * robust_scale_with_clipping(float(fighter_data['div_rank']), 2.0000, 20.0000, 20.0000, 1.0)
    total_fights = 0.80 * robust_scale_with_clipping(float(fighter_data['total_fights']), 0.0000, 22.0000, 5.0000, 8.0000)
    ranked_wins = 1.00 * robust_scale_with_clipping(float(fighter_data['ranked_wins']), 0.0000, 5.0000, 0.0000, 1.0000)
    p4p_wins = 1.00 * ((float(fighter_data['p4p_wins']) - 0.0) / (5.0 - 0.0)) * 100
    champion_wins = 1.25 * ((float(fighter_data['champion_wins']) - 0.0) / (2.0 - 0.0)) * 100
    title_defenses = 1.50 * ((float(fighter_data['title_defenses']) - 0.0) / (10.0 - 0.0)) * 100

    #prestige_score = round((p4p_rank + div_rank + total_fights + ranked_wins + p4p_wins + champion_wins + title_defenses) / 7)
    prestige_score = round(((p4p_rank + div_rank + total_fights + ranked_wins + p4p_wins + champion_wins + title_defenses) / 755.0) * 100)
    prestige_score = max(1, min(prestige_score, 100))

    # Overall
    overall_score = round((striking_score + grappling_score + finish_threat_score + durability_score + recent_performace_score + prestige_score) / 6)
    overall_score = max(1, min(overall_score, 100))

    # Final return data
    fighter_specs = {
        'metadata': {
            'name': fighter_data['name'],
            'age': fighter_data['age'],
            'height': fighter_data['height'],
            'reach': fighter_data['reach'],
            'wins': fighter_data['wins'],
            'losses': fighter_data['losses'],
            'total_fights': fighter_data['total_fights']
        },
        'striking': striking_score,
        'grappling': grappling_score,
        'finish_threat': finish_threat_score,
        'durability': durability_score,
        'recent_performance': recent_performace_score,
        'prestige': prestige_score,
        'overall': overall_score
    }

    return fighter_specs

@head_to_head_api.route('/head-to-head', methods=['GET'])
def predict():
    print("Received Get /api/head-to-head")

    fighter_a_id = request.args.get('fighter_a_id')
    fighter_b_id = request.args.get('fighter_b_id')

    fighter_a_data = get_fighter_by_id(fighter_a_id)
    fighter_b_data = get_fighter_by_id(fighter_b_id)

    # Fighter Data
    fighter_a_specs = calculateFighterSpecs(fighter_a_data)
    fighter_b_specs = calculateFighterSpecs(fighter_b_data)

    response = {
        'fighter_a_specs': fighter_a_specs,
        'fighter_b_specs': fighter_b_specs,
    }

    return jsonify(response)