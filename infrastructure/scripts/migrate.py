#!/usr/bin/env python3
"""
Storm-Logos Migration Script

Exports and imports data from both Neo4j and PostgreSQL for cloud migration.
Creates clean, portable CSV/JSON files.

Usage:
    # Export all data
    python migrate.py export --neo4j-password experience123 --pg-password yourpass

    # Import all data
    python migrate.py import --neo4j-password localdevpassword --pg-password yourpass

    # Export only (for transferring to cloud)
    python migrate.py export-only --neo4j-password experience123 --pg-password yourpass

    # Import only (on cloud server)
    python migrate.py import-only --neo4j-password cloudpass --pg-password cloudpass

    # Verify all data
    python migrate.py verify --neo4j-password localdevpassword --pg-password yourpass
"""

import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Default paths
DEFAULT_EXPORT_DIR = Path(__file__).parent.parent.parent / 'data' / 'migration'
DEFAULT_BACKUP_DIR = Path(__file__).parent.parent.parent / 'data' / 'backup'
DEFAULT_COORDS_DIR = Path(__file__).parent.parent.parent / 'data' / 'coordinates'


# =============================================================================
# NEO4J MIGRATOR
# =============================================================================

class Neo4jMigrator:
    """Handles Neo4j data migration."""

    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def connect(self, uri: str, user: str, password: str):
        """Connect to Neo4j and return driver."""
        try:
            from neo4j import GraphDatabase
        except ImportError:
            print("ERROR: neo4j package not installed. Run: pip install neo4j")
            return None

        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                session.run("RETURN 1")
            return driver
        except Exception as e:
            print(f"ERROR: Could not connect to Neo4j at {uri}: {e}")
            return None

    def export_all(self, uri: str, user: str, password: str) -> Dict[str, int]:
        """Export all data from Neo4j to CSV files."""
        print("-" * 60)
        print("NEO4J EXPORT")
        print("-" * 60)
        print(f"Source: {uri}")

        driver = self.connect(uri, user, password)
        if not driver:
            return {}

        stats = {}
        try:
            with driver.session() as session:
                stats['books'] = self._export_books(session)
                stats['bonds'] = self._export_bonds(session)
                stats['follows'] = self._export_follows(session)
        finally:
            driver.close()

        return stats

    def _export_books(self, session) -> int:
        """Export Book nodes to CSV."""
        filepath = self.export_dir / 'neo4j_books.csv'
        print(f"  Exporting books to {filepath.name}...")

        result = session.run("""
            MATCH (b:Book)
            RETURN b.id AS id, b.title AS title, b.author AS author,
                   b.filename AS filename, b.genre AS genre
            ORDER BY b.author, b.title
        """)

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_ALL)
            writer.writerow(['id', 'title', 'author', 'filename', 'genre'])
            for record in result:
                writer.writerow([
                    record['id'] or '',
                    record['title'] or '',
                    record['author'] or '',
                    record['filename'] or '',
                    record['genre'] or ''
                ])
                count += 1

        print(f"    {count} books")
        return count

    def _export_bonds(self, session) -> int:
        """Export Bond nodes to CSV in batches."""
        filepath = self.export_dir / 'neo4j_bonds.csv'
        print(f"  Exporting bonds to {filepath.name}...")

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['id', 'adj', 'noun', 'A', 'S', 'tau', 'source'])

            skip = 0
            batch_size = 10000

            while True:
                result = session.run("""
                    MATCH (b:Bond)
                    RETURN b.id AS id, b.adj AS adj, b.noun AS noun,
                           b.A AS A, b.S AS S, b.tau AS tau, b.source AS source
                    ORDER BY b.id
                    SKIP $skip LIMIT $limit
                """, skip=skip, limit=batch_size)

                records = list(result)
                if not records:
                    break

                for record in records:
                    writer.writerow([
                        record['id'] or '',
                        record['adj'] or '',
                        record['noun'] or '',
                        record['A'] if record['A'] is not None else 0.0,
                        record['S'] if record['S'] is not None else 0.0,
                        record['tau'] if record['tau'] is not None else 2.5,
                        record['source'] or 'corpus'
                    ])
                    count += 1

                skip += batch_size
                if count % 50000 == 0:
                    print(f"    {count:,} bonds...")

        print(f"    {count:,} bonds total")
        return count

    def _export_follows(self, session) -> int:
        """Export FOLLOWS relationships to CSV in batches."""
        filepath = self.export_dir / 'neo4j_follows.csv'
        print(f"  Exporting FOLLOWS to {filepath.name}...")

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['from_id', 'to_id', 'source', 'book_id'])

            skip = 0
            batch_size = 10000

            while True:
                result = session.run("""
                    MATCH (from:Bond)-[f:FOLLOWS]->(to:Bond)
                    RETURN from.id AS from_id, to.id AS to_id,
                           f.source AS source, f.book_id AS book_id
                    SKIP $skip LIMIT $limit
                """, skip=skip, limit=batch_size)

                records = list(result)
                if not records:
                    break

                for record in records:
                    writer.writerow([
                        record['from_id'] or '',
                        record['to_id'] or '',
                        record['source'] or 'corpus',
                        record['book_id'] or ''
                    ])
                    count += 1

                skip += batch_size
                if count % 50000 == 0:
                    print(f"    {count:,} relationships...")

        print(f"    {count:,} FOLLOWS total")
        return count

    def import_all(self, uri: str, user: str, password: str, batch_size: int = 5000) -> Dict[str, int]:
        """Import all data from CSV files to Neo4j."""
        print("-" * 60)
        print("NEO4J IMPORT")
        print("-" * 60)
        print(f"Target: {uri}")

        # Check for files (try both naming conventions)
        books_file = self._find_file('neo4j_books.csv', 'books.csv')
        bonds_file = self._find_file('neo4j_bonds.csv', 'bonds.csv')
        follows_file = self._find_file('neo4j_follows.csv', 'follows.csv')

        if not all([books_file, bonds_file, follows_file]):
            print("ERROR: Missing required Neo4j CSV files")
            return {}

        driver = self.connect(uri, user, password)
        if not driver:
            return {}

        stats = {}
        try:
            with driver.session() as session:
                self._clear_data(session)
                self._create_indexes(session)
                stats['books'] = self._import_books(session, books_file)
                stats['bonds'] = self._import_bonds(session, bonds_file, batch_size)
                stats['follows'] = self._import_follows(session, follows_file, batch_size)
                stats['contains'] = self._create_contains(session)
        finally:
            driver.close()

        return stats

    def _find_file(self, *names) -> Optional[Path]:
        """Find first existing file from list of names."""
        for name in names:
            filepath = self.export_dir / name
            if filepath.exists():
                return filepath
        print(f"  WARNING: None of {names} found")
        return None

    def _clear_data(self, session):
        """Clear existing corpus data in batches to avoid memory issues."""
        print("  Clearing existing data...")

        # Delete CONTAINS in batches
        while True:
            result = session.run("MATCH ()-[r:CONTAINS]->() WITH r LIMIT 10000 DELETE r RETURN count(r) as deleted")
            deleted = result.single()['deleted']
            if deleted == 0:
                break

        # Delete FOLLOWS in batches
        while True:
            result = session.run("MATCH ()-[r:FOLLOWS]->() WITH r LIMIT 10000 DELETE r RETURN count(r) as deleted")
            deleted = result.single()['deleted']
            if deleted == 0:
                break

        # Delete Bonds in batches
        while True:
            result = session.run("MATCH (b:Bond) WITH b LIMIT 10000 DELETE b RETURN count(b) as deleted")
            deleted = result.single()['deleted']
            if deleted == 0:
                break

        # Delete Books (usually few, can do in one go)
        session.run("MATCH (b:Book) DELETE b")

    def _create_indexes(self, session):
        """Create indexes for faster import."""
        print("  Creating indexes...")
        session.run("CREATE INDEX bond_id_idx IF NOT EXISTS FOR (b:Bond) ON (b.id)")
        session.run("CREATE INDEX book_id_idx IF NOT EXISTS FOR (b:Book) ON (b.id)")

    def _import_books(self, session, filepath: Path) -> int:
        """Import books from CSV."""
        print(f"  Importing books from {filepath.name}...")

        books = []
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                books.append({
                    'id': row['id'],
                    'title': row['title'],
                    'author': row['author'],
                    'filename': row['filename'],
                    'genre': row['genre']
                })

        session.run("""
            UNWIND $books AS book
            CREATE (b:Book {
                id: book.id,
                title: book.title,
                author: book.author,
                filename: book.filename,
                genre: book.genre
            })
        """, books=books)

        print(f"    {len(books)} books")
        return len(books)

    def _import_bonds(self, session, filepath: Path, batch_size: int) -> int:
        """Import bonds from CSV in batches."""
        print(f"  Importing bonds from {filepath.name}...")

        total = 0
        batch = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                batch.append({
                    'id': row['id'],
                    'adj': row['adj'],
                    'noun': row['noun'],
                    'A': float(row['A']) if row['A'] else 0.0,
                    'S': float(row['S']) if row['S'] else 0.0,
                    'tau': float(row['tau']) if row['tau'] else 2.5,
                    'source': row['source']
                })

                if len(batch) >= batch_size:
                    self._insert_bonds_batch(session, batch)
                    total += len(batch)
                    if total % 50000 == 0:
                        print(f"    {total:,} bonds...")
                    batch = []

        if batch:
            self._insert_bonds_batch(session, batch)
            total += len(batch)

        print(f"    {total:,} bonds total")
        return total

    def _insert_bonds_batch(self, session, bonds: List[Dict]):
        """Insert a batch of bonds."""
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

    def _import_follows(self, session, filepath: Path, batch_size: int) -> int:
        """Import FOLLOWS relationships from CSV in batches."""
        print(f"  Importing FOLLOWS from {filepath.name}...")

        total = 0
        batch = []

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                batch.append({
                    'from_id': row['from_id'],
                    'to_id': row['to_id'],
                    'source': row['source'],
                    'book_id': row['book_id']
                })

                if len(batch) >= batch_size:
                    self._insert_follows_batch(session, batch)
                    total += len(batch)
                    if total % 50000 == 0:
                        print(f"    {total:,} relationships...")
                    batch = []

        if batch:
            self._insert_follows_batch(session, batch)
            total += len(batch)

        print(f"    {total:,} FOLLOWS total")
        return total

    def _insert_follows_batch(self, session, rels: List[Dict]):
        """Insert a batch of FOLLOWS relationships."""
        session.run("""
            UNWIND $rels AS rel
            MATCH (from:Bond {id: rel.from_id})
            MATCH (to:Bond {id: rel.to_id})
            CREATE (from)-[:FOLLOWS {source: rel.source, book_id: rel.book_id}]->(to)
        """, rels=rels)

    def _create_contains(self, session) -> int:
        """Create CONTAINS relationships between Books and Bonds."""
        print("  Creating CONTAINS relationships...")

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

        print(f"    {created:,} CONTAINS")
        return created

    def verify(self, uri: str, user: str, password: str) -> Dict[str, int]:
        """Verify the imported data."""
        driver = self.connect(uri, user, password)
        if not driver:
            return {}

        stats = {}
        try:
            with driver.session() as session:
                result = session.run("MATCH (b:Book) RETURN count(b) as count")
                stats['books'] = result.single()['count']

                result = session.run("MATCH (b:Bond) RETURN count(b) as count")
                stats['bonds'] = result.single()['count']

                result = session.run("MATCH ()-[f:FOLLOWS]->() RETURN count(f) as count")
                stats['follows'] = result.single()['count']

                result = session.run("MATCH ()-[c:CONTAINS]->() RETURN count(c) as count")
                stats['contains'] = result.single()['count']
        finally:
            driver.close()

        return stats


# =============================================================================
# POSTGRESQL MIGRATOR
# =============================================================================

class PostgresMigrator:
    """Handles PostgreSQL data migration."""

    def __init__(self, export_dir: Path):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def connect(self, host: str, port: int, database: str, user: str, password: str):
        """Connect to PostgreSQL and return connection."""
        try:
            import psycopg2
        except ImportError:
            print("ERROR: psycopg2 package not installed. Run: pip install psycopg2-binary")
            return None

        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            return conn
        except Exception as e:
            print(f"ERROR: Could not connect to PostgreSQL at {host}:{port}: {e}")
            return None

    def export_all(self, host: str, port: int, database: str, user: str, password: str) -> Dict[str, int]:
        """Export all data from PostgreSQL to CSV files."""
        print("-" * 60)
        print("POSTGRESQL EXPORT")
        print("-" * 60)
        print(f"Source: {host}:{port}/{database}")

        conn = self.connect(host, port, database, user, password)
        if not conn:
            return {}

        stats = {}
        try:
            stats['hyp_bond_vocab'] = self._export_hyp_bond_vocab(conn)
            stats['word_coordinates'] = self._export_word_coordinates(conn)
            stats['learned_bonds'] = self._export_learned_bonds(conn)
        finally:
            conn.close()

        return stats

    def _export_hyp_bond_vocab(self, conn) -> int:
        """Export hyp_bond_vocab table to CSV."""
        filepath = self.export_dir / 'pg_hyp_bond_vocab.csv'
        print(f"  Exporting hyp_bond_vocab to {filepath.name}...")

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM hyp_bond_vocab")
        total = cursor.fetchone()[0]

        if total == 0:
            print("    0 records (table empty)")
            cursor.close()
            return 0

        cursor.execute("""
            SELECT bond, first_seen_order, first_seen_book, total_count, book_count, created_at
            FROM hyp_bond_vocab
            ORDER BY bond
        """)

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['bond', 'first_seen_order', 'first_seen_book', 'total_count', 'book_count', 'created_at'])

            while True:
                rows = cursor.fetchmany(10000)
                if not rows:
                    break
                for row in rows:
                    writer.writerow(row)
                    count += 1
                if count % 500000 == 0:
                    print(f"    {count:,} records...")

        cursor.close()
        print(f"    {count:,} records total")
        return count

    def _export_word_coordinates(self, conn) -> int:
        """Export word_coordinates table to CSV."""
        filepath = self.export_dir / 'pg_word_coordinates.csv'
        print(f"  Exporting word_coordinates to {filepath.name}...")

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM word_coordinates")
        total = cursor.fetchone()[0]

        if total == 0:
            print("    0 records (table empty)")
            cursor.close()
            return 0

        cursor.execute("""
            SELECT word, A, S, tau, source, created_at
            FROM word_coordinates
            ORDER BY word
        """)

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['word', 'A', 'S', 'tau', 'source', 'created_at'])

            for row in cursor:
                writer.writerow(row)
                count += 1

        cursor.close()
        print(f"    {count:,} records")
        return count

    def _export_learned_bonds(self, conn) -> int:
        """Export learned_bonds table to CSV."""
        filepath = self.export_dir / 'pg_learned_bonds.csv'
        print(f"  Exporting learned_bonds to {filepath.name}...")

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM learned_bonds")
        total = cursor.fetchone()[0]

        if total == 0:
            print("    0 records (table empty)")
            cursor.close()
            return 0

        cursor.execute("""
            SELECT id, adj, noun, A, S, tau, source, confidence, use_count, created_at
            FROM learned_bonds
            ORDER BY id
        """)

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'adj', 'noun', 'A', 'S', 'tau', 'source', 'confidence', 'use_count', 'created_at'])

            for row in cursor:
                writer.writerow(row)
                count += 1

        cursor.close()
        print(f"    {count:,} records")
        return count

    def import_all(self, host: str, port: int, database: str, user: str, password: str) -> Dict[str, int]:
        """Import all data from CSV files to PostgreSQL."""
        print("-" * 60)
        print("POSTGRESQL IMPORT")
        print("-" * 60)
        print(f"Target: {host}:{port}/{database}")

        conn = self.connect(host, port, database, user, password)
        if not conn:
            return {}

        stats = {}
        try:
            self._ensure_tables(conn)
            stats['hyp_bond_vocab'] = self._import_hyp_bond_vocab(conn)
            stats['word_coordinates'] = self._import_word_coordinates(conn)
            stats['learned_bonds'] = self._import_learned_bonds(conn)
            conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"ERROR: {e}")
            raise
        finally:
            conn.close()

        return stats

    def _ensure_tables(self, conn):
        """Create tables if they don't exist."""
        print("  Ensuring tables exist...")
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS word_coordinates (
                word VARCHAR(100) PRIMARY KEY,
                A DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                S DOUBLE PRECISION NOT NULL DEFAULT 0.0,
                tau DOUBLE PRECISION NOT NULL DEFAULT 2.5,
                source VARCHAR(50) DEFAULT 'corpus',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # hyp_bond_vocab uses bond column (adj|noun format) for compatibility with existing data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hyp_bond_vocab (
                bond VARCHAR(200) PRIMARY KEY,
                first_seen_order INTEGER,
                first_seen_book UUID,
                total_count INTEGER DEFAULT 1,
                book_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_bonds (
                id SERIAL PRIMARY KEY,
                adj VARCHAR(255),
                noun VARCHAR(255),
                A FLOAT,
                S FLOAT,
                tau FLOAT,
                source VARCHAR(50) DEFAULT 'user',
                confidence FLOAT DEFAULT 1.0,
                use_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(adj, noun)
            )
        """)

        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bond_vocab_count ON hyp_bond_vocab(total_count DESC)
        """)

        cursor.close()
        conn.commit()

    def _import_hyp_bond_vocab(self, conn) -> int:
        """Import hyp_bond_vocab from CSV or backup file."""
        # Try migration file first, then backup
        filepath = self._find_file('pg_hyp_bond_vocab.csv', '../backup/hyp_bond_vocab.csv')

        if not filepath:
            print("  Skipping hyp_bond_vocab (no file found)")
            return 0

        print(f"  Importing hyp_bond_vocab from {filepath.name}...")

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE hyp_bond_vocab")

        count = 0
        batch = []
        batch_size = 10000

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Parse UUID or set to None
                first_seen_book = row.get('first_seen_book')
                if first_seen_book and first_seen_book.strip():
                    try:
                        # Validate it's a valid UUID format
                        import uuid
                        uuid.UUID(first_seen_book)
                    except (ValueError, AttributeError):
                        first_seen_book = None
                else:
                    first_seen_book = None

                batch.append((
                    row['bond'],
                    int(row.get('first_seen_order', 0)) if row.get('first_seen_order') else None,
                    first_seen_book,
                    int(row.get('total_count', 1)) if row.get('total_count') else 1,
                    int(row.get('book_count', 1)) if row.get('book_count') else 1,
                    row.get('created_at')
                ))

                if len(batch) >= batch_size:
                    self._insert_hyp_batch(cursor, batch)
                    count += len(batch)
                    if count % 500000 == 0:
                        print(f"    {count:,} records...")
                        conn.commit()
                    batch = []

        if batch:
            self._insert_hyp_batch(cursor, batch)
            count += len(batch)

        conn.commit()
        cursor.close()
        print(f"    {count:,} records total")
        return count

    def _insert_hyp_batch(self, cursor, batch):
        """Insert batch into hyp_bond_vocab."""
        from psycopg2.extras import execute_values
        execute_values(cursor, """
            INSERT INTO hyp_bond_vocab (bond, first_seen_order, first_seen_book, total_count, book_count, created_at)
            VALUES %s
            ON CONFLICT (bond) DO UPDATE SET
                total_count = hyp_bond_vocab.total_count + EXCLUDED.total_count
        """, batch)

    def _import_word_coordinates(self, conn) -> int:
        """Import word_coordinates from CSV or JSON."""
        # Try CSV first, then JSON
        csv_path = self.export_dir / 'pg_word_coordinates.csv'
        json_path = self.export_dir.parent / 'coordinates' / 'derived_coordinates.json'

        if csv_path.exists():
            return self._import_word_coords_csv(conn, csv_path)
        elif json_path.exists():
            return self._import_word_coords_json(conn, json_path)
        else:
            print("  Skipping word_coordinates (no file found)")
            return 0

    def _import_word_coords_csv(self, conn, filepath: Path) -> int:
        """Import word coordinates from CSV."""
        print(f"  Importing word_coordinates from {filepath.name}...")

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE word_coordinates")

        count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT INTO word_coordinates (word, A, S, tau, source)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (word) DO NOTHING
                """, (
                    row['word'],
                    float(row['A']) if row.get('A') else 0.0,
                    float(row['S']) if row.get('S') else 0.0,
                    float(row['tau']) if row.get('tau') else 2.5,
                    row.get('source', 'corpus')
                ))
                count += 1

        conn.commit()
        cursor.close()
        print(f"    {count:,} records")
        return count

    def _import_word_coords_json(self, conn, filepath: Path) -> int:
        """Import word coordinates from derived_coordinates.json."""
        print(f"  Importing word_coordinates from {filepath.name}...")

        with open(filepath, 'r') as f:
            data = json.load(f)

        coords = data.get('coordinates', {})
        if not coords:
            print("    0 records (no coordinates in JSON)")
            return 0

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE word_coordinates")

        count = 0
        batch = []

        for word, values in coords.items():
            # Use 'n' as tau approximation if tau not present
            tau_val = values.get('tau') or values.get('n') or 2.5
            batch.append((
                word,
                values.get('A', 0.0),
                values.get('S', 0.0),
                tau_val,
                'derived'  # source
            ))

            if len(batch) >= 5000:
                self._insert_coords_batch(cursor, batch)
                count += len(batch)
                batch = []

        if batch:
            self._insert_coords_batch(cursor, batch)
            count += len(batch)

        conn.commit()
        cursor.close()
        print(f"    {count:,} records")
        return count

    def _insert_coords_batch(self, cursor, batch):
        """Insert batch into word_coordinates."""
        from psycopg2.extras import execute_values
        execute_values(cursor, """
            INSERT INTO word_coordinates (word, A, S, tau, source)
            VALUES %s
            ON CONFLICT (word) DO NOTHING
        """, batch)

    def _import_learned_bonds(self, conn) -> int:
        """Import learned_bonds from CSV."""
        filepath = self._find_file('pg_learned_bonds.csv', '../backup/learned_bonds.csv')

        if not filepath:
            print("  Skipping learned_bonds (no file found)")
            return 0

        print(f"  Importing learned_bonds from {filepath.name}...")

        cursor = conn.cursor()
        cursor.execute("TRUNCATE TABLE learned_bonds RESTART IDENTITY")

        count = 0
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                cursor.execute("""
                    INSERT INTO learned_bonds (adj, noun, A, S, tau, source, confidence, use_count)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (adj, noun) DO NOTHING
                """, (
                    row.get('adj', ''),
                    row.get('noun', ''),
                    float(row['A']) if row.get('A') else 0.0,
                    float(row['S']) if row.get('S') else 0.0,
                    float(row['tau']) if row.get('tau') else 2.5,
                    row.get('source', 'user'),
                    float(row.get('confidence', 1.0)),
                    int(row.get('use_count', 1))
                ))
                count += 1

        cursor.close()
        print(f"    {count:,} records")
        return count

    def _find_file(self, *names) -> Optional[Path]:
        """Find first existing file from list of names."""
        for name in names:
            if name.startswith('../'):
                filepath = self.export_dir.parent / name[3:]
            else:
                filepath = self.export_dir / name
            if filepath.exists():
                return filepath
        return None

    def verify(self, host: str, port: int, database: str, user: str, password: str) -> Dict[str, int]:
        """Verify the imported data."""
        conn = self.connect(host, port, database, user, password)
        if not conn:
            return {}

        stats = {}
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM hyp_bond_vocab")
            stats['hyp_bond_vocab'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM word_coordinates")
            stats['word_coordinates'] = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM learned_bonds")
            stats['learned_bonds'] = cursor.fetchone()[0]
        except Exception as e:
            print(f"  Warning: {e}")
        finally:
            cursor.close()
            conn.close()

        return stats


# =============================================================================
# MAIN MIGRATOR
# =============================================================================

class StormLogosMigrator:
    """Main migrator coordinating Neo4j and PostgreSQL."""

    def __init__(self, export_dir: Path = DEFAULT_EXPORT_DIR):
        self.export_dir = Path(export_dir)
        self.neo4j = Neo4jMigrator(export_dir)
        self.postgres = PostgresMigrator(export_dir)

    def export_all(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                   pg_host: str, pg_port: int, pg_db: str, pg_user: str, pg_password: str) -> Dict:
        """Export all data from both databases."""
        print("=" * 60)
        print("STORM-LOGOS DATA EXPORT")
        print("=" * 60)
        print(f"Export directory: {self.export_dir}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        stats = {'neo4j': {}, 'postgres': {}}

        stats['neo4j'] = self.neo4j.export_all(neo4j_uri, neo4j_user, neo4j_password)
        print()
        stats['postgres'] = self.postgres.export_all(pg_host, pg_port, pg_db, pg_user, pg_password)

        self._print_summary("EXPORT SUMMARY", stats)
        self._save_manifest(stats, 'export')

        return stats

    def import_all(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                   pg_host: str, pg_port: int, pg_db: str, pg_user: str, pg_password: str) -> Dict:
        """Import all data to both databases."""
        print("=" * 60)
        print("STORM-LOGOS DATA IMPORT")
        print("=" * 60)
        print(f"Import directory: {self.export_dir}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print()

        stats = {'neo4j': {}, 'postgres': {}}

        stats['neo4j'] = self.neo4j.import_all(neo4j_uri, neo4j_user, neo4j_password)
        print()
        stats['postgres'] = self.postgres.import_all(pg_host, pg_port, pg_db, pg_user, pg_password)

        self._print_summary("IMPORT SUMMARY", stats)

        return stats

    def verify_all(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str,
                   pg_host: str, pg_port: int, pg_db: str, pg_user: str, pg_password: str) -> Dict:
        """Verify data in both databases."""
        print("=" * 60)
        print("STORM-LOGOS DATA VERIFICATION")
        print("=" * 60)
        print()

        stats = {'neo4j': {}, 'postgres': {}}

        print("Neo4j:")
        stats['neo4j'] = self.neo4j.verify(neo4j_uri, neo4j_user, neo4j_password)
        for k, v in stats['neo4j'].items():
            print(f"  {k}: {v:,}")

        print()
        print("PostgreSQL:")
        stats['postgres'] = self.postgres.verify(pg_host, pg_port, pg_db, pg_user, pg_password)
        for k, v in stats['postgres'].items():
            print(f"  {k}: {v:,}")

        return stats

    def _print_summary(self, title: str, stats: Dict):
        """Print summary of operation."""
        print()
        print("=" * 60)
        print(title)
        print("=" * 60)

        print("\nNeo4j:")
        for k, v in stats.get('neo4j', {}).items():
            print(f"  {k}: {v:,}")

        print("\nPostgreSQL:")
        for k, v in stats.get('postgres', {}).items():
            print(f"  {k}: {v:,}")

        # Calculate totals
        neo4j_total = sum(stats.get('neo4j', {}).values())
        pg_total = sum(stats.get('postgres', {}).values())
        print(f"\nTotal records: {neo4j_total + pg_total:,}")

    def _save_manifest(self, stats: Dict, operation: str):
        """Save manifest file with export details."""
        manifest = {
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'stats': stats
        }
        manifest_path = self.export_dir / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        print(f"\nManifest saved to {manifest_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Storm-Logos Migration Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Common arguments
    def add_neo4j_args(p, prefix=''):
        p.add_argument(f'--neo4j-uri', default='bolt://localhost:7687')
        p.add_argument(f'--neo4j-user', default='neo4j')
        p.add_argument(f'--neo4j-password', required=True)

    def add_pg_args(p):
        p.add_argument('--pg-host', default='localhost')
        p.add_argument('--pg-port', type=int, default=5432)
        p.add_argument('--pg-db', default='semantic')
        p.add_argument('--pg-user', default='postgres')
        p.add_argument('--pg-password', required=True)

    # Export command
    export_parser = subparsers.add_parser('export', help='Export from source databases')
    add_neo4j_args(export_parser)
    add_pg_args(export_parser)
    export_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)

    # Import command
    import_parser = subparsers.add_parser('import', help='Import to target databases')
    import_parser.add_argument('--neo4j-uri', default='bolt://localhost:7687')
    import_parser.add_argument('--neo4j-user', default='neo4j')
    import_parser.add_argument('--neo4j-password', required=True)
    add_pg_args(import_parser)
    import_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify data in databases')
    verify_parser.add_argument('--neo4j-uri', default='bolt://localhost:7687')
    verify_parser.add_argument('--neo4j-user', default='neo4j')
    verify_parser.add_argument('--neo4j-password', required=True)
    add_pg_args(verify_parser)

    # Export-only (no postgres connection needed for target)
    export_only_parser = subparsers.add_parser('export-only', help='Export only (for transfer)')
    add_neo4j_args(export_only_parser)
    add_pg_args(export_only_parser)
    export_only_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)

    # Import-only (use files from export)
    import_only_parser = subparsers.add_parser('import-only', help='Import only (from files)')
    import_only_parser.add_argument('--neo4j-uri', default='bolt://localhost:7687')
    import_only_parser.add_argument('--neo4j-user', default='neo4j')
    import_only_parser.add_argument('--neo4j-password', required=True)
    add_pg_args(import_only_parser)
    import_only_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    migrator = StormLogosMigrator(getattr(args, 'export_dir', DEFAULT_EXPORT_DIR))

    if args.command in ['export', 'export-only']:
        migrator.export_all(
            args.neo4j_uri, args.neo4j_user, args.neo4j_password,
            args.pg_host, args.pg_port, args.pg_db, args.pg_user, args.pg_password
        )

    elif args.command in ['import', 'import-only']:
        migrator.import_all(
            args.neo4j_uri, args.neo4j_user, args.neo4j_password,
            args.pg_host, args.pg_port, args.pg_db, args.pg_user, args.pg_password
        )

    elif args.command == 'verify':
        migrator.verify_all(
            args.neo4j_uri, args.neo4j_user, args.neo4j_password,
            args.pg_host, args.pg_port, args.pg_db, args.pg_user, args.pg_password
        )


if __name__ == '__main__':
    main()
