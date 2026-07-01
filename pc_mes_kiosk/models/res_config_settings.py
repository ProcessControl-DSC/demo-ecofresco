# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pc_kiosk_mode = fields.Selection(
        selection=[
            ("on_checkin", "Ask on check-in"),
            ("on_checkout", "Ask on check-out"),
        ],
        string="Kiosk Imputation Prompt",
        config_parameter="pc_mes_kiosk.mode",
        default="on_checkout",
        help="When to ask the operator to select a project/task in the kiosk.",
    )
    pc_kiosk_show_project = fields.Boolean(
        string="Show Project Selector",
        config_parameter="pc_mes_kiosk.show_project",
        default=True,
        help="If enabled, the kiosk will offer a project selection.",
    )
    pc_kiosk_show_task = fields.Boolean(
        string="Show Task Selector",
        config_parameter="pc_mes_kiosk.show_task",
        default=True,
        help="If enabled, the kiosk will offer a task selection.",
    )
