# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHrEmployeeShopfloorAttendance(TransactionCase):
    """Unit tests for the attendance helpers plugged into Shop Floor
    login()/logout().

    ``hr.employee.login()``/``logout()`` (defined in ``mrp_workorder``) read
    and write ``request.session``, which only exists inside an HTTP request
    (covered by the native Shop Floor tour tests, e.g.
    ``mrp_workorder/tests/test_shopfloor.py``). Here we test the module's
    own contribution directly: the idempotent clock-in/clock-out helpers,
    independent of the HTTP session machinery.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({
            "name": "Test Shop Floor Operator",
        })

    def _open_attendances(self):
        return self.env["hr.attendance"].search([
            ("employee_id", "=", self.employee.id),
            ("check_out", "=", False),
        ])

    def test_clock_in_creates_open_attendance(self):
        self.assertFalse(self._open_attendances())
        attendance = self.employee._pc_shopfloor_clock_in()
        self.assertTrue(attendance)
        self.assertFalse(attendance.check_out)
        self.assertEqual(self._open_attendances(), attendance)

    def test_clock_in_is_idempotent(self):
        """Calling it twice (e.g. session-owner switch, page reload) must
        not create a second open attendance."""
        first = self.employee._pc_shopfloor_clock_in()
        second = self.employee._pc_shopfloor_clock_in()
        self.assertEqual(first, second)
        self.assertEqual(len(self._open_attendances()), 1)

    def test_clock_out_closes_open_attendance(self):
        attendance = self.employee._pc_shopfloor_clock_in()
        closed = self.employee._pc_shopfloor_clock_out()
        self.assertEqual(closed, attendance)
        self.assertTrue(closed.check_out)
        self.assertFalse(self._open_attendances())

    def test_clock_out_without_open_attendance_is_noop(self):
        """Calling logout() twice, or logging out an operator with no open
        attendance, must not raise nor touch anything."""
        self.assertFalse(self._open_attendances())
        result = self.employee._pc_shopfloor_clock_out()
        self.assertFalse(result)
        self.assertFalse(self._open_attendances())

    def test_clock_in_does_not_duplicate_existing_external_attendance(self):
        """If the employee is already clocked in through another channel
        (public Attendance kiosk, Attendances app...), Shop Floor login
        must not create a second attendance record."""
        existing = self.env["hr.attendance"].create({
            "employee_id": self.employee.id,
        })
        result = self.employee._pc_shopfloor_clock_in()
        self.assertEqual(result, existing)
        self.assertEqual(len(self._open_attendances()), 1)
