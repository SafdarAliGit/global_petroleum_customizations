import frappe
from frappe import _
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from global_petroleum_customizations.overrides.global_petroleum_utils import StockTransferUtils, validate_tank_lease_warehouse


class CustomStockEntry(StockEntry, StockTransferUtils):
	def validate(self):
		self.validate_warehouse()
		if self.stock_entry_type == "Material Transfer":
			self.calculate_weights()
			self.set_actual_qty_and_stock_adjustement()
		super().validate()

	def set_actual_qty_and_stock_adjustement(self):
		for item in self.items:
			# if item.custom_net_weight_by_receiver and item.custom_net_weight > item.custom_net_weight_by_receiver:
				item.custom_net_weight_difference = item.custom_net_weight - item.custom_net_weight_by_receiver
				item.qty = item.custom_net_weight_by_receiver
				if self.get("_action") and self._action == "submit" and item.custom_net_weight_difference != 0:
					stock_entry = make_stock_entry(item, self.doctype, self.name, self.posting_date, self.posting_time)
					if stock_entry:
						self.add_comment("Comment", _("Adjusting stock through Stock Entry {0} for Stock Entry {1}").format(stock_entry, self.name))

	def validate_warehouse(self):
		for item in self.items:
			if self.stock_entry_type in ["Material Receipt", "Material Transfer"]:
				validate_tank_lease_warehouse(item.t_warehouse, item.item_code, self.posting_date)


def make_stock_entry(item, doctype, docname, posting_date, posting_time):
	if not item.custom_wastage_account:
		frappe.throw(_("Please set Wastage Account in row# {}").format(item.idx))

	se = frappe.new_doc("Stock Entry")

	if item.custom_net_weight_difference < 0:
		stock_entry_type = "Material Receipt"
		transfer_qty = -item.custom_net_weight_difference

	elif item.custom_net_weight_difference > 0:
		stock_entry_type = "Material Issue"
		transfer_qty = item.custom_net_weight_difference

	else:
		return

	se.stock_entry_type = stock_entry_type
	
	se.posting_date = posting_date
	se.posting_time = posting_time
	se.set_posting_time = 1
	se.custom_adjustment_stock_entry = docname
	se.append("items", {
		"item_code": item.item_code,
		"qty": transfer_qty,
		"transfer_qty": transfer_qty,
		"uom": item.uom,
		"conversion_factor": item.conversion_factor,
		"s_warehouse": item.s_warehouse if stock_entry_type == "Material Issue" else "",
		"t_warehouse": item.s_warehouse if stock_entry_type == "Material Receipt" else "",
		"project": item.project,
		"cost_center": item.cost_center,
		"expense_account": item.custom_wastage_account,
		"use_serial_batch_fields":1 if item.batch_no else "",
		"batch_no": item.batch_no if item.batch_no else "",
	})
	se.save()
	se.submit()
	se.add_comment("Comment", _("Adjusting stock for {0} {1}").format(doctype, docname))

	return se.name