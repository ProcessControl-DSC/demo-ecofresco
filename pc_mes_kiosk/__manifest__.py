# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
{
    "name": "PC MES Kiosk",
    "summary": "Extend attendance kiosk to capture project/task imputation and create timesheet entries",
    "version": "19.0.1.2.0",
    "category": "Human Resources/Attendances",
    "author": "Process Control",
    "website": "https://www.processcontrol.es",
    "license": "LGPL-3",
    "depends": [
        "hr_attendance",
        "hr_timesheet",
        "project",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "hr_attendance.assets_public_attendance": [
            "pc_mes_kiosk/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
