import os
import sys
import time

import requests
from flask import Flask, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db import init_db, get_connection

app = Flask(__name__)

init_db()

FAILURE_THRESHOLD = 3
RECOVERY_TIMEOUT  = 10
REQUEST_TIMEOUT   = 1.5

_cb_failures   = 0
_cb_open_since = None


def _circuit_is_open() -> bool:
    global _cb_open_since
    if _cb_open_since is None:
        return False
    if (time.time() - _cb_open_since) >= RECOVERY_TIMEOUT:
        _cb_open_since = None
        return False
    return True


def _record_success():
    global _cb_failures, _cb_open_since
    _cb_failures   = 0
    _cb_open_since = None


def _record_failure():
    global _cb_failures, _cb_open_since
    _cb_failures += 1
    if _cb_failures >= FAILURE_THRESHOLD:
        _cb_open_since = time.time()


FALLBACK_IDS = [6, 7, 8]


def _get_recommendations(movie_id: int):
    """
    Call the Recommendation Service.
    Returns (list_of_ids, error_reason_or_None).
    """
    if _circuit_is_open():
        return None, "circuit_open"

    try:
        resp = requests.get(
            f"http://localhost:5002/recommendations/{movie_id}",
            timeout=REQUEST_TIMEOUT
        )
        resp.raise_for_status()
        _record_success()
        return resp.json()["recommended_ids"], None

    except requests.exceptions.Timeout:
        _record_failure()
        return None, "timeout"

    except requests.exceptions.HTTPError as e:
        _record_failure()
        return None, f"http_error:{e.response.status_code}"

    except requests.exceptions.ConnectionError:
        _record_failure()
        return None, "connection_error"


def _fetch_movies_by_ids(ids: list) -> list:
    """Return a list of {id, title, description} dicts from the DB."""
    if not ids:
        return []
    placeholders = ",".join("?" * len(ids))
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        f"SELECT id, title, description FROM movies WHERE id IN ({placeholders})",
        ids
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows



@app.route("/movie/<int:movie_id>")
def movie_page(movie_id):
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT id, title, description FROM movies WHERE id = ?", (movie_id,))
    row  = cur.fetchone()
    conn.close()

    if row is None:
        return jsonify({"error": f"Movie {movie_id} not found"}), 404

    movie = dict(row)

    rec_ids, error = _get_recommendations(movie_id)

    if rec_ids:
        similar = _fetch_movies_by_ids(rec_ids)
        source  = "recommendation_service"
    else:
        similar = _fetch_movies_by_ids(FALLBACK_IDS)
        source  = "fallback"

    return jsonify({
        "movie":          movie,
        "similar_movies": similar,
        "source":         source,
        "circuit": {
            "state":    "open" if _circuit_is_open() else "closed",
            "failures": _cb_failures,
        },
        "error": error,
    })


@app.route("/health")
def health():
    return jsonify({"service": "movie_service", "status": "ok"})


@app.route("/circuit-status")
def circuit_status():
    """Handy endpoint to inspect the circuit breaker state."""
    state = "open" if _circuit_is_open() else "closed"
    recovery_in = None
    if _cb_open_since:
        remaining = RECOVERY_TIMEOUT - (time.time() - _cb_open_since)
        recovery_in = max(0, round(remaining, 1))

    return jsonify({
        "state":       state,
        "failures":    _cb_failures,
        "threshold":   FAILURE_THRESHOLD,
        "recovery_in": recovery_in,
    })


if __name__ == "__main__":
    app.run(port=5001, debug=False)