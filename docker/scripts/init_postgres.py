#!/usr/bin/env python3
"""Initialize PostgreSQL with all data.

This script loads:
1. Word coordinates from derived_coordinates.json (27K+ words)
2. Bonds from neo4j_bonds.csv (85K bonds with A, S, tau)
3. Bond vocabulary from hyp_bond_vocab.csv (6M+ corpus bonds)

Usage:
    python init_postgres.py

Or with Docker:
    docker exec storm-postgres python /app/scripts/init_postgres.py
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import psycopg2


def get_connection(max_retries=30, delay=2):
    """Get PostgreSQL connection with retry."""
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.environ.get('POSTGRES_HOST', 'localhost'),
                port=int(os.environ.get('POSTGRES_PORT', 5432)),
                database=os.environ.get('POSTGRES_DB', 'semantic'),
                user=os.environ.get('POSTGRES_USER', 'postgres'),
                password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
            )
            return conn
        except psycopg2.OperationalError:
            print(f"  Waiting for PostgreSQL... ({i+1}/{max_retries})")
            time.sleep(delay)
    raise Exception("Could not connect to PostgreSQL")


def load_coordinates(conn, json_path: str):
    """Load word coordinates from JSON."""
    print(f"\n=== Loading Word Coordinates ===")
    print(f"From: {json_path}")

    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    # Handle nested structure
    if isinstance(raw_data, dict) and 'coordinates' in raw_data:
        data = raw_data['coordinates']
    else:
        data = raw_data

    print(f"Found {len(data):,} words")

    cur = conn.cursor()
    batch_size = 1000
    batch = []
    total = 0

    for word, coords in data.items():
        if isinstance(coords, dict):
            A = coords.get('A', 0.0)
            S = coords.get('S', 0.0)
            tau = coords.get('tau', 2.5)
        else:
            continue

        batch.append((word.lower(), float(A), float(S), float(tau), 'json'))

        if len(batch) >= batch_size:
            cur.executemany("""
                INSERT INTO word_coordinates (word, A, S, tau, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (word) DO UPDATE
                SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau
            """, batch)
            conn.commit()
            total += len(batch)
            batch = []

    if batch:
        cur.executemany("""
            INSERT INTO word_coordinates (word, A, S, tau, source)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (word) DO UPDATE
            SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau
        """, batch)
        conn.commit()
        total += len(batch)

    cur.close()
    print(f"Loaded {total:,} word coordinates")
    return total


def load_bonds(conn, csv_path: str):
    """Load bonds from CSV (85K with pre-computed coords)."""
    print(f"\n=== Loading Bonds ===")
    print(f"From: {csv_path}")

    cur = conn.cursor()
    total = 0

    with open(csv_path, 'r') as f:
        for line in f:
            # Format: "id", "adj", "noun", A, S, tau, "source"
            parts = line.strip().split(', ')
            if len(parts) >= 6:
                adj = parts[1].strip('"')
                noun = parts[2].strip('"')
                try:
                    A = float(parts[3])
                    S = float(parts[4])
                    tau = float(parts[5])
                except ValueError:
                    continue

                cur.execute("""
                    INSERT INTO bonds (adj, noun, A, S, tau)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (adj, noun) DO UPDATE
                    SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau
                """, (adj.lower(), noun.lower(), A, S, tau))
                total += 1

                if total % 10000 == 0:
                    conn.commit()
                    print(f"  Loaded {total:,} bonds...")

    conn.commit()
    cur.close()
    print(f"Loaded {total:,} bonds")
    return total


def load_bond_vocab(conn, csv_path: str):
    """Load bond vocabulary from CSV (6M+ corpus bonds)."""
    print(f"\n=== Loading Bond Vocabulary ===")
    print(f"From: {csv_path}")

    cur = conn.cursor()

    # Use COPY for fast loading
    with open(csv_path, 'r') as f:
        # Skip header
        next(f)
        cur.copy_expert("""
            COPY hyp_bond_vocab (bond, first_seen_order, first_seen_book, total_count, book_count, created_at)
            FROM STDIN WITH CSV
        """, f)

    conn.commit()

    cur.execute("SELECT COUNT(*) FROM hyp_bond_vocab")
    total = cur.fetchone()[0]
    cur.close()

    print(f"Loaded {total:,} bond vocabulary entries")
    return total


def main():
    print("=" * 60)
    print("Storm-Logos PostgreSQL Initialization")
    print("=" * 60)

    # Find data files
    data_paths = [
        '/app/data/backup',
        '/home/chukiss/dream_engine/data/backup',
        './data/backup',
    ]

    coord_paths = [
        '/app/storm_logos/data/derived_coordinates.json',
        '/home/chukiss/dream_engine/storm_logos/data/derived_coordinates.json',
        './storm_logos/data/derived_coordinates.json',
    ]

    data_dir = None
    for path in data_paths:
        if Path(path).exists():
            data_dir = Path(path)
            break

    coord_file = None
    for path in coord_paths:
        if Path(path).exists():
            coord_file = path
            break

    if not data_dir:
        print("ERROR: Could not find data/backup directory")
        sys.exit(1)

    print(f"Data directory: {data_dir}")
    print(f"Coordinates file: {coord_file}")

    # Connect to PostgreSQL
    print("\nConnecting to PostgreSQL...")
    conn = get_connection()
    print("Connected!")

    # Load data
    if coord_file:
        load_coordinates(conn, coord_file)

    bonds_file = data_dir / 'neo4j_bonds.csv'
    if bonds_file.exists():
        load_bonds(conn, str(bonds_file))

    vocab_file = data_dir / 'hyp_bond_vocab.csv'
    if vocab_file.exists():
        load_bond_vocab(conn, str(vocab_file))

    # Summary
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM word_coordinates")
    n_coords = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bonds")
    n_bonds = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM hyp_bond_vocab")
    n_vocab = cur.fetchone()[0]
    cur.close()
    conn.close()

    print("\n" + "=" * 60)
    print("PostgreSQL Initialization Complete")
    print("=" * 60)
    print(f"  word_coordinates: {n_coords:,}")
    print(f"  bonds: {n_bonds:,}")
    print(f"  hyp_bond_vocab: {n_vocab:,}")


if __name__ == '__main__':
    main()
