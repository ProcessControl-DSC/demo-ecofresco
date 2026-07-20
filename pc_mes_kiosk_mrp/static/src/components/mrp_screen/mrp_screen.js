/** @odoo-module **/
// Copyright 2026 Process Control (https://www.processcontrol.es)
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import { Component, useExternalListener, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";

// A keyboard-wedge barcode scanner emits each digit of the EAN as a fast
// burst of keydown events, normally terminated by "Enter". A human never
// types this fast, so any gap longer than SCAN_GAP_MS between two keydowns
// resets the buffer — this tells scanner input apart from stray keystrokes
// without needing a dedicated focused input field.
const SCAN_GAP_MS = 100;
const EAN13_LENGTH = 13;

/**
 * PcMesMrpScreen — tablet-friendly Manufacturing / Work Order screen shown
 * inside the attendance kiosk when the operator chooses the "Production" path.
 *
 * Navigation flow (≤3 taps per action):
 *   1. List of active manufacturing orders (MOs)
 *   2. Tap an MO → show its formula (BOM components + lot/expiry)
 *      and its open work orders. Each component can be weighed individually
 *      (simulated reading, registered on its stock.move.line with lot/
 *      traceability via register_weighing).
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
            weighingProductId: null, // product_id currently being weighed
            selectedWorkorder: null, // {id, name, state, workcenter}
            // ── Barcode scanner (scan-to-weigh) ──────────────────────────
            scannedProductId: null,  // product_id just matched — for the
                                      // brief highlight animation on its row
            scanError: null,         // e.g. "Unknown barcode: 123..."
            // ── Weighing placeholder ─────────────────────────────────────
            // TODO: integrate a real scale (barcode/serial comms). For now
            // we display a simulated weight so the UX flow is complete.
            simulatedWeight: null,
            // ── In-progress flags ────────────────────────────────────────
            starting: false,
            stopping: false,
            workorderStarted: false, // true once start_workorder returned ok
        });

        // Internal (non-reactive) scanner buffer — see _onScannerKeydown().
        this._scanBuffer = "";
        this._lastScanKeyTime = 0;
        this._scanHighlightTimer = null;
        this._scanErrorTimer = null;
        useExternalListener(window, "keydown", (ev) => this._onScannerKeydown(ev));

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

    /**
     * Weigh one BOM component and register the result on its stock.move.line.
     *
     * The weight itself is still simulated (no physical scale — see
     * simulateWeighing() below), but the outcome is now really recorded on
     * the component's move line via register_weighing(), with lot
     * assignment/creation when the product is tracked, so the manufacturing
     * order keeps traceability of what was actually consumed.
     */
    async weighComponent(comp) {
        if (this.state.weighingProductId || !comp.product_id) {
            return;
        }
        this.state.weighingProductId = comp.product_id;
        this.state.error = null;
        // Simulate a plausible reading close to the theoretical BOM quantity
        // (±3%), rounded to 3 decimals. TODO: replace with a real scale
        // reading (see simulateWeighing() for hardware integration options).
        const jitter = 1 + (Math.random() * 0.06 - 0.03);
        const simulatedQty = Number((Math.max(0, comp.qty * jitter)).toFixed(3));
        try {
            const result = await rpc("/pc_mes_kiosk/register_weighing", {
                production_id: this.state.selectedMo.id,
                product_id: comp.product_id,
                qty: simulatedQty,
            });
            if (result && result.ok) {
                comp.weighed_qty = result.recorded_qty;
                if (result.lot) {
                    comp.lot = result.lot;
                }
            } else {
                this.state.error =
                    (result && result.error) || "Could not register the weighing.";
            }
        } catch (_err) {
            this.state.error = "Could not register the weighing. Please try again.";
        } finally {
            this.state.weighingProductId = null;
        }
    }

    // ── Barcode scanner (scan component → weigh it) ─────────────────────────

    /**
     * Global keydown listener that recognizes a barcode-scanner "keyboard"
     * burst: a USB/Bluetooth HID scanner types the EAN digits and then
     * Enter, all within a few milliseconds — far faster than a human could
     * type. We buffer digits and flush (process) the buffer as soon as
     * either:
     *   - it reaches EAN13_LENGTH (13 digits), since every component
     *     barcode in this screen is an EAN13, or
     *   - an "Enter" arrives (some scanners are configured for shorter
     *     codes / a trailing terminator).
     * Any gap longer than SCAN_GAP_MS between two keydowns resets the
     * buffer, so normal keyboard/touch use elsewhere never gets
     * misinterpreted as a scan.
     */
    _onScannerKeydown(ev) {
        // Only listen while the formula (BOM components) is on screen.
        if (this.state.step !== "mo_detail" || this.state.formulaLoading) {
            return;
        }

        const now = Date.now();
        if (now - this._lastScanKeyTime > SCAN_GAP_MS) {
            this._scanBuffer = "";
        }
        this._lastScanKeyTime = now;

        if (ev.key >= "0" && ev.key <= "9") {
            this._scanBuffer += ev.key;
            if (this._scanBuffer.length >= EAN13_LENGTH) {
                this._processScannedBarcode(this._scanBuffer);
                this._scanBuffer = "";
            }
            return;
        }

        if (ev.key === "Enter" && this._scanBuffer) {
            this._processScannedBarcode(this._scanBuffer);
            this._scanBuffer = "";
        }
    }

    /**
     * Match a scanned barcode against the pending (not-yet-weighed)
     * components of the current formula and trigger its weighing via the
     * existing register_weighing flow (weighComponent), with a brief
     * highlight on the matched row for operator feedback.
     */
    _processScannedBarcode(barcode) {
        const comp = this.state.formula.find(
            (c) => c.barcode && c.barcode === barcode && !c.weighed_qty
        );
        if (!comp) {
            this._flashScanError(`Unknown or already-weighed barcode: ${barcode}`);
            return;
        }

        clearTimeout(this._scanHighlightTimer);
        this.state.scanError = null;
        this.state.scannedProductId = comp.product_id;
        this._scanHighlightTimer = setTimeout(() => {
            this.state.scannedProductId = null;
        }, 1500);

        this.weighComponent(comp);
    }

    /** Show a transient error banner for an unrecognized scan. */
    _flashScanError(message) {
        clearTimeout(this._scanErrorTimer);
        this.state.scanError = message;
        this._scanErrorTimer = setTimeout(() => {
            this.state.scanError = null;
        }, 2500);
    }

    // ── Navigation helpers ─────────────────────────────────────────────────

    /** Tap on an MO card — go to MO detail (formula + workorder list). */
    async selectMo(mo) {
        this.state.selectedMo = mo;
        this.state.step = "mo_detail";
        this.state.selectedWorkorder = null;
        this.state.workorderStarted = false;
        this.state.simulatedWeight = null;
        this.state.weighingProductId = null;
        this.state.scannedProductId = null;
        this.state.scanError = null;
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
        this.state.weighingProductId = null;
        this.state.scannedProductId = null;
        this.state.scanError = null;
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
