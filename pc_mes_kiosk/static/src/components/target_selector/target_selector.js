/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

/**
 * PcMesTargetSelector — tablet-friendly project/task picker shown inside the
 * attendance kiosk after check-in (or check-out, depending on configuration).
 *
 * Once the project/task is chosen (or the operator skips it), the component
 * shows a small "work screen" confirmation with two big buttons — "Pausa"
 * and "Fichar salida" — so the operator can close the workday (or take a
 * break) without leaving this app: they don't need to walk back to the main
 * kiosk screen and re-enter their PIN. Both buttons reuse the native
 * check-in/check-out toggle (hr_attendance has no separate "break" state —
 * a pause IS a check-out; resuming later is a normal check-in again).
 *
 * Props:
 *   employeeId  {Number}  — id of the employee who just checked in/out.
 *   onDone      {Function} — called with no arguments when the operator taps
 *                            "Continuar" and the kiosk should move to the
 *                            greet screen.
 *   onSkip      {Function} — called with no arguments when the user skips.
 *   onQuickEnd  {Function} — called (returns a Promise) when the operator
 *                            taps "Pausa" or "Fichar salida". Provided by the
 *                            kiosk patch; it replays the cached PIN through
 *                            the native onManualSelection() to check out.
 */
export class PcMesTargetSelector extends Component {
    static template = "pc_mes_kiosk.TargetSelector";
    static props = {
        employeeId: { type: Number },
        onDone: { type: Function },
        onSkip: { type: Function },
        onQuickEnd: { type: Function },
    };

    setup() {
        this.state = useState({
            loading: true,
            error: null,
            // Configuration flags returned by /pc_mes_kiosk/targets
            showProject: true,
            showTask: true,
            // Data
            projects: [],
            tasks: [],
            // Navigation
            selectedProjectId: null,
            saving: false,
            // Work screen shown after the target is confirmed (or skipped)
            confirmed: false,
            confirmedProjectName: "",
            confirmedTaskName: "",
            quickEndError: null,
        });
        this._loadTargets();
    }

    async _loadTargets() {
        try {
            const result = await rpc("/pc_mes_kiosk/targets", {});
            this.state.projects = result.projects || [];
            this.state.tasks = result.tasks || [];
            // Read config flags from response (backend must return them).
            // Fallback to true so the UI is usable even if the backend has not
            // yet been updated to return these fields.
            this.state.showProject =
                result.show_project !== undefined ? result.show_project : true;
            this.state.showTask =
                result.show_task !== undefined ? result.show_task : true;
        } catch (_err) {
            this.state.error = "No se pudieron cargar los proyectos. Inténtalo de nuevo.";
        } finally {
            this.state.loading = false;
        }
    }

    // ── Navigation ──────────────────────────────────────────────────────────

    /**
     * Called when the user taps a project button.
     * If tasks are shown, navigate to the task list; otherwise confirm directly.
     */
    onProjectTap(projectId) {
        if (this.state.showTask) {
            this.state.selectedProjectId = projectId;
        } else {
            this.confirmProject(projectId);
        }
    }

    /** Called when the user taps the "back" button in the task list. */
    backToProjects() {
        this.state.selectedProjectId = null;
    }

    /** Display name of the currently selected project. */
    get selectedProjectName() {
        if (!this.state.selectedProjectId) {
            return "";
        }
        const found = this.state.projects.find(
            (p) => p.id === this.state.selectedProjectId
        );
        return found ? found.name : "";
    }

    /** Tasks visible for the currently selected project. */
    get visibleTasks() {
        if (!this.state.selectedProjectId) {
            return [];
        }
        return this.state.tasks.filter(
            (t) => t.project_id === this.state.selectedProjectId
        );
    }

    /** Whether to show the project list (initial screen). */
    get showingProjects() {
        return this.state.showProject && this.state.selectedProjectId === null;
    }

    /** Whether to show the task list (after a project was tapped). */
    get showingTasks() {
        return (
            this.state.showProject &&
            this.state.showTask &&
            this.state.selectedProjectId !== null
        );
    }

    // ── Actions ─────────────────────────────────────────────────────────────

    /**
     * Confirm the selection.
     * @param {Number|null} projectId
     * @param {Number|null} taskId
     */
    async confirmSelection(projectId, taskId) {
        if (this.state.saving) {
            return;
        }
        this.state.saving = true;
        try {
            await rpc("/pc_mes_kiosk/set_target", {
                employee_id: this.props.employeeId,
                project_id: projectId || null,
                task_id: taskId || null,
            });
            this._showWorkScreen(projectId, taskId);
        } catch (_err) {
            this.state.saving = false;
            this.state.error = "No se pudo guardar la selección. Inténtalo de nuevo.";
        }
    }

    /** Confirm after selecting a task. */
    selectTask(taskId) {
        this.confirmSelection(this.state.selectedProjectId, taskId);
    }

    /**
     * Confirm with only a project (no task available or show_task is false).
     */
    confirmProject(projectId) {
        this.confirmSelection(projectId, null);
    }

    /**
     * Move to the "work screen": the imputation was saved (or skipped), and
     * the operator now sees the Pausa / Fichar salida controls, plus a
     * Continuar button to head back to the greet screen.
     */
    _showWorkScreen(projectId, taskId) {
        const project = this.state.projects.find((p) => p.id === projectId);
        const task = this.state.tasks.find((t) => t.id === taskId);
        this.state.confirmedProjectName = project ? project.name : "";
        this.state.confirmedTaskName = task ? task.name : "";
        this.state.saving = false;
        this.state.confirmed = true;
    }

    /** Skip target selection, but still show the work screen (Pausa /
     * Fichar salida must stay reachable even if no project/task was set). */
    skip() {
        this._showWorkScreen(null, null);
    }

    /** Tap on "Continuar": leave the work screen and go back to greet/idle. */
    continueToGreet() {
        this.props.onDone();
    }

    /**
     * Tap on "Pausa" or "Fichar salida": replay the cached PIN through the
     * native check-in/out toggle so the operator closes (or pauses) the
     * workday in a single tap, without leaving this screen or re-entering
     * their PIN on the main kiosk list.
     */
    async quickEnd() {
        if (this.state.saving) {
            return;
        }
        this.state.saving = true;
        this.state.quickEndError = null;
        try {
            await this.props.onQuickEnd();
            // On success the parent switches active_display away from
            // 'mes_target', so this component will be unmounted shortly.
        } catch (_err) {
            this.state.saving = false;
            this.state.quickEndError =
                "No se pudo registrar la salida. Inténtalo de nuevo.";
        }
    }
}
