// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on("Purchase Invoice", {
	setup: function (frm) {
		frm.set_query("custom_document_name_for_pro", "items", () => {
			return {
				filters: {
					docstatus: 1
				},
			};
		});
	},
	custom_document_for_pro: function (frm) {
		if (!frm.doc.custom_document_for_pro) {
			frm.set_value("custom_document_name_for_pro", "");
		}
	},
	custom_pro_template: function (frm) {
		frappe.call({
			method: "global_petroleum_customizations.overrides.purchase_invoice.get_all_pro_items",
			args: { pro_template: frm.doc.custom_pro_template },

			callback: function (r) {
				if (r.message.length > 0) {
					frm.clear_table("items");
					r.message.forEach(function (row) {
						var child = frm.add_child("items");
						child.item_code = row.item;
						frm.script_manager.trigger("item_code", child.doctype, child.name);
					});
					frm.refresh_field("items");
				}
			},
		});
	},
});

frappe.ui.form.on("Purchase Invoice Item", {
	custom_document_name_for_pro: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		
		if (row.custom_document_for_pro && row.custom_document_name_for_pro) {
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: row.custom_document_for_pro,
					filters: {
						name: row.custom_document_name_for_pro
					},
					fieldname: ["cost_center"]
				},
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, "cost_center", r.message.cost_center);
					}
				}
			});
		}
	}
});