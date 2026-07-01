/** @odoo-module **/
// Copyright 2026 Process Control (https://www.processcontrol.es)
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import { Component, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

/**
 * PcMesMrpScreen — tablet-friendly Manufacturing / Work Order screen shown
 * inside the attendance kiosk when the operator chooses the "Production" path.
 *
 * Navigation flow (≤3 taps per action):
 *   1. List of active manufacturing orders (MOs)
 *   2. Tap an MO → show its formula (BOM components + lot/expiry)
 *      and its open work orders
 *   3. Tap a work order → Weighing placeholder (TODO: real scale) + Confirm
 *      → start_workorder RPC → stop_workorder RPC on confirm → greet screen
 *
 * Props:
 *   employeeId  {Number}   — id of the employee who just clocked in/out.
 *   onDone      {Function} — called when the session ends (navigates to greet).
 *   onSkip      {Function} — called when the operator skips.
 */
export class PcMesMrpScreen extends Component {
    static template = "pc_mes_kiosk_mrp.MrpScreen";
    static props = {
        employeeId: { type: Number },
        onDone: { type: Function },
        onSkip: { type: Function },
    };

    setup() {
        this.state = useState({
            // ── Loading / error ──────────────────────────────────────────
            loading: true,
            error: null,
            // ── Step: "mo_list" | "mo_detail" | "wo_active" ─────────────
            step: "mo_list",
            // ── Data ────────────────────────────────────────────────────
            productions: [],         // list of MOs from /workorders
            selectedMo: null,        // full MO object (with workorders array)
            formula: [],             // components from /mo_formula
            formulaLoading: false,
            selectedWorkorder: null, // {id, name, state, workcenter}
            // ── Weighing placeholder ─────────────────────────────────────
            // TODO: integrate a real scale (barcode/serial comms). For now
            // we display a simulated weight so the UX flow is complete.
            simulatedWeight: null,
            // ── In-progress flags ────────────────────────────────────────
            starting: false,
            stopping: false,
            workorderStarted: false, // true once start_workorder returned ok
        });
        this._loadProductions();
    }

    // ── Data fetching ──────────────────────────────────────────────────────

    async _loadProductions() {
        try {
            const result = await rpc("/pc_mes_kiosk/workorders", {});
            this.state.productions = Array.isArray(result) ? result : [];
        } catch (_err) {
            this.state.error = "Could not load manufacturing orders. Please try again.";
        } finally {
            this.state.loading = false;
        }
    }

    async _loadFormula(productionId) {
        this.state.formulaLoading = true;
        this.state.formula = [];
        try {
            const result = await rpc("/pc_mes_kiosk/mo_formula", {
                production_id: productionId,
            });
            this.state.formula = Array.isArray(result) ? result : [];
        } catch (_err) {
            this.state.formula = [];
        } finally {
            this.state.formulaLoading = false;
        }
    }

    // ── Navigation helpers ─────────────────────────────────────────────────

    /** Tap on an MO card — go to MO detail (formula + workorder list). */
    async selectMo(mo) {
        this.state.selectedMo = mo;
        this.state.step = "mo_detail";
        this.state.selectedWorkorder = null;
        this.state.workorderStarted = false;
        this.state.simulatedWeight = null;
        await this._loadFormula(mo.id);
    }

    /** Back from MO detail to MO list. */
    backToMoList() {
        this.state.step = "mo_list";
        this.state.selectedMo = null;
        this.state.formula = [];
        this.state.selectedWorkorder = null;
        this.state.workorderStarted = false;
        this.state.simulatedWeight = null;
    }

    /** Tap on a work order button — move to the active-WO step. */
    selectWorkorder(wo) {
        this.state.selectedWorkorder = wo;
        this.state.step = "wo_active";
        this.state.workorderStarted = false;
        this.state.simulatedWeight = null;
    }

    /** Back from WO step to MO detail. */
    backToMoDetail() {
        this.state.step = "mo_detail";
        this.state.selectedWorkorder = null;
        this.state.workorderStarted = false;
        this.state.simulatedWeight = null;
    }

    // ── Weighing placeholder ───────────────────────────────────────────────

    /**
     * Simulate a scale reading.
     * TODO: Replace this with real hardware integration (USB/Bluetooth scale,
     * barcode-triggered weight read, or WebSerial API).  The real integration
     * will call a local bridge endpoint or use WebSerial to read from the scale
     * controller.
     */
    simulateWeighing() {
        // Generate a plausible random weight between 0.5 and 25 kg (demo only).
        const kg = (Math.random() * 24.5 + 0.5).toFixed(3);
        this.state.simulatedWeight = kg;
    }

    // ── Start / Stop workorder ─────────────────────────────────────────────

    /** Call start_workorder, then mark workorderStarted so the UI shows "Confirm". */
    async startWorkorder() {
        if (this.state.starting || !this.state.selectedWorkorder) {
            return;
        }
        this.state.starting = true;
        this.state.error = null;
        try {
            const result = await rpc("/pc_mes_kiosk/start_workorder", {
                employee_id: this.props.employeeId,
                workorder_id: this.state.selectedWorkorder.id,
            });
            if (result && result.ok) {
                this.state.workorderStarted = true;
            } else {
                this.state.error =
                    (result && result.error) || "Could not start work order.";
            }
        } catch (_err) {
            this.state.error = "Could not start work order. Please try again.";
        } finally {
            this.state.starting = false;
        }
    }

    /** Call stop_workorder, then call onDone to navigate to greet screen. */
    async finishWorkorder() {
        if (this.state.stopping || !this.state.selectedWorkorder) {
            return;
        }
        this.state.stopping = true;
        this.state.error = null;
        try {
            const result = await rpc("/pc_mes_kiosk/stop_workorder", {
                employee_id: this.props.employeeId,
                workorder_id: this.state.selectedWorkorder.id,
            });
            if (result && result.ok) {
                this.props.onDone();
            } else {
                this.state.error =
                    (result && result.error) || "Could not stop work order.";
                this.state.stopping = false;
            }
        } catch (_err) {
            this.state.error = "Could not stop work order. Please try again.";
            this.state.stopping = false;
        }
    }

    /** Skip the whole MRP flow and go straight to greet. */
    skip() {
        this.props.onSkip();
    }
}
