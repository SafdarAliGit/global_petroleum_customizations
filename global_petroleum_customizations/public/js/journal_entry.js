// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on("Journal Entry", {
    refresh(frm) {
        frm.set_query("cost_center", "accounts", () => {
            return {
                filters: {
                    custom_is_active: 1
                }
            };
        });
    }
});
