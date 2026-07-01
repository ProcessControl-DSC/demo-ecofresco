# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pc_kiosk_show_workorder = fields.Boolean(
        string="Show Work Order Selector",
        config_parameter="pc_mes_kiosk.show_workorder",
        default=True,
        help=(
            "If enabled, the kiosk will offer a Production / Work Order "
            "path so operators can log time against manufacturing work orders."
        ),
    )
