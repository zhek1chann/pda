-- Remove only the reserved demo entities. RESTRICT prevents accidental deletion
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
