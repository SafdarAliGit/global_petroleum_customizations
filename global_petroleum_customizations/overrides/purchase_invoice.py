import frappe
from frappe import _
from frappe.query_builder import DocType
from global_petroleum_customizations.overrides.global_petroleum_utils import validate_tank_lease_warehouse


def validate_warehouse(doc, method):
	if doc.update_stock:
		for item in doc.items:
			validate_tank_lease_warehouse(item.warehouse, item.item_code, doc.posting_date)


def validate_pro_items(doc, method):

	""" Validate that combination of custom_document_for_pro, custom_document_name_for_pro and item_code are unique for all Purchase Invoice and throw if not"""
	for item in doc.items:
		if not item.custom_document_for_pro or not item.custom_document_name_for_pro or not item.item_code:
			continue

		item_group = frappe.db.get_value("Item", item.item_code, "item_group")
		if frappe.db.get_value("Item Group", item_group, "custom_restrict_repeated_pro_item"):	
			existing_invoices = frappe.get_all(
				"Purchase Invoice Item",
				filters={
					"item_code": item.item_code,
					"custom_document_for_pro": item.custom_document_for_pro,
					"custom_document_name_for_pro": item.custom_document_name_for_pro,
					"docstatus": ["!=", 2],
					"parent": ["!=", doc.name]
				},
				fields=["parent"]
			)
			if existing_invoices:
				invoice_numbers = [frappe.get_desk_link("Purchase Invoice", invoice["parent"]) for invoice in existing_invoices]
				invoice_list_str = "<br>".join(invoice_numbers)

				frappe.throw(
					_("Purchase Invoice for {0} from {1} <br>Existing Purchase Invoices:<br>{2}")
					.format(frappe.get_desk_link("Item", item.item_code), frappe.get_desk_link(item.custom_document_for_pro, item.custom_document_name_for_pro), invoice_list_str)
				)


@frappe.whitelist()
def get_all_pro_items(pro_template):
	pro_items = frappe.db.get_all(
		"PRO Template Item",
		filters={
			"parenttype": "PRO Template",
			"parentfield": "pro_template_item",
			"parent": pro_template,
		},
		fields=["item"]
	)
	return pro_items