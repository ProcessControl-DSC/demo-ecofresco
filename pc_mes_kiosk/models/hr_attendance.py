# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    pc_project_id = fields.Many2one(
        "project.project",
        string="Imputation Project",
        help="Project to which the worked hours will be imputed.",
    )
    pc_task_id = fields.Many2one(
        "project.task",
        string="Imputation Task",
        help="Task to which the worked hours will be imputed.",
    )
    pc_timesheet_line_id = fields.Many2one(
        "account.analytic.line",
        string="Generated Timesheet Entry",
        readonly=True,
        copy=False,
        help="Timesheet line automatically created when the attendance is closed.",
    )

    def _pc_impute(self):
        """Create a timesheet entry for a closed attendance record.

        Called after check_out is set. Only runs when:
        - worked_hours > 0
        - pc_project_id or pc_task_id is set
        - pc_timesheet_line_id is not yet linked (idempotent guard)
        """
        self.ensure_one()
        if not self.worked_hours or self.pc_timesheet_line_id:
            return
        if not (self.pc_project_id or self.pc_task_id):
            return

        # Resolve project: prefer the task's project, fall back to direct project field
        project = (
            self.pc_task_id.project_id if self.pc_task_id else self.pc_project_id
        )
        if not project:
            return

        # Resolve user from employee (hr_timesheet links employee → user)
        user = self.employee_id.user_id

        analytic_line = self.env["account.analytic.line"].sudo().create({
            "name": _("Kiosk: %s") % self.employee_id.name,
            "project_id": project.id,
            "task_id": self.pc_task_id.id if self.pc_task_id else False,
            "employee_id": self.employee_id.id,
            "user_id": user.id if user else False,
            "unit_amount": self.worked_hours,
            "date": self.check_in.date() if self.check_in else fields.Date.today(),
        })
        # Link back without triggering another write cycle
        self.sudo().write({"pc_timesheet_line_id": analytic_line.id})

    def write(self, vals):
        """Override to trigger timesheet imputation when check_out is set."""
        res = super().write(vals)
        if "check_out" in vals and vals.get("check_out"):
            # Only process records that are now closed and have an imputation target
            for record in self:
                if record.check_out and not record.pc_timesheet_line_id:
                    record._pc_impute()
        return res
