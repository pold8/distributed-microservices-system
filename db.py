import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "movies.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id          INTEGER PRIMARY KEY,
            title       TEXT    NOT NULL,
            description TEXT    NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            movie_id            INTEGER NOT NULL,
            recommended_movie_id INTEGER NOT NULL,
            PRIMARY KEY (movie_id, recommended_movie_id)
        )
    """)

    cur.execute("SELECT COUNT(*) FROM movies")
    if cur.fetchone()[0] == 0:
        movies = [
            (1, "The Dark Knight",            "Batman faces the Joker in Gotham City."),
            (2, "Pulp Fiction",               "Interconnected stories of crime in LA."),
            (3, "Fight Club",                 "An insomniac forms an underground fight club."),
            (4, "Goodfellas",                 "Rise and fall of a mob associate."),
            (5, "The Shawshank Redemption",   "Two imprisoned men bond over years."),
            (6, "Inception",                  "A thief enters dreams to plant an idea."),
            (7, "Interstellar",               "Astronauts travel through a wormhole."),
            (8, "The Matrix",                 "A hacker discovers reality is a simulation."),
            (9, "Se7en",                      "Detectives hunt a serial killer."),
            (10,"Forrest Gump",               "Life story of a man with a low IQ."),
        ]
        cur.executemany(
            "INSERT INTO movies (id, title, description) VALUES (?, ?, ?)",
            movies
        )

    cur.execute("SELECT COUNT(*) FROM recommendations")
    if cur.fetchone()[0] == 0:
        pairs = [
            # For movie 1 (Dark Knight) → recommend 2,6,9
            (1, 2), (1, 6), (1, 9),
            # For movie 2 (Pulp Fiction) → recommend 3,4,9
            (2, 3), (2, 4), (2, 9),
            # For movie 3 (Fight Club)   → recommend 2,6,8
            (3, 2), (3, 6), (3, 8),
            # For movie 4 (Goodfellas)   → recommend 2,3,9
            (4, 2), (4, 3), (4, 9),
            # For movie 5 (Shawshank)    → recommend 10,7,6
            (5, 10),(5, 7), (5, 6),
            # For movie 6 (Inception)    → recommend 7,8,3
            (6, 7), (6, 8), (6, 3),
            # For movie 7 (Interstellar) → recommend 6,8,5
            (7, 6), (7, 8), (7, 5),
            # For movie 8 (The Matrix)   → recommend 6,7,3
            (8, 6), (8, 7), (8, 3),
            # For movie 9 (Se7en)        → recommend 1,2,4
            (9, 1), (9, 2), (9, 4),
            # For movie 10 (Forrest Gump)→ recommend 5,7,10 — note 10→self excluded in query
            (10,5), (10,7),
        ]
        cur.executemany(
            "INSERT INTO recommendations (movie_id, recommended_movie_id) VALUES (?, ?)",
            pairs
        )

    conn.commit()
    conn.close()
    print(f"[db] Database ready at {DB_PATH}")