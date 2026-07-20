# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

from odoo.addons.hr_attendance.controllers.main import HrAttendance

from odoo import fields, http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PcMesKioskController(HrAttendance):
    """Extends the native attendance kiosk controller with two JSON endpoints:

    - /pc_mes_kiosk/targets — returns available projects/tasks for the
      imputation picker, filtered by the module configuration flags, plus the
      chronometer state of the employee's current/last attendance.
    - /pc_mes_kiosk/set_target — writes the chosen project/task onto the
      currently open attendance record for a given employee.
    """

    def _pc_attendance_chrono(self, employee_id):
        """Return the chronometer state for an employee's attendance.

        - If the employee has an open attendance (no check_out yet), the
          elapsed time is computed live from check_in to now: the kiosk work
          screen ticks this up client-side (HH:MM:SS).
        - If the last attendance is closed, the elapsed time is the final
          worked_hours converted to seconds: the kiosk shows it static.

        :param employee_id: int or None.
        :return: dict {'is_open': bool, 'elapsed_seconds': int} or None if
            the employee has no attendance record at all.
        """
        if not employee_id:
            return None
        attendance = (
            request.env["hr.attendance"]
            .sudo()
            .search(
                [("employee_id", "=", int(employee_id))],
                limit=1,
                order="check_in desc",
            )
        )
        if not attendance:
            return None
        if not attendance.check_out:
            elapsed = 0.0
            if attendance.check_in:
                elapsed = (fields.Datetime.now() - attendance.check_in).total_seconds()
            return {"is_open": True, "elapsed_seconds": int(max(elapsed, 0))}
        return {
            "is_open": False,
            "elapsed_seconds": int(max((attendance.worked_hours or 0.0) * 3600, 0)),
        }

    @http.route(
        "/pc_mes_kiosk/targets",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def get_targets(self, company_id=None, employee_id=None, **kwargs):
        """Return available projects and tasks for the kiosk imputation picker.

        Respects the module configuration flags pc_mes_kiosk.show_project and
        pc_mes_kiosk.show_task stored in ir.config_parameter.

        :param company_id: optional int — if provided, tasks/projects are
            filtered to that company.
        :param employee_id: optional int — if provided, the response includes
            the chronometer state of the employee's attendance.
        :return: dict with keys 'projects', 'tasks', 'mode', 'show_project',
            'show_task' and 'attendance' (chronometer state or None).
        """
        ICP = request.env["ir.config_parameter"].sudo()
        show_project = ICP.get_param("pc_mes_kiosk.show_project", "True") not in (
            "False", "0", ""
        )
        show_task = ICP.get_param("pc_mes_kiosk.show_task", "True") not in (
            "False", "0", ""
        )

        projects = []
        if show_project:
            project_domain = [("active", "=", True)]
            if company_id:
                project_domain.append(("company_id", "=", int(company_id)))
            project_records = (
                request.env["project.project"]
                .sudo()
                .search_fetch(project_domain, ["id", "name"], order="name asc")
            )
            projects = [{"id": p.id, "name": p.name} for p in project_records]

        tasks = []
        if show_task:
            # Exclude closed/cancelled stages — filter on stage fold
            # Include tasks with no stage as well as tasks in a non-folded
            # stage (a folded stage marks closed/cancelled work).
            task_domain = [
                "&",
                ("active", "=", True),
                "|",
                ("stage_id", "=", False),
                ("stage_id.fold", "=", False),
            ]
            if company_id:
                task_domain.append(("company_id", "=", int(company_id)))
            task_records = (
                request.env["project.task"]
                .sudo()
                .search_fetch(
                    task_domain,
                    ["id", "name", "project_id"],
                    order="name asc",
                )
            )
            tasks = [
                {
                    "id": t.id,
                    "name": t.name,
                    "project_id": t.project_id.id if t.project_id else False,
                }
                for t in task_records
            ]

        mode = ICP.get_param("pc_mes_kiosk.mode", "on_checkout")
        return {
            "projects": projects,
            "tasks": tasks,
            "mode": mode,
            "show_project": show_project,
            "show_task": show_task,
            "attendance": self._pc_attendance_chrono(employee_id),
        }

    @http.route(
        "/pc_mes_kiosk/set_target",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def set_target(self, employee_id, project_id=None, task_id=None, **kwargs):
        """Write the imputation target onto the employee's open attendance record.

        Locates the attendance record with check_out = False (still open) for
        the given employee and updates pc_project_id / pc_task_id.

        :param employee_id: int — mandatory.
        :param project_id: int or None.
        :param task_id: int or None.
        :return: dict {'ok': True, 'attendance': <chrono state>} on success,
            {'ok': False, 'error': str} on failure.
        """
        if not employee_id:
            return {"ok": False, "error": "employee_id is required"}

        attendance = (
            request.env["hr.attendance"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", int(employee_id)),
                    ("check_out", "=", False),
                ],
                limit=1,
                order="check_in desc",
            )
        )

        if not attendance:
            return {"ok": False, "error": "No open attendance record found for this employee"}

        vals = {}
        if project_id:
            vals["pc_project_id"] = int(project_id)
        if task_id:
            vals["pc_task_id"] = int(task_id)

        if vals:
            attendance.write(vals)

        return {"ok": True, "attendance": self._pc_attendance_chrono(employee_id)}
