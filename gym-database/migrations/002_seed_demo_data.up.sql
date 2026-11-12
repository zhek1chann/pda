INSERT INTO members (first_name, last_name, email, phone) VALUES
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
