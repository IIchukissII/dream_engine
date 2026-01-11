#!/usr/bin/env python3
"""Initialize Neo4j with all data.

This script loads:
1. Bond nodes from neo4j_bonds.csv (85K bonds with A, S, tau)
2. FOLLOWS edges from neo4j_follows.csv (154K edges)
3. Books and Authors from neo4j_books.csv (27 books)

Usage:
    python init_neo4j.py

Or with Docker:
    docker exec storm-api python /app/scripts/init_neo4j.py
"""

import csv
import os
import sys
import time
from pathlib import Path

from neo4j import GraphDatabase


def get_driver(max_retries=30, delay=2):
    """Get Neo4j driver with retry."""
    uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    user = os.environ.get('NEO4J_USER', 'neo4j')
    password = os.environ.get('NEO4J_PASSWORD', 'password')

    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            driver.verify_connectivity()
            return driver
        except Exception as e:
            print(f"  Waiting for Neo4j... ({i+1}/{max_retries})")
            time.sleep(delay)

    raise Exception("Could not connect to Neo4j")


def create_indexes(driver):
    """Create indexes and constraints."""
    print("\n=== Creating Indexes ===")

    queries = [
        "CREATE INDEX bond_id IF NOT EXISTS FOR (b:Bond) ON (b.id)",
        "CREATE INDEX bond_adj IF NOT EXISTS FOR (b:Bond) ON (b.adj)",
        "CREATE INDEX bond_noun IF NOT EXISTS FOR (b:Bond) ON (b.noun)",
        "CREATE INDEX author_name IF NOT EXISTS FOR (a:Author) ON (a.name)",
        "CREATE INDEX book_id IF NOT EXISTS FOR (b:Book) ON (b.id)",
        "CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:User) REQUIRE u.user_id IS UNIQUE",
        "CREATE CONSTRAINT username IF NOT EXISTS FOR (u:User) REQUIRE u.username IS UNIQUE",
    ]

    with driver.session() as session:
        for query in queries:
            try:
                session.run(query)
                print(f"  {query[:50]}...")
            except Exception as e:
                print(f"  Warning: {e}")

    print("Indexes created")


def load_bonds(driver, csv_path: str):
    """Load Bond nodes from CSV."""
    print(f"\n=== Loading Bond Nodes ===")
    print(f"From: {csv_path}")

    total = 0
    batch = []
    batch_size = 5000

    with driver.session() as session:
        with open(csv_path, 'r') as f:
            for line in f:
                # Format: "id", "adj", "noun", A, S, tau, "source"
                parts = line.strip().split(', ')
                if len(parts) >= 6:
                    bond_id = parts[0].strip('"')
                    adj = parts[1].strip('"')
                    noun = parts[2].strip('"')
                    try:
                        A = float(parts[3])
                        S = float(parts[4])
                        tau = float(parts[5])
                    except ValueError:
                        continue
                    source = parts[6].strip('"') if len(parts) > 6 else 'corpus'

                    batch.append({
                        'id': bond_id,
                        'adj': adj,
                        'noun': noun,
                        'A': A,
                        'S': S,
                        'tau': tau,
                        'source': source
                    })

                    if len(batch) >= batch_size:
                        session.run("""
                            UNWIND $batch AS b
                            CREATE (bond:Bond {
                                id: b.id,
                                adj: b.adj,
                                noun: b.noun,
                                A: b.A,
                                S: b.S,
                                tau: b.tau,
                                source: b.source
                            })
                        """, batch=batch)
                        total += len(batch)
                        print(f"  Loaded {total:,} bonds...")
                        batch = []

        if batch:
            session.run("""
                UNWIND $batch AS b
                CREATE (bond:Bond {
                    id: b.id,
                    adj: b.adj,
                    noun: b.noun,
                    A: b.A,
                    S: b.S,
                    tau: b.tau,
                    source: b.source
                })
            """, batch=batch)
            total += len(batch)

    print(f"Loaded {total:,} Bond nodes")
    return total


def load_follows(driver, csv_path: str):
    """Load FOLLOWS edges from CSV."""
    print(f"\n=== Loading FOLLOWS Edges ===")
    print(f"From: {csv_path}")

    total = 0
    batch = []
    batch_size = 5000
    skipped = 0

    with driver.session() as session:
        with open(csv_path, 'r') as f:
            for line in f:
                # Format: "from_id", "to_id", weight/NULL, "source", "book_id"
                parts = line.strip().split(', ')
                if len(parts) >= 4:
                    from_id = parts[0].strip('"')
                    to_id = parts[1].strip('"')

                    # Skip self-loops
                    if from_id == to_id:
                        skipped += 1
                        continue

                    weight_str = parts[2]
                    weight = 1.0 if weight_str == 'NULL' else float(weight_str)
                    source = parts[3].strip('"')

                    batch.append({
                        'from_id': from_id,
                        'to_id': to_id,
                        'weight': weight,
                        'source': source
                    })

                    if len(batch) >= batch_size:
                        result = session.run("""
                            UNWIND $batch AS e
                            MATCH (a:Bond {id: e.from_id})
                            MATCH (b:Bond {id: e.to_id})
                            CREATE (a)-[:FOLLOWS {weight: e.weight, source: e.source}]->(b)
                        """, batch=batch)
                        total += len(batch)
                        print(f"  Loaded {total:,} edges...")
                        batch = []

        if batch:
            session.run("""
                UNWIND $batch AS e
                MATCH (a:Bond {id: e.from_id})
                MATCH (b:Bond {id: e.to_id})
                CREATE (a)-[:FOLLOWS {weight: e.weight, source: e.source}]->(b)
            """, batch=batch)
            total += len(batch)

    print(f"Loaded {total:,} FOLLOWS edges (skipped {skipped} self-loops)")
    return total


def load_books(driver, csv_path: str):
    """Load Books and Authors from CSV."""
    print(f"\n=== Loading Books and Authors ===")
    print(f"From: {csv_path}")

    with driver.session() as session:
        with open(csv_path, 'r') as f:
            for line in f:
                # Format: "author", "book_id", "title", "filename"
                parts = line.strip().split(', ')
                if len(parts) >= 4:
                    author = parts[0].strip('"')
                    book_id = parts[1].strip('"')
                    title = parts[2].strip('"')
                    filename = parts[3].strip('"')

                    session.run("""
                        MERGE (a:Author {name: $author})
                        CREATE (b:Book {id: $book_id, title: $title, filename: $filename})
                        CREATE (a)-[:WROTE]->(b)
                    """, author=author, book_id=book_id, title=title, filename=filename)

        # Count
        result = session.run("MATCH (b:Book) RETURN count(b) as count")
        n_books = result.single()['count']
        result = session.run("MATCH (a:Author) RETURN count(a) as count")
        n_authors = result.single()['count']

    print(f"Loaded {n_books} books, {n_authors} authors")
    return n_books


def main():
    print("=" * 60)
    print("Storm-Logos Neo4j Initialization")
    print("=" * 60)

    # Find data files
    data_paths = [
        '/app/data/backup',
        '/home/chukiss/dream_engine/data/backup',
        './data/backup',
    ]

    data_dir = None
    for path in data_paths:
        if Path(path).exists():
            data_dir = Path(path)
            break

    if not data_dir:
        print("ERROR: Could not find data/backup directory")
        sys.exit(1)

    print(f"Data directory: {data_dir}")

    # Connect to Neo4j
    print("\nConnecting to Neo4j...")
    driver = get_driver()
    print("Connected!")

    # Create indexes first
    create_indexes(driver)

    # Load data
    bonds_file = data_dir / 'neo4j_bonds.csv'
    if bonds_file.exists():
        load_bonds(driver, str(bonds_file))

    follows_file = data_dir / 'neo4j_follows.csv'
    if follows_file.exists():
        load_follows(driver, str(follows_file))

    books_file = data_dir / 'neo4j_books.csv'
    if books_file.exists():
        load_books(driver, str(books_file))

    # Summary
    with driver.session() as session:
        result = session.run("MATCH (b:Bond) RETURN count(b) as count")
        n_bonds = result.single()['count']
        result = session.run("MATCH ()-[r:FOLLOWS]->() RETURN count(r) as count")
        n_follows = result.single()['count']
        result = session.run("MATCH (b:Book) RETURN count(b) as count")
        n_books = result.single()['count']

    driver.close()

    print("\n" + "=" * 60)
    print("Neo4j Initialization Complete")
    print("=" * 60)
    print(f"  Bond nodes: {n_bonds:,}")
    print(f"  FOLLOWS edges: {n_follows:,}")
    print(f"  Books: {n_books}")


if __name__ == '__main__':
    main()
