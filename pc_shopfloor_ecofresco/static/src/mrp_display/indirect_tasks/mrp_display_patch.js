import { patch } from "@web/core/utils/patch";
import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";
import { IndirectTaskDialog } from "./indirect_task_dialog";

/**
 * Adds the "Tareas indirectas" entry point to the Shop Floor control panel:
 * opens IndirectTaskDialog, which lets the operator imputate time to
 * indirect project tasks (cleaning, warehouse...) without leaving Shop
 * Floor. See mrp_display_patch.xml for the button itself.
 */
patch(MrpDisplay.prototype, {
    pcOpenIndirectTaskDialog() {
        this.dialogService.add(IndirectTaskDialog, {});
    },
});
