import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

MOVIE_SERVICE_URL = "http://localhost:5001"


@app.route("/movie/<int:movie_id>")
def gateway_movie(movie_id):
    try:
        resp = requests.get(
            f"{MOVIE_SERVICE_URL}/movie/{movie_id}",
            timeout=5
        )
        return jsonify(resp.json()), resp.status_code

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Movie service is unreachable"}), 503

    except requests.exceptions.Timeout:
        return jsonify({"error": "Movie service timed out"}), 504


@app.route("/circuit-status")
def gateway_circuit():
    try:
        resp = requests.get(f"{MOVIE_SERVICE_URL}/circuit-status", timeout=3)
        return jsonify(resp.json()), resp.status_code
    except Exception:
        return jsonify({"error": "Movie service unreachable"}), 503


@app.route("/health")
def health():
    return jsonify({"service": "api_gateway", "status": "ok"})


if __name__ == "__main__":
    app.run(port=5000, debug=False)