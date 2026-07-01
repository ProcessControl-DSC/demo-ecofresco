/** @odoo-module **/
// Copyright 2026 Process Control (https://www.processcontrol.es)
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import { onWillUnmount } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { PcMesMrpScreen } from "./components/mrp_screen/mrp_screen";

// Import the kiosk app component from the native module.
import kioskAppDefault from "@hr_attendance/public_kiosk/public_kiosk_app";

const { kioskAttendanceApp } = kioskAppDefault;

// Register PcMesMrpScreen so the patched template can use it as <PcMesMrpScreen/>.
kioskAttendanceApp.components.PcMesMrpScreen = PcMesMrpScreen;

patch(kioskAttendanceApp.prototype, {
    /**
     * Extend setup: read show_workorder flag and listen for the
     * 'pc-mes-go-mrp' custom event dispatched by the TargetSelector
     * Production button (see target_selector_mrp_patch.js).
     */
    setup() {
        super.setup();
        this._pcMesShowWorkorder = false;
        this._pcMesMrpLoadConfig();

        // Bind the document-level listener.  Using Owl's onWillUnmount
        // ensures it is removed when the kiosk app component unmounts.
        const handler = (evt) => this._pcMesOnGoMrp(evt);
        document.addEventListener("pc-mes-go-mrp", handler);
        onWillUnmount(() => document.removeEventListener("pc-mes-go-mrp", handler));
    },

    /**
     * Handle the 'pc-mes-go-mrp' custom event: switch to the MRP screen.
     * _pcMesEmployeeId was already stored by the base kiosk patch
     * (pc_mes_kiosk/static/src/kiosk_patch.js) when onManualSelection ran.
     */
    _pcMesOnGoMrp(_evt) {
        if (this._pcMesShowWorkorder) {
            this.state.active_display = "mes_mrp";
        }
        // If show_workorder is false the Production button should not have
        // appeared; this is a no-op safety guard.
    },

    /**
     * Read show_workorder from /pc_mes_kiosk/targets (the MRP controller
     * override appends this flag to the base response).
     */
    async _pcMesMrpLoadConfig() {
        try {
            const result = await rpc("/pc_mes_kiosk/targets", {});
            if (result && result.show_workorder !== undefined) {
                this._pcMesShowWorkorder = !!result.show_workorder;
            }
        } catch (_e) {
            // Non-blocking: if the call fails the MRP path remains hidden.
        }
    },
});
