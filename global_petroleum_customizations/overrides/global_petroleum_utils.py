import frappe
from frappe import _
from frappe.utils import getdate

class StockTransferUtils:
	def calculate_weights(self):
		for item in self.items:
			item.custom_net_weight = item.custom_second_weight - item.custom_first_weight
			item.custom_net_weight_by_receiver =  item.custom_tare_weight_by_receiver - item.custom_gross_weight_by_receiver
			item.custom_net_weight_difference = item.custom_net_weight - item.custom_net_weight_by_receiver
		
			if item.custom_net_weight_by_receiver > 1 and item.custom_net_weight > item.custom_net_weight_by_receiver:
				item.qty = item.custom_net_weight_by_receiver
			else:
				item.qty = item.custom_net_weight


def make_stock_entry(item, doctype, docname, posting_date, posting_time):
	if not item.custom_wastage_account:
		frappe.throw(_("Please set Wastage Account in row# {}").format(item.idx))

	se = frappe.new_doc("Stock Entry")

	se.stock_entry_type = "Material Issue"
	se.posting_date = posting_date
	se.posting_time = posting_time
	se.set_posting_time = 1
	se.append("items", {
		"item_code": item.item_code,
		"qty": item.custom_net_weight_difference,
		"transfer_qty": item.custom_net_weight_difference,
		"uom": item.uom,
		"conversion_factor": item.conversion_factor,
		"s_warehouse": item.warehouse if doctype == "Delivery Note" else item.s_warehouse,
		"project": item.project,
		"cost_center": item.cost_center,
		"expense_account": item.custom_wastage_account,
        "use_serial_batch_fields":1 if item.batch_no else "",
        "batch_no": item.batch_no if item.batch_no else "",
	})
	se.save()
	se.submit()
	se.add_comment("Comment", _("Adjusting stock for {0} {1}").format(doctype, docname))

	return se


def validate_tank_lease_warehouse(warehouse, item_code, transaction_date):
	warehouse = frappe.get_doc("Warehouse", warehouse)
	# if warehouse.custom_is_tank_lease_warehouse and getdate(transaction_date) > warehouse.custom_booking_date:
	# 	if warehouse.custom_tank_lease_contract and warehouse.custom_base_oil_item and warehouse.custom_base_oil_item != item_code:
	# 		frappe.throw(_("Warehouse Booked for {0}, cannot move {1} to this warehouse").format(warehouse.custom_base_oil_item, item_code))

	# 	if warehouse.custom_status == "Expired":
	# 		frappe.throw(_("Warehouse is Expired, cannot move {0} to this warehouse").format(item_code))

	# 	if warehouse.disabled:
	# 		frappe.throw(_("Warehouse is Disabled, cannot move {0} to this warehouse").format(item_code))