#!/usr/bin/env python3
"""Self-contained gym migration. Run: python migration-up.py [up|seed|status|down|verify].

Install psycopg[binary] first. DATABASE_URL overrides localhost:5433/gym.
The default command is up. Down undoes the latest migration and deletes its data.
"""
import argparse
import hashlib
import os
import sys

import psycopg

DEFAULT_DSN = 'postgresql://gym_user:gym_password@localhost:5433/gym'


SQL_001_CREATE_GYM_SCHEMA_DOWN_SQL = """DROP TABLE class_bookings;
DROP TABLE gym_classes;
DROP TABLE trainers;
DROP TABLE memberships;
DROP TABLE membership_plans;
DROP TABLE member_profiles;
DROP TABLE members;
"""

SQL_001_CREATE_GYM_SCHEMA_UP_SQL = """-- Transactions are managed by scripts/migrate.py.
CREATE TABLE members (
    member_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name varchar(100) NOT NULL CHECK (btrim(first_name) <> ''),
    last_name varchar(100) NOT NULL CHECK (btrim(last_name) <> ''),
    email varchar(254) NOT NULL UNIQUE CHECK (btrim(email) <> ''),
    phone varchar(30),
    created_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE member_profiles (
    member_id bigint PRIMARY KEY REFERENCES members(member_id) ON DELETE CASCADE,
    emergency_contact_name varchar(200) NOT NULL CHECK (btrim(emergency_contact_name) <> ''),
    emergency_contact_phone varchar(30) NOT NULL CHECK (btrim(emergency_contact_phone) <> '')
);
CREATE TABLE membership_plans (
    membership_plan_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    plan_name varchar(100) NOT NULL UNIQUE CHECK (btrim(plan_name) <> ''),
    duration_days integer NOT NULL CHECK (duration_days > 0),
    price_kzt numeric(12,2) NOT NULL CHECK (price_kzt > 0),
    is_active boolean NOT NULL DEFAULT true
);
CREATE TABLE memberships (
    membership_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    member_id bigint NOT NULL REFERENCES members(member_id) ON DELETE RESTRICT,
    membership_plan_id bigint NOT NULL REFERENCES membership_plans(membership_plan_id) ON DELETE RESTRICT,
    starts_on date NOT NULL,
    ends_on date NOT NULL,
    paid_amount_kzt numeric(12,2) NOT NULL CHECK (paid_amount_kzt >= 0),
    CHECK (ends_on > starts_on)
);
CREATE TABLE trainers (
    trainer_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    first_name varchar(100) NOT NULL CHECK (btrim(first_name) <> ''),
    last_name varchar(100) NOT NULL CHECK (btrim(last_name) <> ''),
    email varchar(254) NOT NULL UNIQUE CHECK (btrim(email) <> '')
);
CREATE TABLE gym_classes (
    gym_class_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trainer_id bigint NOT NULL REFERENCES trainers(trainer_id) ON DELETE RESTRICT,
    class_name varchar(100) NOT NULL CHECK (btrim(class_name) <> ''),
    starts_at timestamptz NOT NULL,
    ends_at timestamptz NOT NULL,
    capacity integer NOT NULL CHECK (capacity > 0),
    CHECK (ends_at > starts_at)
);
CREATE TABLE class_bookings (
    member_id bigint NOT NULL REFERENCES members(member_id) ON DELETE RESTRICT,
    gym_class_id bigint NOT NULL REFERENCES gym_classes(gym_class_id) ON DELETE RESTRICT,
    booked_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    booking_status varchar(20) NOT NULL DEFAULT 'booked'
        CHECK (booking_status IN ('booked', 'cancelled', 'attended')),
    PRIMARY KEY (member_id, gym_class_id)
);
CREATE INDEX memberships_member_idx ON memberships(member_id);
CREATE INDEX memberships_plan_idx ON memberships(membership_plan_id);
CREATE INDEX gym_classes_trainer_idx ON gym_classes(trainer_id);
CREATE INDEX class_bookings_class_idx ON class_bookings(gym_class_id);
COMMENT ON TABLE member_profiles IS 'Optional profile: each member has zero or one profile; each profile belongs to exactly one member.';
COMMENT ON TABLE class_bookings IS 'Junction for the members/classes many-to-many relationship. Rebooking updates the existing row.';
COMMENT ON COLUMN membership_plans.duration_days IS 'Advertised plan duration, measured in calendar days.';
COMMENT ON COLUMN membership_plans.price_kzt IS 'Current advertised price in Kazakhstani tenge (KZT).';
COMMENT ON COLUMN memberships.paid_amount_kzt IS 'Actual amount paid in KZT; a historical transaction fact, independent of current plan price.';
COMMENT ON COLUMN memberships.starts_on IS 'First included calendar date of the purchased membership.';
COMMENT ON COLUMN memberships.ends_on IS 'Exclusive end date agreed at purchase; may include an extension independent of current plan duration.';
COMMENT ON COLUMN gym_classes.capacity IS 'Maximum intended number of participants, measured in persons. Booking count enforcement is outside this schema.';
COMMENT ON COLUMN gym_classes.starts_at IS 'Session start instant with time zone; display in Asia/Almaty for local time.';
COMMENT ON COLUMN gym_classes.ends_at IS 'Session end instant with time zone.';
COMMENT ON COLUMN members.created_at IS 'Record creation instant with time zone.';
COMMENT ON COLUMN class_bookings.booked_at IS 'Booking creation instant with time zone.';
"""

SQL_002_SEED_DEMO_DATA_DOWN_SQL = """-- Remove only the reserved demo entities. RESTRICT prevents accidental deletion
-- if additional non-demo rows now reference them; the runner rolls back on error.
DELETE FROM class_bookings WHERE member_id IN
(SELECT member_id FROM members WHERE email IN ('aida@example.test', 'daniyar@example.test'))
AND gym_class_id IN (SELECT c.gym_class_id FROM gym_classes c JOIN trainers t USING (trainer_id)
WHERE t.email = 'askar@example.test' AND c.starts_at = '2026-11-20 09:00:00+05');
DELETE FROM gym_classes WHERE trainer_id IN (SELECT trainer_id FROM trainers WHERE email = 'askar@example.test')
AND starts_at = '2026-11-20 09:00:00+05';
DELETE FROM trainers WHERE email = 'askar@example.test';
DELETE FROM memberships WHERE member_id IN (SELECT member_id FROM members WHERE email = 'aida@example.test')
AND membership_plan_id IN (SELECT membership_plan_id FROM membership_plans WHERE plan_name = 'Monthly')
AND starts_on = '2026-11-01' AND ends_on = '2026-12-01' AND paid_amount_kzt = 18000;
DELETE FROM membership_plans WHERE plan_name IN ('Monthly', 'Quarterly');
DELETE FROM members WHERE email IN ('aida@example.test', 'daniyar@example.test');
"""

SQL_002_SEED_DEMO_DATA_UP_SQL = """INSERT INTO members (first_name, last_name, email, phone) VALUES
('Aida', 'Karimova', 'aida@example.test', '+77010000001'),
('Daniyar', 'Omarov', 'daniyar@example.test', '+77010000002');
INSERT INTO member_profiles SELECT member_id, 'Aliya Karimova', '+77010000003'
FROM members WHERE email = 'aida@example.test';
INSERT INTO membership_plans (plan_name, duration_days, price_kzt) VALUES
('Monthly', 30, 20000.00), ('Quarterly', 90, 54000.00);
INSERT INTO memberships (member_id, membership_plan_id, starts_on, ends_on, paid_amount_kzt)
SELECT m.member_id, p.membership_plan_id, DATE '2026-11-01', DATE '2026-12-01', 18000.00
FROM members m CROSS JOIN membership_plans p
WHERE m.email = 'aida@example.test' AND p.plan_name = 'Monthly';
INSERT INTO trainers (first_name, last_name, email) VALUES ('Askar', 'Sadykov', 'askar@example.test');
INSERT INTO gym_classes (trainer_id, class_name, starts_at, ends_at, capacity)
SELECT trainer_id, 'Morning Strength', '2026-11-20 09:00:00+05', '2026-11-20 10:00:00+05', 12
FROM trainers WHERE email = 'askar@example.test';
INSERT INTO class_bookings (member_id, gym_class_id)
SELECT m.member_id, c.gym_class_id FROM members m CROSS JOIN gym_classes c
JOIN trainers t ON t.trainer_id = c.trainer_id
WHERE m.email IN ('aida@example.test', 'daniyar@example.test')
AND t.email = 'askar@example.test' AND c.starts_at = '2026-11-20 09:00:00+05';
"""

MIGRATIONS = {
    '001_create_gym_schema': (SQL_001_CREATE_GYM_SCHEMA_UP_SQL, SQL_001_CREATE_GYM_SCHEMA_DOWN_SQL),
    '002_seed_demo_data': (SQL_002_SEED_DEMO_DATA_UP_SQL, SQL_002_SEED_DEMO_DATA_DOWN_SQL),
}


def verify():
    """Check constraints and roll back all test records."""
    with psycopg.connect(os.environ.get('DATABASE_URL', DEFAULT_DSN)) as conn:
        def rejected(sql, error):
            try:
                with conn.transaction():
                    conn.execute(sql)
            except error:
                return
            raise AssertionError(f'Expected {error.__name__}: {sql}')
    
        conn.execute("INSERT INTO members (first_name,last_name,email) VALUES ('Test','Member','verify@example.test')")
        conn.execute("INSERT INTO member_profiles SELECT member_id,'Contact','123' FROM members WHERE email='verify@example.test'")
        rejected("INSERT INTO member_profiles SELECT member_id,'Other','456' FROM members WHERE email='verify@example.test'", psycopg.errors.UniqueViolation)
        rejected("INSERT INTO members (first_name,last_name,email) VALUES ('Test','Member','verify@example.test')", psycopg.errors.UniqueViolation)
        rejected("INSERT INTO members (last_name,email) VALUES ('Member','null@example.test')", psycopg.errors.NotNullViolation)
        rejected("INSERT INTO membership_plans (plan_name,duration_days,price_kzt) VALUES ('Invalid',0,-1)", psycopg.errors.CheckViolation)
        rejected("INSERT INTO member_profiles VALUES (-1,'Nobody','123')", psycopg.errors.ForeignKeyViolation)
        conn.execute("INSERT INTO trainers (first_name,last_name,email) VALUES ('Test','Trainer','verify@example.test')")
        conn.execute("""INSERT INTO gym_classes (trainer_id,class_name,starts_at,ends_at,capacity)
            SELECT trainer_id,'Verify','2026-12-01 09:00+05','2026-12-01 10:00+05',5 FROM trainers WHERE email='verify@example.test'""")
        booking = """INSERT INTO class_bookings (member_id,gym_class_id)
            SELECT m.member_id,c.gym_class_id FROM members m CROSS JOIN gym_classes c
            JOIN trainers t USING (trainer_id) WHERE m.email='verify@example.test' AND t.email='verify@example.test'"""
        conn.execute(booking)
        rejected(booking, psycopg.errors.UniqueViolation)
        rejected("UPDATE gym_classes SET ends_at=starts_at", psycopg.errors.CheckViolation)
        rejected("UPDATE class_bookings SET booking_status='unknown'", psycopg.errors.CheckViolation)
        rejected("DELETE FROM members WHERE email='verify@example.test'", psycopg.errors.ForeignKeyViolation)
        assert conn.execute("SELECT booking_status, booked_at IS NOT NULL FROM class_bookings WHERE member_id=(SELECT member_id FROM members WHERE email='verify@example.test')").fetchone() == ('booked', True)
        conn.rollback()
    print('PASS: 1:1, junction uniqueness, FK, NOT NULL, UNIQUE, CHECK, DEFAULT and delete protection; test data rolled back.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', nargs='?', default='up', choices=['up', 'seed', 'down', 'status', 'verify'])
    args = parser.parse_args()
    if args.command == 'verify':
        verify()
        return
    files = MIGRATIONS
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
                if version not in files or hashlib.sha256(files[version][0].encode('utf-8')).hexdigest() != checksum:
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
                sql = files[version][1]
                with conn.transaction():
                    conn.execute(sql, prepare=False)
                    conn.execute('DELETE FROM public.schema_migrations WHERE version = %s', (version,))
                print(f'Rolled back {version}')
                return
            count = 0
            for version, (up_sql, down_sql) in files.items():
                if version in rows or (args.command == 'up' and version == '002_seed_demo_data'):
                    continue
                content = up_sql.encode('utf-8')
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
    except (psycopg.Error, ValueError, OSError, AssertionError) as exc:
        print(f'Migration failed: {exc}', file=sys.stderr)
        sys.exit(1)
