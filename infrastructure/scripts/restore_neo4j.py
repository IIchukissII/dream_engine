#!/usr/bin/env python3
"""
Restore Neo4j data from backup CSV files.

This script properly handles CSV files with:
- Mixed quoting styles
- Spaces after commas
- Embedded quotes

Usage:
    python restore_neo4j.py [--uri bolt://localhost:7689] [--backup-dir /path/to/backup]
"""

import csv
import os
import sys
import argparse
from typing import List, Dict, Any

try:
    from neo4j import GraphDatabase
except ImportError:
    print("ERROR: neo4j package not installed. Run: pip install neo4j")
    sys.exit(1)


def clean_value(value: str) -> str:
    """Clean a CSV value by removing extra quotes and whitespace."""
    if value is None:
        return ""
    # Strip whitespace
    value = value.strip()
    # Remove surrounding quotes
    if value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    return value.strip()


def clean_float(value: str) -> float:
    """Parse a float value from CSV."""
    cleaned = clean_value(value)
    # Remove any remaining quotes
    cleaned = cleaned.replace('"', '').strip()
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


class Neo4jRestorer:
    def __init__(self, uri: str, user: str, password: str, backup_dir: str):
        self.uri = uri
        self.user = user
        self.password = password
        self.backup_dir = backup_dir
        self.driver = None

    def connect(self) -> bool:
        """Connect to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            # Verify connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception as e:
            print(f"ERROR: Could not connect to Neo4j: {e}")
            return False

    def close(self):
        """Close connection."""
        if self.driver:
            self.driver.close()

    def clear_data(self):
        """Clear existing corpus data (preserves Users)."""
        print("Clearing existing corpus data...")
        with self.driver.session() as session:
            # Delete in order to avoid constraint issues
            session.run("MATCH ()-[r:CONTAINS]->() DELETE r")
            session.run("MATCH ()-[r:FOLLOWS]->() DELETE r")
            session.run("MATCH (b:Bond) DELETE b")
            session.run("MATCH (b:Book) DELETE b")
        print("  Done.")

    def create_indexes(self):
        """Create indexes for faster import."""
        print("Creating indexes...")
        with self.driver.session() as session:
            session.run("CREATE INDEX bond_id_idx IF NOT EXISTS FOR (b:Bond) ON (b.id)")
            session.run("CREATE INDEX book_id_idx IF NOT EXISTS FOR (b:Book) ON (b.id)")
        print("  Done.")

    def import_books(self) -> int:
        """Import books from CSV."""
        filepath = os.path.join(self.backup_dir, 'neo4j_books.csv')
        print(f"Importing books from {filepath}...")

        books = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 4:
                    books.append({
                        'author': clean_value(row[0]),
                        'id': clean_value(row[1]),
                        'title': clean_value(row[2]),
                        'filename': clean_value(row[3])
                    })

        with self.driver.session() as session:
            session.run("""
                UNWIND $books AS book
                CREATE (b:Book {
                    author: book.author,
                    id: book.id,
                    title: book.title,
                    filename: book.filename
                })
            """, books=books)

        print(f"  Imported {len(books)} books.")
        return len(books)

    def import_bonds(self, batch_size: int = 5000) -> int:
        """Import bonds from CSV in batches."""
        filepath = os.path.join(self.backup_dir, 'neo4j_bonds.csv')
        print(f"Importing bonds from {filepath}...")

        total = 0
        batch = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 7:
                    bond = {
                        'id': clean_value(row[0]),
                        'adj': clean_value(row[1]),
                        'noun': clean_value(row[2]),
                        'A': clean_float(row[3]),
                        'S': clean_float(row[4]),
                        'tau': clean_float(row[5]),
                        'source': clean_value(row[6])
                    }
                    batch.append(bond)

                    if len(batch) >= batch_size:
                        self._import_bond_batch(batch)
                        total += len(batch)
                        print(f"  Imported {total:,} bonds...")
                        batch = []

        # Import remaining
        if batch:
            self._import_bond_batch(batch)
            total += len(batch)

        print(f"  Total: {total:,} bonds.")
        return total

    def _import_bond_batch(self, bonds: List[Dict[str, Any]]):
        """Import a batch of bonds."""
        with self.driver.session() as session:
            session.run("""
                UNWIND $bonds AS bond
                CREATE (b:Bond {
                    id: bond.id,
                    adj: bond.adj,
                    noun: bond.noun,
                    A: bond.A,
                    S: bond.S,
                    tau: bond.tau,
                    source: bond.source
                })
            """, bonds=bonds)

    def import_follows(self, batch_size: int = 5000) -> int:
        """Import FOLLOWS relationships from CSV."""
        filepath = os.path.join(self.backup_dir, 'neo4j_follows.csv')
        print(f"Importing FOLLOWS relationships from {filepath}...")

        total = 0
        batch = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= 5:
                    rel = {
                        'from_id': clean_value(row[0]),
                        'to_id': clean_value(row[1]),
                        'source': clean_value(row[3]),
                        'book_id': clean_value(row[4])
                    }
                    batch.append(rel)

                    if len(batch) >= batch_size:
                        self._import_follows_batch(batch)
                        total += len(batch)
                        print(f"  Imported {total:,} relationships...")
                        batch = []

        # Import remaining
        if batch:
            self._import_follows_batch(batch)
            total += len(batch)

        print(f"  Total: {total:,} FOLLOWS relationships.")
        return total

    def _import_follows_batch(self, rels: List[Dict[str, Any]]):
        """Import a batch of FOLLOWS relationships."""
        with self.driver.session() as session:
            session.run("""
                UNWIND $rels AS rel
                MATCH (from:Bond {id: rel.from_id})
                MATCH (to:Bond {id: rel.to_id})
                CREATE (from)-[:FOLLOWS {source: rel.source, book_id: rel.book_id}]->(to)
            """, rels=rels)

    def create_contains_relationships(self) -> int:
        """Create CONTAINS relationships between Books and Bonds."""
        print("Creating Book-Bond CONTAINS relationships...")

        with self.driver.session() as session:
            # Get unique book_ids from FOLLOWS relationships
            result = session.run("""
                MATCH (b:Book)
                MATCH (bond:Bond)-[f:FOLLOWS]->()
                WHERE f.book_id = b.id
                WITH b, collect(DISTINCT bond) AS bonds
                UNWIND bonds AS bond
                MERGE (b)-[:CONTAINS]->(bond)
                RETURN count(*) AS created
            """)
            created = result.single()['created']

        print(f"  Created {created:,} CONTAINS relationships.")
        return created

    def verify(self) -> Dict[str, int]:
        """Verify the imported data."""
        print("\nVerification:")
        print("-" * 40)

        with self.driver.session() as session:
            stats = {}

            result = session.run("MATCH (b:Book) RETURN count(b) as count")
            stats['books'] = result.single()['count']
            print(f"  Books: {stats['books']}")

            result = session.run("MATCH (b:Bond) RETURN count(b) as count")
            stats['bonds'] = result.single()['count']
            print(f"  Bonds: {stats['bonds']:,}")

            result = session.run("MATCH ()-[f:FOLLOWS]->() RETURN count(f) as count")
            stats['follows'] = result.single()['count']
            print(f"  FOLLOWS: {stats['follows']:,}")

            result = session.run("MATCH ()-[c:CONTAINS]->() RETURN count(c) as count")
            stats['contains'] = result.single()['count']
            print(f"  CONTAINS: {stats['contains']:,}")

            # Sample books with bond counts
            print("\n  Sample books:")
            result = session.run("""
                MATCH (b:Book)
                OPTIONAL MATCH (b)-[:CONTAINS]->(bond:Bond)
                RETURN b.title AS title, b.author AS author, count(bond) AS n_bonds
                ORDER BY n_bonds DESC
                LIMIT 5
            """)
            for record in result:
                print(f"    - {record['title']} ({record['author']}): {record['n_bonds']:,} bonds")

        return stats


def main():
    parser = argparse.ArgumentParser(description='Restore Neo4j data from backup')
    parser.add_argument('--uri', default=os.environ.get('NEO4J_URI', 'bolt://localhost:7689'),
                        help='Neo4j URI')
    parser.add_argument('--user', default=os.environ.get('NEO4J_USER', 'neo4j'),
                        help='Neo4j username')
    parser.add_argument('--password', default=os.environ.get('NEO4J_PASSWORD', 'localdevpassword'),
                        help='Neo4j password')
    parser.add_argument('--backup-dir', default='/home/chukiss/dream_engine/data/backup',
                        help='Backup directory path')
    parser.add_argument('--batch-size', type=int, default=5000,
                        help='Batch size for imports')

    args = parser.parse_args()

    print("=" * 60)
    print("Neo4j Data Restore")
    print("=" * 60)
    print(f"URI: {args.uri}")
    print(f"Backup: {args.backup_dir}")
    print()

    # Verify backup files exist
    required_files = ['neo4j_books.csv', 'neo4j_bonds.csv', 'neo4j_follows.csv']
    for filename in required_files:
        filepath = os.path.join(args.backup_dir, filename)
        if not os.path.exists(filepath):
            print(f"ERROR: Required file not found: {filepath}")
            sys.exit(1)

    restorer = Neo4jRestorer(args.uri, args.user, args.password, args.backup_dir)

    try:
        if not restorer.connect():
            sys.exit(1)

        restorer.clear_data()
        restorer.create_indexes()
        restorer.import_books()
        restorer.import_bonds(args.batch_size)
        restorer.import_follows(args.batch_size)
        restorer.create_contains_relationships()

        stats = restorer.verify()

        print()
        print("=" * 60)
        print("RESTORE COMPLETE")
        print("=" * 60)

        # Validate expected counts
        expected_books = 27
        expected_bonds = 85157
        expected_follows = 154393

        if stats['books'] == expected_books:
            print(f"  Books: {stats['books']} OK")
        else:
            print(f"  Books: {stats['books']} (expected {expected_books})")

        if stats['bonds'] == expected_bonds:
            print(f"  Bonds: {stats['bonds']:,} OK")
        else:
            print(f"  Bonds: {stats['bonds']:,} (expected {expected_bonds:,})")

        if stats['follows'] == expected_follows:
            print(f"  FOLLOWS: {stats['follows']:,} OK")
        else:
            print(f"  FOLLOWS: {stats['follows']:,} (expected {expected_follows:,})")

    finally:
        restorer.close()


if __name__ == '__main__':
    main()
