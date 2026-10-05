import frappe
from frappe import _
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote
from frappe.utils import flt


class CustomDeliveryNote(DeliveryNote):
	def validate(self):
		self.calculate_weights()
		self.set_actual_qty_and_stock_adjustement()
		super(CustomDeliveryNote, self).validate()

	def set_actual_qty_and_stock_adjustement(self):
		for item in self.items:
			# if item.custom_net_weight_by_receiver and item.custom_net_weight > item.custom_net_weight_by_receiver:
					if item.custom_stock_adjustment_entry_by == "Average Weight":
						item.custom_net_weight_difference = flt(item.custom_net_weight, 2) - flt(item.custom_average_weight, 2)
					elif item.custom_stock_adjustment_entry_by == "Receiver Weight":
						item.custom_net_weight_difference = flt(item.custom_net_weight, 2) - flt(item.custom_net_weight_by_receiver, 2)
					if self.get("_action") and self._action == "submit":
						stock_entry = make_stock_entry(item, self.doctype, self.name, self.posting_date, self.posting_time)
						if stock_entry:
							self.add_comment("Comment", _("Adjusting stock through Stock Entry {0} for Delivery Note {1}").format(stock_entry, self.name))

	def calculate_weights(self):
		for item in self.items:
			item.custom_net_weight = item.custom_second_weight - item.custom_first_weight
			item.custom_net_weight_by_receiver =  item.custom_tare_weight_by_receiver - item.custom_gross_weight_by_receiver
			
			
			if item.custom_stock_adjustment_entry_by == "Average Weight":
				item.qty = item.custom_average_weight
			elif item.custom_stock_adjustment_entry_by == "Receiver Weight":
				item.qty = item.custom_net_weight_by_receiver
			elif item.custom_stock_adjustment_entry_by == "Delivered Quantity":
				item.qty = item.custom_net_weight

			if self.is_return:
				item.qty = -item.qty
		
			# if item.custom_net_weight_by_receiver > 1 and item.custom_net_weight > item.custom_net_weight_by_receiver:
			# 	if item.custom_stock_adjustment_entry_by == "Average Weight":
			# 		item.qty = item.custom_average_weight
			# 	elif item.custom_stock_adjustment_entry_by == "Receiver Weight":
			# 		item.qty = item.custom_net_weight_by_receiver
			# else:
			# 	item.qty = item.custom_net_weight



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
	se.custom_delivery_note = docname
	se.append("items", {
		"item_code": item.item_code,
		"qty": transfer_qty,
		"transfer_qty": transfer_qty,
		"uom": item.uom,
		"conversion_factor": item.conversion_factor,
		"s_warehouse": item.warehouse if stock_entry_type == "Material Issue" else "",
		"t_warehouse": item.warehouse if stock_entry_type == "Material Receipt" else "",
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