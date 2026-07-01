# PC MES Kiosk

Extends the Odoo attendance kiosk to capture project and task imputation at check-in or check-out, and generates timesheet entries automatically.

## Description

This module integrates the MES (Manufacturing Execution System) workflow into the standard Odoo HR Attendance kiosk. After an employee checks in or out, a touch-friendly screen appears allowing the operator to select the project and/or task to which the worked hours should be imputed. When the attendance record is closed (check_out set), a timesheet line (`account.analytic.line`) is created automatically and linked back to the attendance record.

The imputation screen is configurable: it can appear on check-in or on check-out, and the project and task selectors can be enabled or disabled independently from the Settings menu.

## Compatibility

| Odoo version | Status        |
|--------------|---------------|
| 19.0         | Supported     |

## Dependencies

- `hr_attendance` — native HR Attendance module (kiosk included)
- `hr_timesheet` — timesheet / analytic line model
- `project` — project and task models

## Installation

1. Copy the `pc_mes_kiosk` directory into your Odoo addons path.
2. Update the module list: Settings > Apps > Update Apps List.
3. Search for "PC MES Kiosk" and click Install.
4. A module update (`-u pc_mes_kiosk`) is required if the module was already installed and new fields have been added.

## Configuration

Navigate to Settings > Attendances. A new block "MES Kiosk — Project Imputation" appears with three options:

- Imputation Prompt Timing: choose "Ask on check-in" or "Ask on check-out". Determines at which event the selector screen is displayed.
- Show Project Selector: enables or disables the project picker step.
- Show Task Selector: enables or disables the task picker step.

These parameters are stored as `ir.config_parameter` values (`pc_mes_kiosk.mode`, `pc_mes_kiosk.show_project`, `pc_mes_kiosk.show_task`) and are read by the public kiosk controller without authentication.

## Usage

1. Open the attendance kiosk in the browser (the public URL served by `hr_attendance`).
2. The employee identifies via PIN or badge as usual.
3. Depending on the configured timing, the MES target selector screen appears:
   - If "Show Project Selector" is enabled, a grid of active projects is displayed.
   - After selecting a project, the list of active tasks for that project is shown (if "Show Task Selector" is enabled).
   - The operator can tap "Project only" to confirm without selecting a task, or "Skip" to bypass imputation entirely.
4. On confirmation, the open attendance record is updated with the selected project and/or task.
5. When the employee checks out and `check_out` is written to the attendance record, the `_pc_impute` method creates an `account.analytic.line` with the worked hours and links it to the attendance.

## Relevant models and fields

### hr.attendance (extended)

| Field                   | Type      | Description                                                         |
|-------------------------|-----------|---------------------------------------------------------------------|
| `pc_project_id`         | Many2one  | Project selected by the operator in the kiosk.                      |
| `pc_task_id`            | Many2one  | Task selected by the operator in the kiosk.                         |
| `pc_timesheet_line_id`  | Many2one  | Timesheet line created automatically after check-out (readonly).    |

### res.config.settings (extended)

| Field                    | Type      | Config parameter              | Default      |
|--------------------------|-----------|-------------------------------|--------------|
| `pc_kiosk_mode`          | Selection | `pc_mes_kiosk.mode`           | `on_checkout`|
| `pc_kiosk_show_project`  | Boolean   | `pc_mes_kiosk.show_project`   | `True`       |
| `pc_kiosk_show_task`     | Boolean   | `pc_mes_kiosk.show_task`      | `True`       |

### HTTP endpoints (public, JSON-RPC)

- `POST /pc_mes_kiosk/targets` — returns available projects and tasks plus current config flags.
- `POST /pc_mes_kiosk/set_target` — writes `pc_project_id` / `pc_task_id` on the employee's open attendance.

## Known limitations

- The timesheet line is created with `sudo()` to ensure it can be written regardless of the kiosk user's access rights. The resulting analytic line is owned by the employee's linked Odoo user.
- If the employee has no linked Odoo user (`employee_id.user_id` is empty), `user_id` on the analytic line will be left blank.
- Tasks are filtered to non-folded stages only. Tasks in folded (closed/cancelled) stages are not visible in the kiosk.
- There is no multi-project imputation per attendance: one attendance record maps to one project and one task.
- The `_pc_impute` method is idempotent: if `pc_timesheet_line_id` is already set, it will not create a duplicate. However, manual deletion of the timesheet line and a subsequent re-write of `check_out` will not re-trigger creation.

## Tests

Tests are located in `tests/`. They cover:

- Field creation on `hr.attendance`.
- `_pc_impute` logic: timesheet line creation, idempotency guard, fallback to direct project when no task is provided.
- `write` override: trigger on `check_out`.
- Controller endpoints: `get_targets` respects `show_project` / `show_task` flags; `set_target` updates the open attendance record.
