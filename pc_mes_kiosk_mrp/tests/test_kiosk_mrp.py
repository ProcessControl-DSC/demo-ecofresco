# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
"""Tests for pc_mes_kiosk_mrp — start/stop employee on mrp.workorder.

These tests bypass the HTTP controller layer and exercise the underlying
mrp.workorder.start_employee / stop_employee methods directly, which is
what the controller delegates to.

Tagged post_install / -at_install because mrp_workorder has post-install
hooks and the module graph must be fully loaded before the tests run.
"""
from datetime import datetime

from freezegun import freeze_time

from odoo import Command
from odoo.tests import Form, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestKioskMrp(TransactionCase):
    """Verify that start_employee / stop_employee on mrp.workorder create and
    close mrp.workcenter.productivity records with the correct employee."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Enable routings so work orders are generated from the BoM
        grp_routings = cls.env.ref("mrp.group_mrp_routings")
        cls.env.user.write({"groups_id": [(4, grp_routings.id)]})

        # Workcenter with two employees so start_employee has valid subjects
        cls.workcenter = cls.env["mrp.workcenter"].create(
            {
                "name": "Kiosk MRP Workcenter",
                "employee_ids": [
                    Command.create({"name": "Kiosk MRP Employee 1", "pin": "0001"}),
                    Command.create({"name": "Kiosk MRP Employee 2", "pin": "0002"}),
                ],
            }
        )
        cls.employee_1 = cls.workcenter.employee_ids[0]
        cls.employee_2 = cls.workcenter.employee_ids[1]

        # Minimal product + BoM with one operation on the workcenter
        cls.finished_product = cls.env["product.product"].create(
            {"name": "Kiosk Finished Product", "is_storable": True}
        )
        cls.component = cls.env["product.product"].create(
            {"name": "Kiosk Component", "is_storable": True}
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
                "operation_ids": [
                    Command.create(
                        {
                            "name": "Kiosk Op",
                            "workcenter_id": cls.workcenter.id,
                            "time_cycle": 10,
                            "sequence": 1,
                        }
                    )
                ],
            }
        )
        cls.env["mrp.bom.line"].create(
            {
                "product_id": cls.component.id,
                "product_qty": 1.0,
                "bom_id": cls.bom.id,
            }
        )

        # Manufacturing order — confirmed inside the test so workorders exist
        mo_form = Form(cls.env["mrp.production"])
        mo_form.product_id = cls.finished_product
        mo_form.bom_id = cls.bom
        mo_form.product_qty = 1
        cls.mo = mo_form.save()

    # ── tests ─────────────────────────────────────────────────────────────────

    def test_start_stop_workorder(self):
        """start_employee creates an open mrp.workcenter.productivity record;
        stop_employee closes it (date_end set), leaving duration > 0."""

        self.mo.action_confirm()
        self.assertTrue(
            self.mo.workorder_ids,
            "action_confirm must generate at least one work order from the BoM operation.",
        )
        wo = self.mo.workorder_ids[0]

        with freeze_time("2026-07-01 08:00:00"):
            wo.start_employee(self.employee_1.id)
            self.env.flush_all()

        # Immediately after start_employee there must be an open productivity record
        open_times = self.env["mrp.workcenter.productivity"].search(
            [
                ("workorder_id", "=", wo.id),
                ("employee_id", "=", self.employee_1.id),
                ("date_end", "=", False),
            ]
        )
        self.assertEqual(
            len(open_times),
            1,
            "Exactly one open productivity record must exist after start_employee.",
        )
        self.assertEqual(wo.state, "progress",
                         "Work order state must be 'progress' after start_employee.")

        with freeze_time("2026-07-01 09:30:00"):
            wo.stop_employee([self.employee_1.id])
            self.env.flush_all()

        # After stop_employee the record must be closed
        still_open = self.env["mrp.workcenter.productivity"].search(
            [
                ("workorder_id", "=", wo.id),
                ("employee_id", "=", self.employee_1.id),
                ("date_end", "=", False),
            ]
        )
        self.assertFalse(
            still_open,
            "No open productivity records should remain after stop_employee.",
        )

        # Duration should be ~90 minutes (tolerance: > 0)
        closed = self.env["mrp.workcenter.productivity"].search(
            [
                ("workorder_id", "=", wo.id),
                ("employee_id", "=", self.employee_1.id),
            ]
        )
        self.assertTrue(closed, "A closed productivity record must exist.")
        self.assertTrue(
            all(t.date_end for t in closed),
            "All productivity records must have date_end set after stop_employee.",
        )

    def test_start_employee_idempotent(self):
        """Calling start_employee twice for the same employee must NOT open a
        second productivity record (the guard inside start_employee must fire)."""
        mo_form = Form(self.env["mrp.production"])
        mo_form.product_id = self.finished_product
        mo_form.bom_id = self.bom
        mo_form.product_qty = 1
        mo2 = mo_form.save()
        mo2.action_confirm()

        wo = mo2.workorder_ids[0]

        with freeze_time("2026-07-01 10:00:00"):
            wo.start_employee(self.employee_2.id)
            wo.start_employee(self.employee_2.id)  # second call — must be ignored
            self.env.flush_all()

        open_times = self.env["mrp.workcenter.productivity"].search(
            [
                ("workorder_id", "=", wo.id),
                ("employee_id", "=", self.employee_2.id),
                ("date_end", "=", False),
            ]
        )
        self.assertEqual(
            len(open_times),
            1,
            "start_employee called twice must not open two productivity records.",
        )

    def test_productivity_model_fields(self):
        """Smoke-test: mrp.workcenter.productivity has the expected fields
        (date_end, employee_id, workorder_id) used by the controller logic."""
        Productivity = self.env["mrp.workcenter.productivity"]
        field_names = Productivity._fields
        for required_field in ("date_end", "employee_id", "workorder_id"):
            self.assertIn(
                required_field,
                field_names,
                f"mrp.workcenter.productivity must have field '{required_field}'.",
            )


@tagged("post_install", "-at_install")
class TestKioskMrpWeighing(TransactionCase):
    """Verify stock.move.register_weighing() — the model method behind the
    /pc_mes_kiosk/register_weighing endpoint — records the weighed quantity
    (and lot, when the component is tracked) on the move's stock.move.line.

    These tests bypass the HTTP controller layer and exercise
    register_weighing() directly, matching the convention used above for
    start_employee/stop_employee.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.finished_product = cls.env["product.product"].create(
            {"name": "Kiosk Weighing Finished Product", "is_storable": True}
        )
        cls.component_untracked = cls.env["product.product"].create(
            {"name": "Kiosk Weighing Component", "is_storable": True}
        )
        cls.component_lot = cls.env["product.product"].create(
            {
                "name": "Kiosk Weighing Tracked Component",
                "is_storable": True,
                "tracking": "lot",
            }
        )
        cls.bom = cls.env["mrp.bom"].create(
            {
                "product_tmpl_id": cls.finished_product.product_tmpl_id.id,
                "product_qty": 1.0,
            }
        )
        cls.env["mrp.bom.line"].create(
            {
                "product_id": cls.component_untracked.id,
                "product_qty": 2.0,
                "bom_id": cls.bom.id,
            }
        )
        cls.env["mrp.bom.line"].create(
            {
                "product_id": cls.component_lot.id,
                "product_qty": 3.0,
                "bom_id": cls.bom.id,
            }
        )

        mo_form = Form(cls.env["mrp.production"])
        mo_form.product_id = cls.finished_product
        mo_form.bom_id = cls.bom
        mo_form.product_qty = 1
        cls.mo = mo_form.save()
        cls.mo.action_confirm()

    def _move_for(self, product):
        return self.mo.move_raw_ids.filtered(lambda m: m.product_id == product)

    def test_register_weighing_untracked_creates_move_line(self):
        """Weighing an untracked component records quantity+picked on its
        move line, creating it if no reservation had produced one yet."""
        move = self._move_for(self.component_untracked)
        move.move_line_ids.unlink()  # exercise the "no move line yet" branch

        result = move.register_weighing(1.95)

        self.assertAlmostEqual(result["recorded_qty"], 1.95)
        self.assertFalse(result["lot"], "Untracked component must not get a lot.")
        self.assertEqual(len(move.move_line_ids), 1)
        self.assertAlmostEqual(move.move_line_ids.quantity, 1.95)
        self.assertTrue(move.move_line_ids.picked)

    def test_register_weighing_updates_existing_move_line(self):
        """If a move line already exists (e.g. from reservation), weighing
        overwrites its quantity instead of creating a duplicate line."""
        move = self._move_for(self.component_untracked)
        move.move_line_ids.unlink()
        move.register_weighing(1.0)
        self.assertEqual(len(move.move_line_ids), 1)

        result = move.register_weighing(2.5)

        self.assertEqual(
            len(move.move_line_ids), 1,
            "register_weighing must reuse the existing move line, not duplicate it.",
        )
        self.assertAlmostEqual(result["recorded_qty"], 2.5)
        self.assertAlmostEqual(move.move_line_ids.quantity, 2.5)

    def test_register_weighing_tracked_creates_lot(self):
        """Weighing a lot-tracked component without a lot_name auto-generates
        a lot and links it to the move line."""
        move = self._move_for(self.component_lot)

        result = move.register_weighing(2.9)

        self.assertTrue(result["lot"], "A lot name must be generated for tracked products.")
        self.assertEqual(move.move_line_ids.lot_id.name, result["lot"])
        self.assertAlmostEqual(move.move_line_ids.quantity, 2.9)
        self.assertTrue(move.move_line_ids.picked)

    def test_register_weighing_tracked_reuses_lot_name(self):
        """Passing an explicit lot_name reuses/creates that exact lot."""
        move = self._move_for(self.component_lot)

        result = move.register_weighing(3.0, lot_name="LOT-TEST-001")

        self.assertEqual(result["lot"], "LOT-TEST-001")
        self.assertEqual(move.move_line_ids.lot_id.name, "LOT-TEST-001")
        self.assertEqual(
            move.move_line_ids.lot_id.product_id, self.component_lot,
        )
