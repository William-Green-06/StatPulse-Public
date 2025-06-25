from app.model.loader import get_model
from app.model.loader import get_scaler
import numpy as np

# load model and scaler
model = get_model(sport_id='UFC')
scaler = get_scaler(sport_id='UFC')

def american_odds_to_prob(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)

def normalize_probs(prob_a, prob_b):
    total = prob_a + prob_b
    return ((prob_a / total) * 100), ((prob_b / total) * 100)

def parse_odds(odds_1, odds_2):
    fighter_1_prob = american_odds_to_prob(odds_1)
    fighter_2_prob = american_odds_to_prob(odds_2)

    fighter_1_prob, fighter_2_prob = normalize_probs(fighter_1_prob, fighter_2_prob)
    return (fighter_1_prob, fighter_2_prob)

def predict_matchup(fighter_a_data, fighter_b_data):
    # first, let's clean the info and get rid of metadata
    fighter_a_data.pop("id", None)
    fighter_a_data.pop("name", None)
    fighter_b_data.pop("id", None)
    fighter_b_data.pop("name", None)

    no_odds = False
    # Next, lets check if odds are specified, and set them to 100 if they aren't
    if fighter_a_data['odds'] == None or fighter_b_data['odds'] == None:
        fighter_a_data['odds'] = 100
        fighter_b_data['odds'] = 100
        no_odds = True

    parsed_odds = parse_odds(fighter_a_data['odds'], fighter_b_data['odds'])
    fighter_a_data['odds'] = parsed_odds[0]
    fighter_b_data['odds'] = parsed_odds[1]
    
    # Now, we can make a prediction, flip the data, predict again, average, then return
    input = [fighter_a_data[key] - fighter_b_data[key] for key in fighter_a_data]
    # print()
    # print(input)
    # print()

    x = np.array(input).reshape(1, -1)
    x_scaled = scaler.transform(x)
    prediction_a = model.predict_proba(x_scaled).reshape(-1)

    x_mirror = -x

    print(x_mirror.tolist())

    x_mirror_scaled = scaler.transform(x_mirror)
    prediction_b = model.predict_proba(x_mirror_scaled).reshape(-1)

    prediction = (prediction_a[1] + prediction_b[0]) / 2

    return prediction, no_odds