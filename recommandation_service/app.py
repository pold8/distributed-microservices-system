import os, time, random
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/recommendations")
def recommendations():
    # CHAOS MODE — enabled via env variable
    if os.environ.get("CHAOS_MODE") == "1":
        if random.random() < 0.5:           # 50% chance of failure
            return jsonify({"error": "Service unavailable"}), 503
        time.sleep(random.uniform(3, 10))   # latency spike

    return jsonify({"movie_ids": [1, 2, 3, 4, 5]})

if __name__ == "__main__":
    app.run(port=5002)