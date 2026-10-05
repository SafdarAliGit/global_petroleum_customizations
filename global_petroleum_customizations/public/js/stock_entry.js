// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.ui.form.on("Stock Entry Detail", {
	custom_first_weight: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "custom_gross_weight_by_receiver", row.custom_first_weight);
		frm.trigger("calculate_weights", cdt, cdn);
	},
	custom_second_weight: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "custom_tare_weight_by_receiver", row.custom_second_weight);
		frm.trigger("calculate_weights", cdt, cdn);
	},
	custom_gross_weight_by_receiver: function (frm, cdt, cdn) {
		frm.trigger("calculate_weights", cdt, cdn);
	},
	custom_tare_weight_by_receiver: function (frm, cdt, cdn) {
		frm.trigger("calculate_weights", cdt, cdn);
	},
	calculate_weights: function (frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "custom_net_weight", flt(row.custom_second_weight) - flt(row.custom_first_weight));
		frappe.model.set_value(cdt, cdn, "custom_net_weight_by_receiver", flt(row.custom_tare_weight_by_receiver) - flt(row.custom_gross_weight_by_receiver));
		frappe.model.set_value(cdt, cdn, "custom_net_weight_difference", flt(row.custom_net_weight) - flt(row.custom_net_weight_by_receiver));

		if (row.custom_net_weight_by_receiver > 1 && row.custom_net_weight > row.custom_net_weight_by_receiver) {
			frappe.model.set_value(cdt, cdn, "qty", flt(row.custom_net_weight_by_receiver));
		} else {
			frappe.model.set_value(cdt, cdn, "qty", flt(row.custom_net_weight));
		}
	}
});

