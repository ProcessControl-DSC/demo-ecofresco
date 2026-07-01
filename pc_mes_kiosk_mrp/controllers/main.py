# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
import logging

from odoo import http
from odoo.http import request

from odoo.addons.pc_mes_kiosk.controllers.main import PcMesKioskController

_logger = logging.getLogger(__name__)


class PcMesKioskMrpController(PcMesKioskController):
    """Extends the PC MES Kiosk controller with Manufacturing Work Order endpoints.

    New endpoints:
      - /pc_mes_kiosk/workorders   — list active manufacturing orders + workorders
      - /pc_mes_kiosk/mo_formula   — BOM components for a given production order
      - /pc_mes_kiosk/start_workorder — start employee time on a workorder
      - /pc_mes_kiosk/stop_workorder  — stop employee time on a workorder

    Also overrides /pc_mes_kiosk/targets to include 'show_workorder' in the
    response payload so the frontend can show/hide the MRP path.

    Time is recorded exclusively in mrp.workcenter.productivity via
    mrp.workorder.start_employee / stop_employee — no analytic lines are
    created here (Odoo creates them via project_mrp_workorder_account if that
    module is installed).
    """

    # ── Override: targets — add show_workorder flag ────────────────────────

    @http.route(
        "/pc_mes_kiosk/targets",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def get_targets(self, company_id=None, **kwargs):
        """Extend the base targets response with the show_workorder flag."""
        result = super().get_targets(company_id=company_id, **kwargs)
        ICP = request.env["ir.config_parameter"].sudo()
        show_workorder = ICP.get_param(
            "pc_mes_kiosk.show_workorder", "True"
        ) not in ("False", "0", "")
        result["show_workorder"] = show_workorder
        return result

    # ── /pc_mes_kiosk/workorders ───────────────────────────────────────────

    @http.route(
        "/pc_mes_kiosk/workorders",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def get_workorders(self, **kwargs):
        """Return active manufacturing orders with their work orders.

        Only orders in states 'confirmed', 'progress' or 'to_close' are
        included.  For each order we return its open work orders (state not
        in ('done', 'cancel')).

        :return: list of dicts:
            [{
                id: int,
                name: str,
                product: str,
                qty: float,
                uom: str,
                workorders: [{id, name, state, workcenter}]
            }]
        """
        MO = request.env["mrp.production"].sudo()
        productions = MO.search(
            [("state", "in", ["confirmed", "progress", "to_close"])],
            order="name asc",
        )

        result = []
        for prod in productions:
            workorders = []
            for wo in prod.workorder_ids.filtered(
                lambda w: w.state not in ("done", "cancel")
            ):
                workorders.append(
                    {
                        "id": wo.id,
                        "name": wo.name,
                        "state": wo.state,
                        "workcenter": wo.workcenter_id.name if wo.workcenter_id else "",
                    }
                )
            result.append(
                {
                    "id": prod.id,
                    "name": prod.name,
                    "product": prod.product_id.display_name if prod.product_id else "",
                    "qty": prod.product_qty,
                    "uom": prod.product_uom_id.name if prod.product_uom_id else "",
                    "workorders": workorders,
                }
            )
        return result

    # ── /pc_mes_kiosk/mo_formula ───────────────────────────────────────────

    @http.route(
        "/pc_mes_kiosk/mo_formula",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def get_mo_formula(self, production_id, **kwargs):
        """Return the component lines (BOM formula) for a manufacturing order.

        Reads move_raw_ids and resolves lot/expiration_date from the first
        linked stock.move.line when available.

        :param production_id: int — id of mrp.production.
        :return: list of dicts:
            [{product, qty, uom, lot, expiration_date}]
        """
        if not production_id:
            return {"error": "production_id is required"}

        prod = (
            request.env["mrp.production"]
            .sudo()
            .browse(int(production_id))
        )
        if not prod.exists():
            return {"error": "Manufacturing order not found"}

        components = []
        for move in prod.move_raw_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        ):
            # Try to resolve lot from the first detailed operation line
            lot_name = ""
            expiration_date = ""
            for ml in move.move_line_ids[:1]:
                if ml.lot_id:
                    lot_name = ml.lot_id.name
                    # product_expiry adds expiration_date on stock.lot
                    if hasattr(ml.lot_id, "expiration_date") and ml.lot_id.expiration_date:
                        expiration_date = ml.lot_id.expiration_date.strftime(
                            "%Y-%m-%d"
                        )
            components.append(
                {
                    "product": move.product_id.display_name if move.product_id else "",
                    "qty": move.product_qty,
                    "uom": move.product_uom.name if move.product_uom else "",
                    "lot": lot_name,
                    "expiration_date": expiration_date,
                }
            )
        return components

    # ── /pc_mes_kiosk/start_workorder ─────────────────────────────────────

    @http.route(
        "/pc_mes_kiosk/start_workorder",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def start_workorder(self, employee_id, workorder_id, **kwargs):
        """Start employee time tracking on a manufacturing work order.

        Calls mrp.workorder.start_employee(employee_id) which:
          - links the employee to the workorder
          - creates an mrp.workcenter.productivity record (date_start = now,
            date_end = False)
          - transitions the workorder state to 'progress'

        Time is stored in mrp.workcenter.productivity ONLY — no analytic lines
        are created here.

        :param employee_id: int
        :param workorder_id: int
        :return: {'ok': True} on success, {'ok': False, 'error': str} on failure.
        """
        if not employee_id or not workorder_id:
            return {"ok": False, "error": "employee_id and workorder_id are required"}

        wo = (
            request.env["mrp.workorder"]
            .sudo()
            .browse(int(workorder_id))
        )
        if not wo.exists():
            return {"ok": False, "error": "Work order not found"}

        try:
            wo.start_employee(int(employee_id))
        except Exception as exc:
            _logger.warning("pc_mes_kiosk_mrp: start_workorder error: %s", exc)
            return {"ok": False, "error": str(exc)}

        return {"ok": True}

    # ── /pc_mes_kiosk/stop_workorder ──────────────────────────────────────

    @http.route(
        "/pc_mes_kiosk/stop_workorder",
        type="json",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def stop_workorder(self, employee_id, workorder_id, **kwargs):
        """Stop employee time tracking on a manufacturing work order.

        Calls mrp.workorder.stop_employee([employee_id]) which closes all open
        mrp.workcenter.productivity records for this employee on this workorder
        (sets date_end = now and computes duration).

        :param employee_id: int
        :param workorder_id: int
        :return: {'ok': True} on success, {'ok': False, 'error': str} on failure.
        """
        if not employee_id or not workorder_id:
            return {"ok": False, "error": "employee_id and workorder_id are required"}

        wo = (
            request.env["mrp.workorder"]
            .sudo()
            .browse(int(workorder_id))
        )
        if not wo.exists():
            return {"ok": False, "error": "Work order not found"}

        try:
            wo.stop_employee([int(employee_id)])
        except Exception as exc:
            _logger.warning("pc_mes_kiosk_mrp: stop_workorder error: %s", exc)
            return {"ok": False, "error": str(exc)}

        return {"ok": True}
