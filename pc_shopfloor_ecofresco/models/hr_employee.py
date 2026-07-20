# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    # -------------------------------------------------------------------
    # Functional decision (assumed for this demo, must be validated with
    # the client before going to production):
    #
    #   "Shop Floor login = clock-in / Shop Floor logout = clock-out"
    #
    # `mrp_workorder.hr.employee.login()` / `.logout()` are the methods
    # called by the Shop Floor operator panel (mrp_display) when an
    # operator identifies with their PIN, or disconnects. We piggy-back on
    # them to also open/close the matching `hr.attendance` record, so the
    # operator does not have to clock in/out a second time on the
    # standalone Attendance kiosk.
    #
    # IMPORTANT — no blind toggling:
    # `login()` is called by the Shop Floor JS client not only the first
    # time an operator connects, but also every time an already-connected
    # operator is promoted to "session owner" (the operator allowed to
    # start/stop workorders), and on every page load while trying to
    # restore the previous session owner. We must NOT use
    # `hr.employee.attendance_manual()` (it blindly flips check-in/
    # check-out) — instead we always look up whether the employee already
    # has an open attendance (`check_out` not set) before deciding to
    # create or close one. This makes both overrides idempotent: calling
    # `login()` on an already clocked-in operator is a no-op for
    # attendance, and calling `logout()` on an operator with no open
    # attendance is also a no-op.
    # -------------------------------------------------------------------

    def login(self, pin=False, set_in_session=True):
        result = super().login(pin=pin, set_in_session=set_in_session)
        if result:
            self._pc_shopfloor_clock_in()
        return result

    def logout(self, pin=False, unchecked=False):
        result = super().logout(pin=pin, unchecked=unchecked)
        if result:
            self._pc_shopfloor_clock_out()
        return result

    def _pc_shopfloor_clock_in(self):
        """Open a new hr.attendance for the employee if it does not already
        have one open. Called after a successful Shop Floor ``login()``.

        Never toggles blindly: only creates a check-in when there is no
        open attendance (``check_out`` not set) for this employee, so
        repeated ``login()`` calls (session-owner switch, page reload) or
        an operator already clocked in through another channel (the
        public Attendance kiosk, the Attendances app...) never create a
        duplicate attendance record.
        """
        self.ensure_one()
        open_attendance = self.env["hr.attendance"].sudo().search(
            [("employee_id", "=", self.id), ("check_out", "=", False)],
            limit=1,
        )
        if open_attendance:
            return open_attendance
        return self.env["hr.attendance"].sudo().create({
            "employee_id": self.id,
            "check_in": fields.Datetime.now(),
        })

    def _pc_shopfloor_clock_out(self):
        """Close the employee's open hr.attendance, if any. Called after a
        successful Shop Floor ``logout()``.

        Only closes an attendance that is actually open; if the employee
        has none (already clocked out, or was never clocked in through
        this module) it is a no-op.
        """
        self.ensure_one()
        open_attendance = self.env["hr.attendance"].sudo().search(
            [("employee_id", "=", self.id), ("check_out", "=", False)],
            limit=1,
        )
        if not open_attendance:
            return self.env["hr.attendance"]
        open_attendance.write({"check_out": fields.Datetime.now()})
        return open_attendance

    # -------------------------------------------------------------------
    # Shop Floor "Tareas indirectas" (indirect project tasks: cleaning,
    # warehouse...) — resolve who the current operator is server-side.
    # -------------------------------------------------------------------

    def _pc_shopfloor_get_connected_employee(self):
        """Return the ``hr.employee`` currently connected as the Shop Floor
        session owner (the operator "at the wheel" of the panel), or an
        empty recordset if nobody is connected.

        ``hr.employee.get_session_owner()`` (defined in ``mrp_workorder``)
        reads ``request.session[SESSION_OWNER]`` and normally returns a
        single employee id (int), or ``False``/``[]`` when nobody is
        connected. Outside of an HTTP request (e.g. in tests) it falls back
        to ``[self.env.user.employee_id.id]`` — a list. We defensively
        unwrap both shapes here instead of trusting a client-supplied
        employee id, so a Shop Floor write (like an indirect timesheet)
        always gets credited to the actual connected operator.
        """
        owner = self.sudo().get_session_owner()
        if isinstance(owner, (list, tuple)):
            owner = owner[0] if owner else False
        if not owner:
            return self.browse()
        return self.browse(owner).exists()
