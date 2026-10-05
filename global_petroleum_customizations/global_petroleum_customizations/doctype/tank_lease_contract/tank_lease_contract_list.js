// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.listview_settings['Tank Lease Contract'] = {
	add_fields: ["supplier", "company"],
	onload: function(listview) {
		listview.page.add_inner_button(__('Create Purchase Invoice'), function() {
			const selected = listview.get_checked_items();

			if (!selected.length) {
				frappe.msgprint("Select at least one Tank Lease Contract.");
				return;
			}

			const docnames = selected.map(row => row.name);
			frappe.call({
				method: "global_petroleum_customizations.global_petroleum_customizations.doctype.tank_lease_contract.tank_lease_contract.create_purchase_invoice_for_multiple_tlc",
				args: {
					docnames: JSON.stringify(docnames)
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.sync(r.message);
						frappe.set_route("Form", r.message.doctype, r.message.name);
					}
				}
			});
		});
	}
};
