// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt


frappe.ui.form.on("Tank Lease Contract", {
	refresh(frm) {
		erpnext.hide_company(frm);
		frm.set_query("cost_center", function () {
			return {
				filters: {
					is_group: 0,
				},
			};
		});

		frm.set_query("warehouse", function () {
			return {
				filters: {
					custom_is_tank_lease_warehouse: 1,
				},
			};
		});

		if (frm.doc.docstatus === 1)  {
			frm.add_custom_button(__("Create Purchase Invoice"), function () {
				frappe.model.open_mapped_doc({
					method: "global_petroleum_customizations.global_petroleum_customizations.doctype.tank_lease_contract.tank_lease_contract.create_purchase_invoice",
					frm: frm,
				});
			});
		}
	},
	tc_name: function (frm) {
		erpnext.utils.get_terms(frm.doc.tc_name, frm.doc, function (r) {
			if (!r.exc) {
				frm.set_value("terms", r.message);
			}
		});
	},

});
