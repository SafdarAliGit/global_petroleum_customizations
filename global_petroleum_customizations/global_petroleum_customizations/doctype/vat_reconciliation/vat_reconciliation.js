// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on("VAT Reconciliation", {
	refresh(frm) {
		erpnext.hide_company(frm);
	},
});
