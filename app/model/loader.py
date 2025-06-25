import joblib
import os

# sport_id = String, the id of a paticular sport to access a model for (ex. "UFC", "Tennis", etc.)
# default to UFC
def get_model(sport_id='UFC'):
    base_dir = os.path.dirname(__file__)  # path to app/model/
    sport_folder = os.path.join(base_dir, "models", sport_id)
    for file in os.listdir(sport_folder):
        if "model" in file:
            model_path = os.path.join(sport_folder, file)
            return joblib.load(model_path)
    raise FileNotFoundError(f"No model file found in {sport_folder}")

# default to UFC
def get_scaler(sport_id='UFC'):
    base_dir = os.path.dirname(__file__)
    sport_folder = os.path.join(base_dir, "models", sport_id)
    for file in os.listdir(sport_folder):
        if "scaler" in file:
            scaler_path = os.path.join(sport_folder, file)
            return joblib.load(scaler_path)
    raise FileNotFoundError(f"No scaler file found in {sport_folder}")