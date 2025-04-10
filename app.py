from flask import Flask, render_template, request, jsonify
import pandas as pd
import json
import numpy as np
from flask_cors import CORS
import joblib
from main import improved_recommendations, user_based, hybrid
app = Flask(__name__)
CORS(app)

print("Loading processed data files...")
movies = pd.read_csv("processed\processed_metadata.csv")
ratings = pd.read_csv("processed\processed_ratings.csv")
cosine_sim = np.load("models\cosine_sim.npy")
smd = pd.read_csv("processed\smd.csv")
id_map = pd.read_csv("processed\map.csv")
indices_map = pd.read_csv("processed\indmap.csv")
svd_model = joblib.load("models\model_compressed.pkl")
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
        recs = improved_recommendations(title,cosine_sim,smd)
        if recs is str:
            return jsonify({"error":"Movie not found in database.."}), 400
    elif method =="Collaborative":
        user_id_r=data.get("userId")
        if user_id_r is not None:
            user_id = int(user_id_r)
            if user_id<=0:
                return jsonify({"error": "Invalid user ID"}),400
        else:
            return jsonify({"error": "Invalid user ID"}),400
        recs = user_based(user_id,svd_model,smd,id_map,indices_map)
        if recs is str:
            return jsonify({"error":"User not found in database.."}),400
    elif method == "Hybrid":
        user_id_r=data.get("userId")
        if user_id_r is not None:
            user_id = int(user_id_r)
            if user_id<=0:
                return jsonify({"error": "Invalid user ID"}),400
        else:
            return jsonify({"error": "Invalid user ID"}),400
        title = data.get("title")
        recs = hybrid(user_id, title, id_map, cosine_sim, smd,svd_model)
        if recs is str:
            return jsonify({"error":"Movie not found in database.."})
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
    app.run(debug=False)
