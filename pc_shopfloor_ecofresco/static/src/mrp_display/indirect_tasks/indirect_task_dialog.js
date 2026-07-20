import { _t } from "@web/core/l10n/translation";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onWillUnmount, useState } from "@odoo/owl";

/**
 * "Tareas indirectas" dialog for the Shop Floor app (mrp_display).
 *
 * Two steps:
 * - "select": lists the open tasks of projects flagged
 *   ``pc_shopfloor_indirect_task`` (e.g. Limpieza, Almacén) for the
 *   operator to pick from.
 * - "running": a live HH:MM:SS chronometer for the chosen task, with
 *   "Finalizar" (creates the timesheet server-side) and "Cancelar"
 *   (discards the elapsed time, back to the task list).
 */
export class IndirectTaskDialog extends Component {
    static template = "pc_shopfloor_ecofresco.IndirectTaskDialog";
    static components = { Dialog };
    static props = {
        close: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            step: "select",
            tasks: [],
            loading: true,
            task: null,
            elapsedSeconds: 0,
            saving: false,
        });
        this.startTime = null;
        this.timer = null;

        onWillStart(async () => {
            this.state.tasks = await this.orm.call(
                "project.task",
                "pc_shopfloor_get_indirect_tasks",
                [[]]
            );
            this.state.loading = false;
        });

        onWillUnmount(() => this._stopTimer());
    }

    _startTimer() {
        this.startTime = Date.now();
        this.state.elapsedSeconds = 0;
        this.timer = browser.setInterval(() => {
            this.state.elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000);
        }, 1000);
    }

    _stopTimer() {
        if (this.timer) {
            browser.clearInterval(this.timer);
            this.timer = null;
        }
    }

    get formattedElapsed() {
        const total = this.state.elapsedSeconds;
        const h = String(Math.floor(total / 3600)).padStart(2, "0");
        const m = String(Math.floor((total % 3600) / 60)).padStart(2, "0");
        const s = String(total % 60).padStart(2, "0");
        return `${h}:${m}:${s}`;
    }

    selectTask(task) {
        this.state.task = task;
        this.state.step = "running";
        this._startTimer();
    }

    cancel() {
        this._stopTimer();
        this.state.step = "select";
        this.state.task = null;
        this.state.elapsedSeconds = 0;
    }

    async finish() {
        if (this.state.saving) {
            return;
        }
        this._stopTimer();
        this.state.saving = true;
        try {
            await this.orm.call(
                "account.analytic.line",
                "pc_shopfloor_create_indirect_timesheet",
                [[], this.state.task.id, this.state.elapsedSeconds]
            );
            this.notification.add(_t("Tiempo imputado"), { type: "success" });
            this.props.close();
        } catch (error) {
            this.state.saving = false;
            const message =
                (error && error.data && error.data.message) ||
                _t("No se ha podido imputar el tiempo.");
            this.notification.add(message, { type: "danger" });
            this.state.step = "select";
            this.state.task = null;
            this.state.elapsedSeconds = 0;
        }
    }
}
