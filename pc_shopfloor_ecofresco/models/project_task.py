# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import models


class ProjectTask(models.Model):
    _inherit = "project.task"

    def pc_shopfloor_get_indirect_tasks(self):
        """Return the open tasks eligible for the Shop Floor "Tareas
        indirectas" dialog: tasks whose project is flagged
        ``pc_shopfloor_indirect_task`` (e.g. Limpieza, Almacén), excluding
        tasks already closed (folded stage).

        Called via ``orm.call`` from the Shop Floor client with sudo, since
        Shop Floor operators are not expected to have Project access.

        :return: list of dicts {id, name, project_id, project_name}
        """
        tasks = self.sudo().search(
            [
                ("project_id.pc_shopfloor_indirect_task", "=", True),
                ("is_closed", "=", False),
            ],
            order="project_id, name",
        )
        return [
            {
                "id": task.id,
                "name": task.name,
                "project_id": task.project_id.id,
                "project_name": task.project_id.name,
            }
            for task in tasks
        ]
