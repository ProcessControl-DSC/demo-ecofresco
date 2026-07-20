# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.model
    def pc_shopfloor_create_indirect_timesheet(self, task_id, duration_seconds):
        """Create a timesheet entry for an indirect project task (cleaning,
        warehouse...) from the Shop Floor "Tareas indirectas" dialog,
        credited to the currently connected operator.

        The employee is never trusted from the client: it is always
        resolved server-side from the Shop Floor session
        (``hr.employee.get_session_owner()``, via
        ``_pc_shopfloor_get_connected_employee``), exactly like every other
        Shop Floor write (start/stop workorder, login/logout...).

        :param task_id: int — must belong to a project flagged
            ``pc_shopfloor_indirect_task``, otherwise rejected.
        :param duration_seconds: int/float — elapsed time measured
            client-side (browser chronometer); converted to hours here.
        :return: dict {'id': <new line id>, 'unit_amount': <hours>}
        :raises UserError: no operator connected, invalid task, or zero
            duration.
        """
        employee = self.env["hr.employee"]._pc_shopfloor_get_connected_employee()
        if not employee:
            raise UserError(_("No hay ningún operario conectado en Shop Floor."))

        task = self.env["project.task"].sudo().browse(int(task_id)).exists()
        if not task or not task.project_id.pc_shopfloor_indirect_task:
            raise UserError(
                _("La tarea seleccionada no es una tarea indirecta válida.")
            )

        unit_amount = max(float(duration_seconds or 0.0), 0.0) / 3600.0
        if not unit_amount:
            raise UserError(_("El tiempo imputado debe ser mayor que cero."))

        line = self.sudo().create({
            "name": _("Shop Floor: %s") % task.name,
            "project_id": task.project_id.id,
            "task_id": task.id,
            "employee_id": employee.id,
            "user_id": employee.user_id.id if employee.user_id else False,
            "unit_amount": unit_amount,
            "date": fields.Date.context_today(self),
        })
        return {"id": line.id, "unit_amount": line.unit_amount}
