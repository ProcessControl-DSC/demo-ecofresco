/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { PcMesTargetSelector } from "./components/target_selector/target_selector";

// Import the kiosk app component so we can patch it.
// The named export is the default export object; we use the named class.
import kioskAppDefault from "@hr_attendance/public_kiosk/public_kiosk_app";

const { kioskAttendanceApp } = kioskAppDefault;

// Register PcMesTargetSelector as a sub-component so the patched template
// can use it as <PcMesTargetSelector/>.
kioskAttendanceApp.components.PcMesTargetSelector = PcMesTargetSelector;

patch(kioskAttendanceApp.prototype, {
    /**
     * Override onManualSelection to intercept the result of check-in/check-out
     * and show the MES target selector when the mode requires it.
     *
     * - mode 'on_checkin':  show selector after a check-IN (attendance.check_out is falsy)
     * - mode 'on_checkout': show selector after a check-OUT (attendance.check_out is truthy)
     *
     * The mode is carried in this._pcMesMode, set during setup via _pcMesLoadConfig.
     * If the endpoint has not yet been updated to return 'mode', we default to 'on_checkin'.
     */
    setup() {
        super.setup();
        this._pcMesMode = "on_checkin"; // default; overwritten by _pcMesLoadConfig
        this._pcMesLoadConfig();
    },

    /**
     * Fetch mode (and show_project/show_task) from /pc_mes_kiosk/targets.
     * We call targets here just to obtain the config flags; the selector
     * component will call it again to get the actual data — acceptable since
     * targets is a cheap read endpoint.
     *
     * NOTA: el endpoint /pc_mes_kiosk/targets DEBE devolver también los campos
     * 'mode', 'show_project' y 'show_task' para que este patch pueda decidir
     * cuándo mostrar la pantalla. Ver sección AJUSTE BACKEND NECESARIO.
     */
    async _pcMesLoadConfig() {
        try {
            const result = await rpc("/pc_mes_kiosk/targets", {});
            if (result && result.mode) {
                this._pcMesMode = result.mode;
            }
        } catch (_e) {
            // Non-blocking: if config cannot be loaded, default to on_checkin.
        }
    },

    /**
     * Intercept the attendance result and decide whether to show the target
     * selector before navigating to the greet screen.
     */
    async onManualSelection(employeeId, enteredPin) {
        // Call the original implementation to perform the actual check-in/out RPC.
        await super.onManualSelection(employeeId, enteredPin);

        // If the RPC failed the original method stays on the current screen
        // (it calls displayNotification and does NOT call switchDisplay('greet')).
        // We detect a successful attendance by checking that employeeData was set
        // and that active_display is now 'greet'.
        if (this.state.active_display !== "greet") {
            return;
        }

        // Cache employee id + PIN for the lifetime of this kiosk session so the
        // "Pausa" / "Fichar salida" quick actions on the MES work screen can
        // replay the same toggle (check-in <-> check-out) without asking the
        // operator to re-enter their PIN. Cached regardless of whether the
        // target selector is shown below, so the quick action is always usable.
        this._pcMesEmployeeId = employeeId;
        this._pcMesPin = enteredPin;

        const attendance = this.employeeData && this.employeeData.attendance;
        const isCheckIn = attendance && !attendance.check_out;
        const isCheckOut = attendance && !!attendance.check_out;

        const shouldShow =
            (this._pcMesMode === "on_checkin" && isCheckIn) ||
            (this._pcMesMode === "on_checkout" && isCheckOut);

        if (shouldShow) {
            // Navigate to the MES target selector instead of greet.
            this.state.active_display = "mes_target";
        }
    },

    /**
     * Called from the MES target selector's "Pausa" / "Fichar salida"
     * buttons. Replays the cached employee id + PIN through the same
     * onManualSelection() toggle used by the kiosk's own PIN screen: since
     * the attendance is currently open, this performs a check-out (native
     * hr_attendance behaviour — there is no separate "break" state, a pause
     * IS a check-out; the operator resumes later with a normal check-in).
     *
     * On success this.state.active_display moves to 'greet' (or back to
     * 'mes_target' if the module is configured to ask for the project/task
     * on check-out instead of check-in), so the work screen unmounts itself.
     */
    async _pcMesQuickEnd() {
        if (!this._pcMesEmployeeId) {
            return;
        }
        await this.onManualSelection(this._pcMesEmployeeId, this._pcMesPin);
    },
});
