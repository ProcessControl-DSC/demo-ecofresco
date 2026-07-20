# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pc_kiosk_mode = fields.Selection(
        selection=[
            ("on_checkin", "Al fichar entrada"),
            ("on_checkout", "Al fichar salida"),
        ],
        string="Momento de la pregunta en el kiosco",
        config_parameter="pc_mes_kiosk.mode",
        default="on_checkout",
        help="Cuándo se pide al operario que elija proyecto/tarea en el kiosco.",
    )
    pc_kiosk_show_project = fields.Boolean(
        string="Mostrar selector de proyecto",
        config_parameter="pc_mes_kiosk.show_project",
        default=True,
        help="Si está activo, el kiosco ofrece la selección de proyecto.",
    )
    pc_kiosk_show_task = fields.Boolean(
        string="Mostrar selector de tarea",
        config_parameter="pc_mes_kiosk.show_task",
        default=True,
        help="Si está activo, el kiosco ofrece la selección de tarea.",
    )
