/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

/**
 * PcMesTargetSelector — tablet-friendly project/task picker shown inside the
 * attendance kiosk after check-in (or check-out, depending on configuration).
 *
 * Props:
 *   employeeId  {Number}  — id of the employee who just checked in/out.
 *   onDone      {Function} — called with no arguments when the selection is
 *                            saved and the kiosk should move to the greet screen.
 *   onSkip      {Function} — called with no arguments when the user skips.
 */
export class PcMesTargetSelector extends Component {
    static template = "pc_mes_kiosk.TargetSelector";
    static props = {
        employeeId: { type: Number },
        onDone: { type: Function },
        onSkip: { type: Function },
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
            this.state.error = "Could not load projects. Please try again.";
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
            this.props.onDone();
        } catch (_err) {
            this.state.saving = false;
            this.state.error = "Could not save selection. Please try again.";
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

    /** Skip target selection and proceed to greet screen. */
    skip() {
        this.props.onSkip();
    }
}
