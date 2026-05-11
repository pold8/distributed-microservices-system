import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/movie/<int:movie_id>")
def gateway(movie_id):
    try:
        r = requests.get(f"http://localhost:5001/movie/{movie_id}", timeout=5)
        return jsonify(r.json()), r.status_code
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Movie service unavailable"}), 503
    except requests.exceptions.Timeout:
        return jsonify({"error": "Movie service timed out"}), 504

if __name__ == "__main__":
    app.run(port=5000)