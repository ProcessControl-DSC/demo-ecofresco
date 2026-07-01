# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "PC MES Kiosk - Manufacturing",
    "summary": "Extend the MES attendance kiosk with a Production / Work Order path",
    "version": "19.0.1.0.0",
    "category": "Manufacturing",
    "author": "Process Control",
    "website": "https://www.processcontrol.es",
    "license": "LGPL-3",
    "depends": [
        "pc_mes_kiosk",
        "mrp_workorder",
        "stock_barcode",
        "product_expiry",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "hr_attendance.assets_public_attendance": [
            "pc_mes_kiosk_mrp/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
