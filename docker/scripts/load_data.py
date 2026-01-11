#!/usr/bin/env python3
"""Load all data into Storm-Logos databases.

This script initializes both PostgreSQL and Neo4j with:
1. Word coordinates (PostgreSQL)
2. Book corpus with FOLLOWS edges (Neo4j)

Usage:
    python load_data.py                    # Load all data
    python load_data.py --coordinates      # Only load coordinates
    python load_data.py --books            # Only process books
    python load_data.py --books --limit 5  # Process first 5 books
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add storm_logos to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def wait_for_postgres(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready."""
    import psycopg2

    print("Waiting for PostgreSQL...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=os.environ.get('POSTGRES_HOST', 'localhost'),
                port=int(os.environ.get('POSTGRES_PORT', 5432)),
                database=os.environ.get('POSTGRES_DB', 'semantic'),
                user=os.environ.get('POSTGRES_USER', 'postgres'),
                password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
            )
            conn.close()
            print("PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError:
            print(f"  Attempt {i+1}/{max_retries}...")
            time.sleep(delay)
    return False


def wait_for_neo4j(max_retries=30, delay=2):
    """Wait for Neo4j to be ready."""
    from neo4j import GraphDatabase

    print("Waiting for Neo4j...")
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'password')

    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                session.run("RETURN 1")
            driver.close()
            print("Neo4j is ready!")
            return True
        except Exception:
            print(f"  Attempt {i+1}/{max_retries}...")
            time.sleep(delay)
    return False


def load_coordinates(json_path: str):
    """Load coordinates from JSON file into PostgreSQL."""
    import psycopg2

    print(f"\n{'='*60}")
    print("Loading Word Coordinates into PostgreSQL")
    print(f"{'='*60}\n")

    print(f"Loading from: {json_path}")

    with open(json_path, 'r') as f:
        raw_data = json.load(f)

    # Handle nested structure with 'coordinates' key
    if isinstance(raw_data, dict) and 'coordinates' in raw_data:
        data = raw_data['coordinates']
    else:
        data = raw_data

    print(f"Found {len(data):,} words in JSON")

    conn = psycopg2.connect(
        host=os.environ.get('POSTGRES_HOST', 'localhost'),
        port=int(os.environ.get('POSTGRES_PORT', 5432)),
        database=os.environ.get('POSTGRES_DB', 'semantic'),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres')
    )
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS word_coordinates (
            word VARCHAR(100) PRIMARY KEY,
            A FLOAT NOT NULL DEFAULT 0.0,
            S FLOAT NOT NULL DEFAULT 0.0,
            tau FLOAT NOT NULL DEFAULT 2.5,
            source VARCHAR(50) DEFAULT 'json',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()

    # Batch insert
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
                SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau
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
            SET A = EXCLUDED.A, S = EXCLUDED.S, tau = EXCLUDED.tau
        """, batch)
        conn.commit()
        total += len(batch)

    cur.close()
    conn.close()

    print(f"\nLoaded {total:,} word coordinates into PostgreSQL")
    return total


def load_books(gutenberg_dir: str, limit: int = None, priority_only: bool = False):
    """Process books and load into Neo4j."""
    from storm_logos.data.book_parser import BookProcessor

    print(f"\n{'='*60}")
    print("Processing Books into Neo4j")
    print(f"{'='*60}\n")

    gutenberg_path = Path(gutenberg_dir)
    if not gutenberg_path.exists():
        print(f"Warning: Gutenberg directory not found: {gutenberg_dir}")
        return 0

    processor = BookProcessor()

    print("Connecting to Neo4j...")
    if not processor.connect():
        print("ERROR: Could not connect to Neo4j")
        return 0

    print("Connected!")

    # Priority books (Jung + Mythology + Freud + Bible)
    priority_patterns = [
        '*Jung*', '*jung*',
        '*Freud*', '*freud*',
        '*myth*', '*Myth*',
        '*Bible*', '*bible*',
        '*Homer*', '*homer*', '*Odyssey*',
        '*Dostoevsky*', '*dostoevsky*',
        '*Otto Rank*',
    ]

    if priority_only:
        # Find priority books
        book_files = []
        for pattern in priority_patterns:
            book_files.extend(gutenberg_path.glob(pattern))
        book_files = list(set(book_files))
        print(f"Found {len(book_files)} priority books")
    else:
        book_files = list(gutenberg_path.glob('*.txt'))
        print(f"Found {len(book_files)} total books")

    if limit:
        book_files = book_files[:limit]
        print(f"Processing first {limit} books")

    # Process books
    start_time = datetime.now()
    results = []

    for i, book_file in enumerate(book_files, 1):
        print(f"\n[{i}/{len(book_files)}] Processing: {book_file.name}")
        try:
            result = processor.process_book(book_file)
            results.append(result)
            if 'error' not in result:
                print(f"  -> {result['n_bonds']:,} bonds, {result['n_sentences']} sentences")
        except Exception as e:
            print(f"  -> ERROR: {e}")
            results.append({'error': str(e), 'file': str(book_file)})

    end_time = datetime.now()

    # Summary
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")

    total_bonds = sum(r.get('n_bonds', 0) for r in results if 'error' not in r)
    successful = sum(1 for r in results if 'error' not in r)
    failed = sum(1 for r in results if 'error' in r)

    print(f"Time: {end_time - start_time}")
    print(f"Books: {successful} successful, {failed} failed")
    print(f"Total bonds: {total_bonds:,}")

    # Neo4j stats
    try:
        stats = processor.neo4j.stats()
        print(f"\nNeo4j Stats:")
        print(f"  Authors: {stats.get('n_authors', 0)}")
        print(f"  Books: {stats.get('n_books', 0)}")
        print(f"  Bonds: {stats.get('n_bonds', 0):,}")
        print(f"  FOLLOWS edges: {stats.get('n_follows', 0):,}")
    except Exception as e:
        print(f"Warning: Could not get Neo4j stats: {e}")

    return total_bonds


def main():
    parser = argparse.ArgumentParser(description='Load data into Storm-Logos databases')

    parser.add_argument('--coordinates', action='store_true',
                        help='Load word coordinates into PostgreSQL')
    parser.add_argument('--books', action='store_true',
                        help='Process books into Neo4j')
    parser.add_argument('--priority', action='store_true',
                        help='Only process priority books (Jung, Freud, Mythology)')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of books to process')
    parser.add_argument('--coordinates-file', type=str,
                        default='/app/data/coordinates/derived_coordinates.json',
                        help='Path to coordinates JSON file')
    parser.add_argument('--gutenberg-dir', type=str,
                        default='/app/data/gutenberg',
                        help='Path to Gutenberg books directory')
    parser.add_argument('--wait', action='store_true',
                        help='Wait for databases to be ready')

    args = parser.parse_args()

    # Default: load everything
    if not args.coordinates and not args.books:
        args.coordinates = True
        args.books = True

    print(f"\n{'='*60}")
    print("Storm-Logos Data Loader")
    print(f"{'='*60}")
    print(f"Time: {datetime.now().isoformat()}")

    # Wait for databases if requested
    if args.wait:
        if args.coordinates:
            if not wait_for_postgres():
                print("ERROR: PostgreSQL not ready")
                sys.exit(1)

        if args.books:
            if not wait_for_neo4j():
                print("ERROR: Neo4j not ready")
                sys.exit(1)

    # Load coordinates
    if args.coordinates:
        coord_paths = [
            args.coordinates_file,
            '/home/chukiss/text_project/hypothesis/experiments/semantic_llm/experiments/meaning_chain/data/derived_coordinates.json',
            './data/coordinates/derived_coordinates.json',
            '../data/coordinates/derived_coordinates.json',
        ]

        coord_file = None
        for path in coord_paths:
            if Path(path).exists():
                coord_file = path
                break

        if coord_file:
            load_coordinates(coord_file)
        else:
            print("Warning: Could not find coordinates file")
            print("Tried:", coord_paths)

    # Load books
    if args.books:
        gutenberg_paths = [
            args.gutenberg_dir,
            '/home/chukiss/text_project/data/gutenberg',
            './data/gutenberg',
        ]

        gutenberg_dir = None
        for path in gutenberg_paths:
            if Path(path).exists():
                gutenberg_dir = path
                break

        if gutenberg_dir:
            load_books(gutenberg_dir, args.limit, args.priority)
        else:
            print("Warning: Could not find Gutenberg directory")
            print("Tried:", gutenberg_paths)

    print(f"\n{'='*60}")
    print("Data loading complete!")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
