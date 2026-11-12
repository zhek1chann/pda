-- Transactions are managed by scripts/migrate.py.
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
