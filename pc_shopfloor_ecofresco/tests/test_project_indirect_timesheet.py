# Copyright 2026 Process Control (https://www.processcontrol.es)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestShopfloorIndirectTimesheet(TransactionCase):
    """Unit tests for the Shop Floor "Tareas indirectas" backend: listing
    eligible tasks and creating the resulting timesheet for the connected
    operator.

    ``hr.employee.get_session_owner()`` (defined in ``mrp_workorder``) reads
    ``request.session``, which does not exist outside of an HTTP request; in
    that case it falls back to ``[self.env.user.employee_id.id]``. We make
    sure the current test user has an employee so that fallback resolves to
    a real record, and assert against ``env.user.employee_id`` directly
    rather than hardcoding which employee that is.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if not cls.env.user.employee_id:
            cls.env["hr.employee"].create({
                "name": "Test Shop Floor Operator",
                "user_id": cls.env.user.id,
            })
        cls.employee = cls.env.user.employee_id

        cls.indirect_project = cls.env["project.project"].create({
            "name": "Limpieza Test",
            "pc_shopfloor_indirect_task": True,
        })
        cls.other_project = cls.env["project.project"].create({
            "name": "Producción Planta Test",
            "pc_shopfloor_indirect_task": False,
        })
        cls.indirect_task = cls.env["project.task"].create({
            "name": "Limpieza línea 1",
            "project_id": cls.indirect_project.id,
        })
        cls.other_task = cls.env["project.task"].create({
            "name": "Orden de fabricación 123",
            "project_id": cls.other_project.id,
        })

    def _close_task(self, task):
        """Move a task to a folded (closed) stage, mirroring how a real
        "Done"/"Cancelled" Kanban stage marks a task as closed
        (``project.task.is_closed`` follows ``stage_id.fold``)."""
        stage = self.env["project.task.type"].create({
            "name": "Test Done",
            "fold": True,
        })
        task.write({"stage_id": stage.id})

    # -- pc_shopfloor_get_indirect_tasks ---------------------------------

    def test_get_indirect_tasks_only_returns_flagged_projects(self):
        result = self.env["project.task"].pc_shopfloor_get_indirect_tasks()
        ids = [task["id"] for task in result]
        self.assertIn(self.indirect_task.id, ids)
        self.assertNotIn(self.other_task.id, ids)

    def test_get_indirect_tasks_returns_expected_shape(self):
        result = self.env["project.task"].pc_shopfloor_get_indirect_tasks()
        entry = next(task for task in result if task["id"] == self.indirect_task.id)
        self.assertEqual(entry["name"], self.indirect_task.name)
        self.assertEqual(entry["project_id"], self.indirect_project.id)
        self.assertEqual(entry["project_name"], self.indirect_project.name)

    def test_get_indirect_tasks_excludes_closed_tasks(self):
        self._close_task(self.indirect_task)
        self.assertTrue(self.indirect_task.is_closed)
        result = self.env["project.task"].pc_shopfloor_get_indirect_tasks()
        ids = [task["id"] for task in result]
        self.assertNotIn(self.indirect_task.id, ids)

    # -- pc_shopfloor_create_indirect_timesheet --------------------------

    def test_create_indirect_timesheet_for_connected_employee(self):
        result = self.env["account.analytic.line"].pc_shopfloor_create_indirect_timesheet(
            self.indirect_task.id, 5400  # 1.5h
        )
        line = self.env["account.analytic.line"].browse(result["id"])
        self.assertEqual(line.project_id, self.indirect_project)
        self.assertEqual(line.task_id, self.indirect_task)
        self.assertEqual(line.employee_id, self.employee)
        self.assertAlmostEqual(line.unit_amount, 1.5)
        self.assertAlmostEqual(result["unit_amount"], 1.5)

    def test_create_indirect_timesheet_rejects_non_indirect_task(self):
        with self.assertRaises(UserError):
            self.env["account.analytic.line"].pc_shopfloor_create_indirect_timesheet(
                self.other_task.id, 3600
            )

    def test_create_indirect_timesheet_rejects_zero_duration(self):
        with self.assertRaises(UserError):
            self.env["account.analytic.line"].pc_shopfloor_create_indirect_timesheet(
                self.indirect_task.id, 0
            )

    def test_create_indirect_timesheet_rejects_unknown_task(self):
        missing_id = self.env["project.task"].search([], order="id desc", limit=1).id + 100000
        with self.assertRaises(UserError):
            self.env["account.analytic.line"].pc_shopfloor_create_indirect_timesheet(
                missing_id, 3600
            )

    # -- hr.employee._pc_shopfloor_get_connected_employee ----------------

    def test_get_connected_employee_unwraps_test_fallback_list(self):
        connected = self.env["hr.employee"]._pc_shopfloor_get_connected_employee()
        self.assertEqual(connected, self.employee)
