#!/usr/bin/env python3
"""Apply versioned SQL atomically. Run from any directory."""
import argparse
import hashlib
import os
from pathlib import Path
import sys

import psycopg

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DSN = 'postgresql://gym_user:gym_password@localhost:5433/gym'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['up', 'seed', 'down', 'status'])
    args = parser.parse_args()
    paths = sorted((ROOT / 'migrations').glob('*.up.sql'))
    files = {p.name.removesuffix('.up.sql'): p for p in paths}
    with psycopg.connect(os.environ.get('DATABASE_URL', DEFAULT_DSN), autocommit=True, connect_timeout=10) as conn:
        # Session lock serializes concurrent runners, including ledger creation.
        conn.execute('SELECT pg_advisory_lock(250017)')
        try:
            conn.execute('''CREATE TABLE IF NOT EXISTS public.schema_migrations (
                version text PRIMARY KEY,
                checksum text NOT NULL,
                applied_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
            )''')
            rows = dict(conn.execute('SELECT version, checksum FROM public.schema_migrations').fetchall())
            for version, checksum in rows.items():
                if version not in files or hashlib.sha256(files[version].read_bytes()).hexdigest() != checksum:
                    raise ValueError(f'Applied migration is missing or changed: {version}')
            # Applied history must be a prefix of the local ordered migration list.
            if sorted(rows) != list(files)[:len(rows)]:
                raise ValueError('Migration history is out of order; restore the original migration files.')
            if args.command == 'status':
                for version in files:
                    print(f'{version}: {"applied" if version in rows else "pending"}')
                return
            if args.command == 'down':
                if not rows:
                    print('Nothing to roll back.')
                    return
                version = max(rows)
                sql = (ROOT / 'migrations' / f'{version}.down.sql').read_text()
                with conn.transaction():
                    conn.execute(sql, prepare=False)
                    conn.execute('DELETE FROM public.schema_migrations WHERE version = %s', (version,))
                print(f'Rolled back {version}')
                return
            count = 0
            for version, path in files.items():
                if version in rows or (args.command == 'up' and version == '002_seed_demo_data'):
                    continue
                content = path.read_bytes()
                with conn.transaction():
                    conn.execute(content.decode('utf-8'), prepare=False)
                    conn.execute('INSERT INTO public.schema_migrations (version, checksum) VALUES (%s, %s)',
                                 (version, hashlib.sha256(content).hexdigest()))
                print(f'Applied {version}')
                count += 1
            if not count:
                print('No pending migrations for this command.')
        finally:
            conn.execute('SELECT pg_advisory_unlock(250017)')


if __name__ == '__main__':
    try:
        main()
    except (psycopg.Error, ValueError, OSError) as exc:
        print(f'Migration failed: {exc}', file=sys.stderr)
        sys.exit(1)
