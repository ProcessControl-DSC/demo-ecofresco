# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    def register_weighing(self, qty, lot_name=None):
        """Record a (simulated) weighing result on this component's move line.

        Writes the weighed quantity on the first stock.move.line of this
        move — creating it if the component was not reserved yet — and
        marks it as 'picked' so it is taken into account when the
        manufacturing order is produced/consumed.

        If the product is tracked by lot or serial number, resolves (by
        lot_name) or creates a stock.lot and links it to the move line.
        When product_expiry is installed, the lot's expiration date is
        computed automatically by that module on creation — it is never
        set manually here.

        :param qty: float — weighed quantity, expressed in the move's UoM.
        :param lot_name: str or None — lot/serial name to use; if not
            given and the product is tracked, a lot named "PES-<timestamp>"
            is generated.
        :return: dict {'recorded_qty': float, 'lot': str or False}
        """
        self.ensure_one()

        move_line = self.move_line_ids[:1]
        if move_line:
            move_line.quantity = qty
            move_line.picked = True
        else:
            move_line_vals = self._prepare_move_line_vals(quantity=qty)
            move_line_vals["picked"] = True
            move_line = self.env["stock.move.line"].create([move_line_vals])

        lot = False
        if self.product_id.tracking != "none":
            Lot = self.env["stock.lot"]
            name = lot_name or "PES-%s" % fields.Datetime.now().strftime(
                "%Y%m%d%H%M%S"
            )
            lot_record = Lot.search(
                [("name", "=", name), ("product_id", "=", self.product_id.id)],
                limit=1,
            )
            if not lot_record:
                lot_record = Lot.create(
                    {"name": name, "product_id": self.product_id.id}
                )
            move_line.lot_id = lot_record.id
            lot = lot_record.name

        return {"recorded_qty": move_line.quantity, "lot": lot}
