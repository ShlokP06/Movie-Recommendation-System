from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import pickle
import numpy as np
from flask_cors import CORS
from train import improved_recommendations, user_based, hybrid
app = Flask(__name__)
CORS(app)

print("Loading processed data files...")
movies = pd.read_csv("processed\processed_metadata.csv")
ratings = pd.read_csv("processed\processed_ratings.csv")
cosine_sim = np.load("cosine_sim.npy")
with open("svd.pkl", "rb") as f:
    svd_model = pickle.load(f)
print("Processed data & models loaded successfully!")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    method = data.get("method")
    if method == "Content":
        title=data.get("title")
        recs = improved_recommendations(title)
    elif method =="Collaborative":
        user_id=int(data.get("userId"))
        recs = user_based(user_id,svd_model)
    elif method == "Hybrid":
        user_id = int(data.get("userId"))
        title = data.get("title")
        recs = hybrid(user_id, title)
    else:
        return jsonify({"error": "Invalid method"}), 400    
    print("Received request:", data)
    
    if isinstance(recs, pd.DataFrame):
        recs_json = json.loads(recs.to_json(orient="records"))
    else:
        recs_json = recs.tolist() if hasattr(recs, "tolist") else recs

    print("Generated Recommendations:", recs_json[:5])
    return jsonify(recs_json)

if __name__ == "__main__":
    app.run(debug=True)
