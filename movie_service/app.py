import requests, time
from flask import Flask, jsonify

app = Flask(__name__)

# --- Circuit Breaker State ---
FAILURE_THRESHOLD = 3
RECOVERY_TIMEOUT  = 10   # seconds before trying again

cb_failures   = 0
cb_open_since = None   # when the circuit tripped

FALLBACK_MOVIES = ["The Matrix", "Inception", "Interstellar"]

MOVIES = {
    1: "The Dark Knight",
    2: "Pulp Fiction",
    3: "Fight Club",
    4: "Goodfellas",
    5: "The Shawshank Redemption",
}

def circuit_is_open():
    global cb_open_since
    if cb_open_since and (time.time() - cb_open_since) > RECOVERY_TIMEOUT:
        cb_open_since = None   # move to half-open: allow one attempt
        return False
    return cb_open_since is not None

def record_failure():
    global cb_failures, cb_open_since
    cb_failures += 1
    if cb_failures >= FAILURE_THRESHOLD:
        cb_open_since = time.time()

def record_success():
    global cb_failures, cb_open_since
    cb_failures   = 0
    cb_open_since = None

def get_recommendations():
    if circuit_is_open():
        return None, "circuit_open"
    try:
        r = requests.get("http://localhost:5002/recommendations", timeout=1.5)
        r.raise_for_status()
        record_success()
        return r.json()["movie_ids"], None
    except Exception as e:
        record_failure()
        return None, str(e)

@app.route("/movie/<int:movie_id>")
def movie_page(movie_id):
    title = MOVIES.get(movie_id, "Unknown Movie")
    ids, err = get_recommendations()

    if ids:
        similar = [MOVIES.get(i, "Unknown") for i in ids if i != movie_id]
        source  = "recommendation_service"
    else:
        similar = FALLBACK_MOVIES   # graceful degradation
        source  = "fallback"

    return jsonify({
        "movie":   title,
        "similar": similar,
        "source":  source,
        "circuit": "open" if circuit_is_open() else "closed",
    })

if __name__ == "__main__":
    app.run(port=5001)