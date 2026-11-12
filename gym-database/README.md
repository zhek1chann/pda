# Gym database — variant 25

PostgreSQL 17, seven domain tables, plain SQL migrations, Python 3.12 + Psycopg runner, Docker Compose, editable draw.io ERD.

## Start

Install/start Docker Desktop (or Docker Engine with Compose) and run:

```sh
cd /Users/ZSTalipov/Desktop/aitu/pda/gym-database
make up
make seed       # optional sample records
make verify     # constraint checks; test records are rolled back
make status
```

`make up` waits for a healthy PostgreSQL server, builds the Python image, and applies schema migration 001. `make seed` additionally applies migration 002 once. The runner records migration checksums in `schema_migrations` (an infrastructure table, separate from the seven domain tables). It refuses altered applied migrations, serializes concurrent runners with an advisory lock, and commits each migration and its ledger entry together. A failure rolls back that migration. SQL files intentionally omit BEGIN/COMMIT because Python owns transactions.

Docker creates the database on the first start of the empty named volume. Data survives `make down` and subsequent `make up`. Default credentials are for this local coursework setup. The published port binds only to the local machine.

## DataGrip connection

Add Data Source → PostgreSQL, download the driver if prompted, enter these values, and select Test Connection:

| Field | Value |
|---|---|
| Host | `localhost` |
| Port | `5433` |
| Database | `gym` |
| User | `gym_user` |
| Password | `gym_password` |
| Schema | `public` |
| SSL | Disabled for this local container |

DSN (connection string): `postgresql://gym_user:gym_password@localhost:5433/gym`

JDBC URL: `jdbc:postgresql://localhost:5433/gym` (enter credentials separately).

Inside Compose the hostname is `db`, port `5432`; DataGrip on your computer uses `localhost:5433`. No external DNS record is needed. If port 5433 is occupied, run `POSTGRES_PORT=5543 make up` and use 5543 in DataGrip and the host DSN. Set the same environment variable for subsequent make commands. Refresh/introspect the public schema after migration. For Almaty timestamps, execute `SET TIME ZONE 'Asia/Almaty';` in your SQL console.

## Run Python directly (optional)

Python 3.10+ is required. Docker-based execution does not require host Python packages.

```sh
make db
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/migrate.py up
.venv/bin/python scripts/migrate.py seed
.venv/bin/python scripts/verify.py
```

Override the default local DSN with the `DATABASE_URL` environment variable if needed.

## Commands and rollback

- `make up`: start database and apply schema.
- `make seed`: apply schema and demo data.
- `make status`: show migration state.
- `make verify`: run integration checks.
- `make psql`: open a SQL console.
- `make logs`: follow server logs.
- `make down`: stop/remove containers while keeping the named volume.
- `make rollback`: undo **one** latest migration. This deletes its data. If seed 002 is applied, the first call removes demo data; a second call drops the seven domain tables. Do not use on data you need. Seed rollback uses reserved demo emails/names; do not reuse these identifiers for real records.

To add schema changes, create the next numbered `.up.sql` and matching `.down.sql`; do not edit already-applied migrations. Demo seed is deliberately optional. If adding later migrations, apply the seed before them if you want it: the ledger requires an ordered prefix.

## Diagram

Open `diagram/gym_erd.drawio` with draw.io / diagrams.net using File → Open From → Device. All tables, columns, types, PK/FK markers, nullability and crow's foot relationships are editable. The diagram omits the migration ledger because it is deployment infrastructure.

## Relationships

- Members → member_profiles: 1 to 0..1 (optional 1:1), enforced by shared PK/FK. Every profile has exactly one member; a member need not have a profile.
- Members → memberships: 1 to 0..many.
- Membership_plans → memberships: 1 to 0..many.
- Trainers → gym_classes: 1 to 0..many.
- Members ↔ gym_classes: many-to-many through class_bookings; each booking references exactly one of each. Composite PK prevents duplicate bookings. Rebooking updates the existing row.

## Normalization and assignment checklist

1NF: each of the seven tables has an explicit PK, atomic column values, and no repeating groups. Names are separated into first/last name; class participation is stored in individual booking rows.

2NF: single-column keys have no partial-key dependency. The junction's `booked_at` and `booking_status` describe the complete member/class pair, not just one half of the composite key.

3NF: member, trainer, and plan details reside only in their respective tables. Memberships and classes refer to them by FK. Historical `paid_amount_kzt` is the actual payment, not a copy of the current plan price. Membership end dates are agreed at purchase and can include extensions; they are not calculated from the current plan duration. Each class is an individual session with its own name, schedule, trainer and capacity.

Constraints include identity PKs; explicit FKs; NOT NULL; UNIQUE emails and plan names; positive duration, price and capacity checks; nonnegative payments; valid date/time intervals; allowed booking statuses; timestamp/boolean/status defaults. All identifiers use snake_case. SQL COMMENT metadata documents KZT, calendar days, participants and timestamps. Prices use exact numeric values. Email uniqueness is case-sensitive in this coursework schema.

Limits of this assignment model: capacity is recorded but aggregate booking limits, trainer schedule overlaps and active-membership eligibility are not enforced. These need additional transactional logic if added as business requirements. This schema allows a booking without a membership (for example a trial session).

Implementation references: [Docker Compose health dependencies](https://docs.docker.com/compose/how-tos/startup-order/), [Psycopg transaction management](https://www.psycopg.org/psycopg3/docs/basic/transactions.html).
