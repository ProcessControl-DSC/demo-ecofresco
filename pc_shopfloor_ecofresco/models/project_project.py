# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ProjectProject(models.Model):
    _inherit = "project.project"

    pc_shopfloor_indirect_task = fields.Boolean(
        string="Tarea indirecta Shop Floor",
        help="Si está marcado, las tareas abiertas de este proyecto aparecen "
        'en el diálogo "Tareas indirectas" de la app Shop Floor '
        "(mrp_display), para que los operarios puedan imputar tiempo a "
        "trabajo que no es de producción (limpieza, almacén...) sin salir "
        "del panel.",
    )
