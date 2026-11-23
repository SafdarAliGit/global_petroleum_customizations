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
	refresh: function (frm) {
		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__("Delivery Note"), function () {
				if (!frm.doc.supplier) {
					frappe.throw(__("Please select Supplier first"));
					return;
				}
				open_delivery_note_dialog(frm);
			}, __("Get Items From"));
		}
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

function open_delivery_note_dialog(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Get Items from Delivery Note"),
		size: "large",
		fields: [
			{
				fieldtype: "Date",
				fieldname: "from_date",
				label: __("From Posting Date"),
				onchange: () => load_delivery_notes(frm, dialog),
			},
			{ fieldtype: "Column Break" },
			{
				fieldtype: "Date",
				fieldname: "to_date",
				label: __("To Posting Date"),
				onchange: () => load_delivery_notes(frm, dialog),
			},
			{ fieldtype: "Section Break" },
			{
				fieldtype: "HTML",
				fieldname: "delivery_notes_html",
			},
		],
		primary_action_label: __("Get Items"),
		primary_action: function () {
			const $checked = dialog.$wrapper.find(".dn-row-check:checked");
			if (!$checked.length) {
				frappe.msgprint(__("Please select at least one Delivery Note"));
				return;
			}
			const selected = [];
			$checked.each(function () {
				selected.push({
					name: $(this).data("name"),
					cost_center: $(this).data("cost-center") || "",
				});
			});
			add_delivery_note_items(frm, selected);
			dialog.hide();
		},
	});

	load_delivery_notes(frm, dialog);
	dialog.show();
}

function load_delivery_notes(frm, dialog) {
	const from_date = dialog.get_value("from_date");
	const to_date = dialog.get_value("to_date");

	frappe.call({
		method: "global_petroleum_customizations.overrides.purchase_invoice.get_delivery_notes_for_transporter",
		args: {
			supplier: frm.doc.supplier,
			from_date: from_date || null,
			to_date: to_date || null,
		},
		callback: function (r) {
			render_delivery_notes(dialog, r.message || []);
		},
	});
}

function render_delivery_notes(dialog, rows) {
	const $html = dialog.fields_dict.delivery_notes_html.$wrapper;

	if (!rows.length) {
		$html.html(
			`<div class="text-muted text-center" style="padding:20px;">${__("No Delivery Notes found for this Supplier (transporter)")}</div>`
		);
		return;
	}

	let html = `
		<div style="max-height:400px; overflow-y:auto;">
		<table class="table table-bordered table-condensed">
			<thead>
				<tr>
					<th style="width:40px;"><input type="checkbox" class="dn-check-all"></th>
					<th>${__("Delivery Note")}</th>
					<th>${__("Posting Date")}</th>
					<th>${__("Cost Center")}</th>
				</tr>
			</thead>
			<tbody>
	`;

	rows.forEach(function (row) {
		const name = frappe.utils.escape_html(row.name || "");
		const cc = frappe.utils.escape_html(row.cost_center || "");
		const pd = row.posting_date ? frappe.datetime.str_to_user(row.posting_date) : "";
		html += `
			<tr>
				<td><input type="checkbox" class="dn-row-check"
					data-name="${name}" data-cost-center="${cc}"></td>
				<td>${name}</td>
				<td>${pd}</td>
				<td>${cc}</td>
			</tr>
		`;
	});

	html += "</tbody></table></div>";
	$html.html(html);

	$html.find(".dn-check-all").on("change", function () {
		const checked = this.checked;
		$html.find(".dn-row-check").prop("checked", checked);
	});
}

async function add_delivery_note_items(frm, selected) {
	frm.clear_table("items");

	for (const dn of selected) {
		const child = frm.add_child("items");
		child.item_code = "Transportation";
		await frm.script_manager.trigger("item_code", child.doctype, child.name);
		await frappe.model.set_value(child.doctype, child.name, "qty", 1);
		await frappe.model.set_value(child.doctype, child.name, "custom_document_for_pro", "Delivery Note");
		await frappe.model.set_value(child.doctype, child.name, "custom_document_name_for_pro", dn.name);
		if (dn.cost_center) {
			await frappe.model.set_value(child.doctype, child.name, "cost_center", dn.cost_center);
		}
	}

	frm.refresh_field("items");
}
