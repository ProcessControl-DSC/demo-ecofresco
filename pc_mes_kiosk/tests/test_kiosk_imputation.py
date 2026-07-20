# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Tests for pc_mes_kiosk — _pc_impute logic on hr.attendance."""
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase

MAIL_CTX = {"tracking_disable": True, "mail_notrack": True, "no_reset_password": True}


class TestKioskImputation(TransactionCase):
    """Verify that _pc_impute creates (or does NOT create) account.analytic.line
    records correctly when hr.attendance.check_out is set."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, **MAIL_CTX))

        # Employee with user so analytic line gets a user_id
        cls.user = cls.env["res.users"].create(
            {
                "name": "Kiosk Test User",
                "login": "kiosk_test_user_pc",
                "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Kiosk Test Employee",
                "user_id": cls.user.id,
            }
        )
        cls.project = cls.env["project.project"].create(
            {"name": "Kiosk Test Project"}
        )
        cls.task = cls.env["project.task"].create(
            {
                "name": "Kiosk Test Task",
                "project_id": cls.project.id,
            }
        )

    # ── helpers ──────────────────────────────────────────────────────────────

    def _make_open_attendance(self, check_in=None):
        """Return an open attendance record (no check_out)."""
        if check_in is None:
            check_in = fields.Datetime.now() - timedelta(hours=2)
        return self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in,
            }
        )

    # ── tests ─────────────────────────────────────────────────────────────────

    def test_impute_on_task(self):
        """Closing an attendance with a pc_task_id creates one analytic line
        with the correct project_id, task_id, employee_id and unit_amount."""
        check_in = fields.Datetime.now() - timedelta(hours=1, minutes=30)
        attendance = self._make_open_attendance(check_in=check_in)
        attendance.write({"pc_task_id": self.task.id})

        check_out = check_in + timedelta(hours=1, minutes=30)
        attendance.write({"check_out": check_out})

        self.assertTrue(
            attendance.pc_timesheet_line_id,
            "A timesheet line should have been created on check_out.",
        )
        line = attendance.pc_timesheet_line_id
        self.assertEqual(line.project_id, self.project,
                         "Analytic line project must match the task's project.")
        self.assertEqual(line.task_id, self.task,
                         "Analytic line task must match pc_task_id.")
        self.assertEqual(line.employee_id, self.employee,
                         "Analytic line employee must match the attendance employee.")
        self.assertAlmostEqual(
            line.unit_amount,
            attendance.worked_hours,
            places=4,
            msg="unit_amount must equal worked_hours.",
        )

    def test_impute_on_project_only(self):
        """When only pc_project_id is set (no task), the analytic line must
        carry the project but no task."""
        check_in = fields.Datetime.now() - timedelta(hours=1)
        attendance = self._make_open_attendance(check_in=check_in)
        attendance.write({"pc_project_id": self.project.id})

        check_out = check_in + timedelta(hours=1)
        attendance.write({"check_out": check_out})

        self.assertTrue(
            attendance.pc_timesheet_line_id,
            "A timesheet line should have been created when only project is set.",
        )
        line = attendance.pc_timesheet_line_id
        self.assertEqual(line.project_id, self.project)
        self.assertFalse(line.task_id,
                         "task_id must be empty when only project is given.")

    def test_idempotent(self):
        """A second write with check_out already set must NOT create a new
        analytic line — the idempotent guard on pc_timesheet_line_id must fire."""
        check_in = fields.Datetime.now() - timedelta(hours=1)
        attendance = self._make_open_attendance(check_in=check_in)
        attendance.write({"pc_task_id": self.task.id})

        check_out = check_in + timedelta(hours=1)
        attendance.write({"check_out": check_out})

        first_line = attendance.pc_timesheet_line_id
        self.assertTrue(first_line, "First close must produce an analytic line.")

        # Simulate a second write touching check_out (e.g. correcting the time)
        attendance.write({"check_out": check_out + timedelta(minutes=5)})

        self.assertEqual(
            attendance.pc_timesheet_line_id,
            first_line,
            "A second write on check_out must not create a second analytic line.",
        )
        line_count = self.env["account.analytic.line"].search_count(
            [("employee_id", "=", self.employee.id),
             ("task_id", "=", self.task.id)]
        )
        self.assertEqual(line_count, 1,
                         "Exactly one analytic line must exist after two check_out writes.")

    def test_no_target_no_line(self):
        """Attendance without pc_project_id nor pc_task_id must not produce
        any analytic line, even after check_out is set."""
        check_in = fields.Datetime.now() - timedelta(hours=1)
        attendance = self._make_open_attendance(check_in=check_in)
        # Intentionally leave pc_project_id and pc_task_id empty

        check_out = check_in + timedelta(hours=1)
        attendance.write({"check_out": check_out})

        self.assertFalse(
            attendance.pc_timesheet_line_id,
            "No analytic line must be created when neither project nor task is set.",
        )
