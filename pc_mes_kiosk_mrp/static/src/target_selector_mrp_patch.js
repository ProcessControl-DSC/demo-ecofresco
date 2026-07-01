/** @odoo-module **/
// Copyright 2026 Process Control (https://www.processcontrol.es)
// License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import { patch } from "@web/core/utils/patch";
import { PcMesTargetSelector } from "@pc_mes_kiosk/components/target_selector/target_selector";

/**
 * Patch PcMesTargetSelector to add an 'onGoToProduction' callback.
 *
 * The TargetSelector is rendered inside the kiosk app with a prop 'onDone'
 * and 'onSkip'.  We cannot add a new prop here without touching the parent
 * patch, so we use a simpler approach: the MRP "Production" button navigates
 * by reading the parent app's state directly via an event (custom DOM event)
 * that the kiosk patch listens to.
 *
 * Alternatively — and more cleanly for Owl — we fire a custom event that
 * bubbles up to the kiosk app root.  The kiosk app picks it up through a
 * __owl__ env listener defined in kiosk_mrp_patch.js.
 *
 * For simplicity we expose a dedicated method 'goToProduction' on the
 * TargetSelector that sets a flag, then calls props.onSkip (which goes to
 * 'greet').  We intercept the transition in the kiosk patch.
 *
 * Cleaner approach used here: the "Production" button dispatches a bubbling
 * CustomEvent 'pc-mes-go-mrp' on document.  The kiosk patch root element
 * listens and switches active_display to 'mes_mrp'.
 */
patch(PcMesTargetSelector.prototype, {
    /**
     * Navigate to the MRP screen.
     * Dispatches a bubbling CustomEvent so the kiosk app can intercept it.
     */
    goToProduction() {
        document.dispatchEvent(
            new CustomEvent("pc-mes-go-mrp", { bubbles: true, composed: true })
        );
    },
});
