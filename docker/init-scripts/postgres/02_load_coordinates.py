#!/usr/bin/env python3
"""Load semantic coordinates into PostgreSQL.

This script loads derived_coordinates.json into the word_coordinates table.
Run after the database schema is created.

Usage:
    python 02_load_coordinates.py

Or via Docker:
    docker exec -it storm-postgres psql -U postgres -d semantic -c "\\i /docker-entrypoint-initdb.d/02_load_coordinates.sql"
"""

import json
import os
import sys
import psycopg2
from pathlib import Path


def get_connection():
    """Get PostgreSQL connection."""
    return psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'localhost'),
        port=int(os.environ.get('POSTGRES_PORT', 5432)),
        database=os.environ.get('POSTGRES_DB', 'semantic'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
    )


def load_coordinates(json_path: str):
    """Load coordinates from JSON file into PostgreSQL."""
    print(f"Loading coordinates from {json_path}...")

    with open(json_path, 'r') as f:
        data = json.load(f)

    conn = get_connection()
    cur = conn.cursor()

    # Prepare batch insert
    batch_size = 1000
    batch = []
    total = 0

    for word, coords in data.items():
        if isinstance(coords, dict):
            A = coords.get('A', 0.0)
            S = coords.get('S', 0.0)
            tau = coords.get('tau', 2.5)
        elif isinstance(coords, (list, tuple)) and len(coords) >= 3:
            A, S, tau = coords[0], coords[1], coords[2]
        else:
            continue

        batch.append((word.lower(), float(A), float(S), float(tau), 'json'))

        if len(batch) >= batch_size:
            cur.executemany("""
                INSERT INTO word_coordinates (word, A, S, tau, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (word) DO UPDATE
                SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau, source = EXCLUDED.source
            """, batch)
            conn.commit()
            total += len(batch)
            print(f"  Loaded {total:,} words...")
            batch = []

    # Insert remaining
    if batch:
        cur.executemany("""
            INSERT INTO word_coordinates (word, A, S, tau, source)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (word) DO UPDATE
            SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau, source = EXCLUDED.source
        """, batch)
        conn.commit()
        total += len(batch)

    cur.close()
    conn.close()

    print(f"Loaded {total:,} word coordinates into PostgreSQL")
    return total


def main():
    # Find coordinates file
    paths_to_try = [
        '/app/data/coordinates/derived_coordinates.json',
        '/docker-entrypoint-initdb.d/data/derived_coordinates.json',
        './data/coordinates/derived_coordinates.json',
        '../data/coordinates/derived_coordinates.json',
    ]

    json_path = None
    for path in paths_to_try:
        if Path(path).exists():
            json_path = path
            break

    if not json_path:
        print("Error: Could not find derived_coordinates.json")
        print("Tried:", paths_to_try)
        sys.exit(1)

    load_coordinates(json_path)


if __name__ == '__main__':
    main()
