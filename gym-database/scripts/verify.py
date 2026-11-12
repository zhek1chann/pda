"""Integration checks: all inserted data is rolled back."""
import os
import psycopg
from migrate import DEFAULT_DSN

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
