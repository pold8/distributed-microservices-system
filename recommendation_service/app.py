import os
import sys
import time
import random

from flask import Flask, jsonify

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from db import init_db, get_connection

app = Flask(__name__)

init_db()


@app.route("/recommendations/<int:movie_id>")
def recommendations(movie_id):
    if os.environ.get("CHAOS_MODE") == "1":
        if random.random() < 0.5:
            return jsonify({"error": "Service unavailable"}), 503
        time.sleep(random.uniform(3, 10))

    conn = get_connection()
    cur  = conn.cursor()
    cur.execute(
        """
        SELECT recommended_movie_id
        FROM   recommendations
        WHERE  movie_id = ?
        """,
        (movie_id,)
    )
    rows = cur.fetchall()
    conn.close()

    if rows:
        movie_ids = [row["recommended_movie_id"] for row in rows]
    else:
        cur2 = get_connection().cursor()
        cur2.execute(
            "SELECT id FROM movies WHERE id != ? LIMIT 5",
            (movie_id,)
        )
        movie_ids = [r["id"] for r in cur2.fetchall()]

    return jsonify({"movie_id": movie_id, "recommended_ids": movie_ids})


@app.route("/health")
def health():
    return jsonify({"service": "recommendation_service", "status": "ok"})


if __name__ == "__main__":
    app.run(port=5002, debug=False)