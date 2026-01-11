#!/usr/bin/env python3
"""
Neo4j Migration Script for Storm-Logos

Exports data from source Neo4j and imports to target Neo4j.
Creates clean, portable CSV files for cloud migration.

Usage:
    # Export from source
    python neo4j_migrate.py export --source-uri bolt://localhost:7687 --source-password experience123

    # Import to target
    python neo4j_migrate.py import --target-uri bolt://localhost:7689 --target-password localdevpassword

    # Full migration (export + import)
    python neo4j_migrate.py migrate --source-uri bolt://localhost:7687 --source-password experience123 \
                                    --target-uri bolt://localhost:7689 --target-password localdevpassword
"""

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from neo4j import GraphDatabase
except ImportError:
    print("ERROR: neo4j package not installed. Run: pip install neo4j")
    sys.exit(1)


# Default paths
DEFAULT_EXPORT_DIR = Path(__file__).parent.parent.parent / 'data' / 'migration'


class Neo4jMigrator:
    """Handles Neo4j data migration."""

    def __init__(self, export_dir: Path = DEFAULT_EXPORT_DIR):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)

    def connect(self, uri: str, user: str, password: str) -> Optional[GraphDatabase.driver]:
        """Connect to Neo4j and return driver."""
        try:
            driver = GraphDatabase.driver(uri, auth=(user, password))
            with driver.session() as session:
                session.run("RETURN 1")
            return driver
        except Exception as e:
            print(f"ERROR: Could not connect to {uri}: {e}")
            return None

    # =========================================================================
    # EXPORT
    # =========================================================================

    def export_all(self, uri: str, user: str, password: str) -> Dict[str, int]:
        """Export all data from Neo4j to CSV files."""
        print("=" * 60)
        print("EXPORTING DATA")
        print("=" * 60)
        print(f"Source: {uri}")
        print(f"Export dir: {self.export_dir}")
        print()

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

        print()
        print("Export complete:")
        for key, count in stats.items():
            print(f"  {key}: {count:,}")

        return stats

    def _export_books(self, session) -> int:
        """Export Book nodes to CSV."""
        filepath = self.export_dir / 'books.csv'
        print(f"Exporting books to {filepath}...")

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

        print(f"  Exported {count} books")
        return count

    def _export_bonds(self, session) -> int:
        """Export Bond nodes to CSV in batches."""
        filepath = self.export_dir / 'bonds.csv'
        print(f"Exporting bonds to {filepath}...")

        count = 0
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
            writer.writerow(['id', 'adj', 'noun', 'A', 'S', 'tau', 'source'])

            # Export in batches to handle large datasets
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
                    print(f"  Exported {count:,} bonds...")

        print(f"  Exported {count:,} bonds total")
        return count

    def _export_follows(self, session) -> int:
        """Export FOLLOWS relationships to CSV in batches."""
        filepath = self.export_dir / 'follows.csv'
        print(f"Exporting FOLLOWS relationships to {filepath}...")

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
                    print(f"  Exported {count:,} relationships...")

        print(f"  Exported {count:,} FOLLOWS relationships total")
        return count

    # =========================================================================
    # IMPORT
    # =========================================================================

    def import_all(self, uri: str, user: str, password: str, batch_size: int = 5000) -> Dict[str, int]:
        """Import all data from CSV files to Neo4j."""
        print("=" * 60)
        print("IMPORTING DATA")
        print("=" * 60)
        print(f"Target: {uri}")
        print(f"Import dir: {self.export_dir}")
        print()

        # Verify files exist
        required_files = ['books.csv', 'bonds.csv', 'follows.csv']
        for filename in required_files:
            filepath = self.export_dir / filename
            if not filepath.exists():
                print(f"ERROR: Required file not found: {filepath}")
                return {}

        driver = self.connect(uri, user, password)
        if not driver:
            return {}

        stats = {}
        try:
            with driver.session() as session:
                self._clear_data(session)
                self._create_indexes(session)
                stats['books'] = self._import_books(session)
                stats['bonds'] = self._import_bonds(session, batch_size)
                stats['follows'] = self._import_follows(session, batch_size)
                stats['contains'] = self._create_contains(session)
        finally:
            driver.close()

        print()
        print("Import complete:")
        for key, count in stats.items():
            print(f"  {key}: {count:,}")

        return stats

    def _clear_data(self, session):
        """Clear existing corpus data."""
        print("Clearing existing data...")
        session.run("MATCH ()-[r:CONTAINS]->() DELETE r")
        session.run("MATCH ()-[r:FOLLOWS]->() DELETE r")
        session.run("MATCH (b:Bond) DELETE b")
        session.run("MATCH (b:Book) DELETE b")
        print("  Done")

    def _create_indexes(self, session):
        """Create indexes for faster import."""
        print("Creating indexes...")
        session.run("CREATE INDEX bond_id_idx IF NOT EXISTS FOR (b:Bond) ON (b.id)")
        session.run("CREATE INDEX book_id_idx IF NOT EXISTS FOR (b:Book) ON (b.id)")
        print("  Done")

    def _import_books(self, session) -> int:
        """Import books from CSV."""
        filepath = self.export_dir / 'books.csv'
        print(f"Importing books from {filepath}...")

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

        print(f"  Imported {len(books)} books")
        return len(books)

    def _import_bonds(self, session, batch_size: int) -> int:
        """Import bonds from CSV in batches."""
        filepath = self.export_dir / 'bonds.csv'
        print(f"Importing bonds from {filepath}...")

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
                        print(f"  Imported {total:,} bonds...")
                    batch = []

        if batch:
            self._insert_bonds_batch(session, batch)
            total += len(batch)

        print(f"  Imported {total:,} bonds total")
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

    def _import_follows(self, session, batch_size: int) -> int:
        """Import FOLLOWS relationships from CSV in batches."""
        filepath = self.export_dir / 'follows.csv'
        print(f"Importing FOLLOWS relationships from {filepath}...")

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
                        print(f"  Imported {total:,} relationships...")
                    batch = []

        if batch:
            self._insert_follows_batch(session, batch)
            total += len(batch)

        print(f"  Imported {total:,} FOLLOWS relationships total")
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
        print("Creating Book-Bond CONTAINS relationships...")

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

        print(f"  Created {created:,} CONTAINS relationships")
        return created

    # =========================================================================
    # VERIFY
    # =========================================================================

    def verify(self, uri: str, user: str, password: str) -> Dict[str, int]:
        """Verify the imported data."""
        print("=" * 60)
        print("VERIFICATION")
        print("=" * 60)

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

                print(f"Books: {stats['books']}")
                print(f"Bonds: {stats['bonds']:,}")
                print(f"FOLLOWS: {stats['follows']:,}")
                print(f"CONTAINS: {stats['contains']:,}")

                # Sample books
                print("\nTop 5 books by bond count:")
                result = session.run("""
                    MATCH (b:Book)
                    OPTIONAL MATCH (b)-[:CONTAINS]->(bond:Bond)
                    RETURN b.title AS title, b.author AS author, count(bond) AS n_bonds
                    ORDER BY n_bonds DESC
                    LIMIT 5
                """)
                for r in result:
                    print(f"  - {r['title']} ({r['author']}): {r['n_bonds']:,} bonds")

        finally:
            driver.close()

        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Neo4j Migration for Storm-Logos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export data from Neo4j')
    export_parser.add_argument('--source-uri', default='bolt://localhost:7687')
    export_parser.add_argument('--source-user', default='neo4j')
    export_parser.add_argument('--source-password', required=True)
    export_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)

    # Import command
    import_parser = subparsers.add_parser('import', help='Import data to Neo4j')
    import_parser.add_argument('--target-uri', default='bolt://localhost:7689')
    import_parser.add_argument('--target-user', default='neo4j')
    import_parser.add_argument('--target-password', required=True)
    import_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)
    import_parser.add_argument('--batch-size', type=int, default=5000)

    # Migrate command (export + import)
    migrate_parser = subparsers.add_parser('migrate', help='Full migration (export + import)')
    migrate_parser.add_argument('--source-uri', default='bolt://localhost:7687')
    migrate_parser.add_argument('--source-user', default='neo4j')
    migrate_parser.add_argument('--source-password', required=True)
    migrate_parser.add_argument('--target-uri', default='bolt://localhost:7689')
    migrate_parser.add_argument('--target-user', default='neo4j')
    migrate_parser.add_argument('--target-password', required=True)
    migrate_parser.add_argument('--export-dir', type=Path, default=DEFAULT_EXPORT_DIR)
    migrate_parser.add_argument('--batch-size', type=int, default=5000)

    # Verify command
    verify_parser = subparsers.add_parser('verify', help='Verify data in Neo4j')
    verify_parser.add_argument('--uri', default='bolt://localhost:7689')
    verify_parser.add_argument('--user', default='neo4j')
    verify_parser.add_argument('--password', required=True)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    migrator = Neo4jMigrator(getattr(args, 'export_dir', DEFAULT_EXPORT_DIR))

    if args.command == 'export':
        migrator.export_all(args.source_uri, args.source_user, args.source_password)

    elif args.command == 'import':
        migrator.import_all(args.target_uri, args.target_user, args.target_password, args.batch_size)

    elif args.command == 'migrate':
        print("Starting full migration...\n")
        export_stats = migrator.export_all(args.source_uri, args.source_user, args.source_password)
        if export_stats:
            print()
            import_stats = migrator.import_all(args.target_uri, args.target_user, args.target_password, args.batch_size)
            if import_stats:
                print()
                migrator.verify(args.target_uri, args.target_user, args.target_password)

    elif args.command == 'verify':
        migrator.verify(args.uri, args.user, args.password)


if __name__ == '__main__':
    main()
