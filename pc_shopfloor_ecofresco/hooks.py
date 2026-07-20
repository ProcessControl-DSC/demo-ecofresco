# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Flag the demo's known indirect-work projects (Limpieza, Almacén) as
    eligible for the Shop Floor "Tareas indirectas" dialog, so the feature
    works out of the box on this demo without a manual configuration step.

    Matches by exact project name. Safe no-op if neither project exists:
    the feature still works, the user just has to tick the "Tarea
    indirecta Shop Floor" checkbox manually on whichever project(s) should
    appear in the dialog (Proyecto > <proyecto> > pestaña general).
    """
    projects = env["project.project"].search([
        ("name", "in", ["Limpieza", "Almacén", "Almacen"]),
    ])
    if projects:
        projects.write({"pc_shopfloor_indirect_task": True})
        _logger.info(
            "pc_shopfloor_ecofresco: flagged %s project(s) as Shop Floor "
            "indirect task source: %s",
            len(projects),
            ", ".join(projects.mapped("name")),
        )
    else:
        _logger.info(
            "pc_shopfloor_ecofresco: no 'Limpieza'/'Almacén' project found "
            "at install time, skipping indirect task auto-flag; mark "
            "projects manually via the 'Tarea indirecta Shop Floor' "
            "checkbox on the project form."
        )
