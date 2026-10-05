# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt


import frappe
from frappe import _
from frappe.utils import add_to_date, cint, flt, get_datetime, get_table_name, getdate
from frappe.utils.deprecations import deprecated
from pypika import functions as fn

from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter

SLE_COUNT_LIMIT = 10_000


def _estimate_table_row_count(doctype: str):
	table = get_table_name(doctype)
	return cint(
		frappe.db.sql(
			f"""select table_rows
			from  information_schema.tables
			where table_name = '{table}' ;"""
		)[0][0]
	)


def execute(filters=None):
	if not filters:
		filters = {}

	sle_count = _estimate_table_row_count("Stock Ledger Entry")

	if (
		sle_count > SLE_COUNT_LIMIT
		and not filters.get("item_code")
		and not filters.get("warehouse")
	):
		frappe.throw(
			_("Please select either the Item or Warehouse or Warehouse Type filter to generate the report.")
		)

	if filters.from_date > filters.to_date:
		frappe.throw(_("From Date must be before To Date"))

	float_precision = cint(frappe.db.get_default("float_precision")) or 3

	columns = get_columns()
	item_map = get_item_details(filters)
	iwb_map = get_item_warehouse_batch_map(filters, float_precision)

	data = []
	for item in sorted(iwb_map):
		if not filters.get("item") or filters.get("item") == item:
			for wh in sorted(iwb_map[item]):
				for batch in sorted(iwb_map[item][wh]):
					qty_dict = iwb_map[item][wh][batch]
					if (qty_dict.opening_qty or qty_dict.in_qty or qty_dict.out_qty or qty_dict.bal_qty):
						# Only include rows with non-zero balance_qty if hide_zero_balance is checked
						if not filters.get("hide_zero_balance") or qty_dict.bal_qty != 0:
							balance_amt = flt(qty_dict.bal_qty * (qty_dict.opening_rate or qty_dict.in_rate), float_precision)
							data.append(
								{
									"item": item,
									"item_name": item_map[item]["item_name"],
									"description": item_map[item]["description"],
									"warehouse": wh,
									"batch": batch,
									"opening_qty": flt(qty_dict.opening_qty, float_precision),
									"opening_rate": flt(qty_dict.opening_rate, float_precision),
									"opening_amt": flt(qty_dict.opening_amt, float_precision),
									"in_qty": flt(qty_dict.in_qty, float_precision),
									"in_rate": flt(qty_dict.in_rate, float_precision),
									"in_amt": flt(qty_dict.in_qty * qty_dict.in_rate, float_precision),
									"out_qty": flt(qty_dict.out_qty, float_precision),
									"out_rate": flt(qty_dict.out_rate, float_precision),
									"out_amt": flt(qty_dict.out_qty * qty_dict.out_rate, float_precision),
									"balance_qty": flt(qty_dict.bal_qty, float_precision),
									"balance_rate": flt(balance_amt / qty_dict.bal_qty, float_precision) if qty_dict.bal_qty else 0,
									"balance_amt": balance_amt,
									"uom": item_map[item]["stock_uom"],
								}
							)

	return columns, data


def get_columns():
	columns = [
		{"label": _("Item"), "fieldname": "item", "fieldtype": "Link", "options": "Item", "width": 135},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 135},
		{"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 135},
		{"label": _("Warehouse"), "fieldname": "warehouse", "fieldtype": "Link", "options": "Warehouse", "width": 160},
		{"label": _("Batch"), "fieldname": "batch", "fieldtype": "Link", "options": "Batch", "width": 90},
		{"label": _("Opening Qty"), "fieldname": "opening_qty", "fieldtype": "Float", "width": 160},
		{"label": _("Opening Rate"), "fieldname": "opening_rate", "fieldtype": "Float", "width": 160},
		{"label": _("Opening Amount"), "fieldname": "opening_amt", "fieldtype": "Float", "width": 180},
		{"label": _("Purchase Qty"), "fieldname": "in_qty", "fieldtype": "Float", "width": 160},
		{"label": _("Purchase Rate"), "fieldname": "in_rate", "fieldtype": "Float", "width": 160},
		{"label": _("Purchase Amount"), "fieldname": "in_amt", "fieldtype": "Float", "width": 180},
		{"label": _("Delivery Qty"), "fieldname": "out_qty", "fieldtype": "Float", "width": 160},
		{"label": _("Delivery Rate"), "fieldname": "out_rate", "fieldtype": "Float", "width": 160},
		{"label": _("Delivery Amount"), "fieldname": "out_amt", "fieldtype": "Float", "width": 180},
		{"label": _("Balance Qty"), "fieldname": "balance_qty", "fieldtype": "Float", "width": 160},
		{"label": _("Balance Rate"), "fieldname": "balance_rate", "fieldtype": "Float", "width": 160},
		{"label": _("Balance Amount"), "fieldname": "balance_amt", "fieldtype": "Float", "width": 180},
		{"label": _("UOM"), "fieldname": "uom", "fieldtype": "Data", "width": 90},
	]

	return columns


def get_stock_ledger_entries(filters):
	entries = get_stock_ledger_entries_for_batch_no(filters)

	entries += get_stock_ledger_entries_for_batch_bundle(filters)
	return entries


@deprecated
def get_stock_ledger_entries_for_batch_no(filters):
	"""Get stock ledger entries for batch_no field with rate information"""
	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))
	if not filters.get("to_date"):
		frappe.throw(_("'To Date' is required"))

	posting_datetime = get_datetime(add_to_date(filters["to_date"], days=1))

	sle = frappe.qb.DocType("Stock Ledger Entry")
	query = (
		frappe.qb.from_(sle)
		.select(
			sle.item_code,
			sle.warehouse,
			sle.batch_no,
			sle.posting_date,
			sle.actual_qty,
			sle.incoming_rate,
			sle.outgoing_rate,
			sle.valuation_rate,
			sle.stock_value_difference,
			sle.voucher_type,
			sle.voucher_no
		)
		.where(
			(sle.docstatus < 2)
			& (sle.is_cancelled == 0)
			& (sle.batch_no != "")
			& (sle.posting_datetime < posting_datetime)
		)
		.orderby(sle.item_code, sle.warehouse, sle.posting_date)
	)

	query = apply_warehouse_filter(query, sle, filters)
	if filters.warehouse_type and not filters.warehouse:
		warehouses = frappe.get_all(
			"Warehouse",
			filters={"warehouse_type": filters.warehouse_type, "is_group": 0},
			pluck="name",
		)

		if warehouses:
			query = query.where(sle.warehouse.isin(warehouses))

	for field in ["item_code", "batch_no", "company"]:
		if filters.get(field):
			query = query.where(sle[field] == filters.get(field))

	return query.run(as_dict=True) or []


def get_stock_ledger_entries_for_batch_bundle(filters):
	sle = frappe.qb.DocType("Stock Ledger Entry")
	batch_package = frappe.qb.DocType("Serial and Batch Entry")

	query = (
		frappe.qb.from_(sle)
		.inner_join(batch_package)
		.on(batch_package.parent == sle.serial_and_batch_bundle)
		.select(
			sle.item_code,
			sle.warehouse,
			batch_package.batch_no,
			sle.posting_date,
			batch_package.qty.as_("actual_qty"),
			sle.incoming_rate,
			sle.outgoing_rate,
			sle.valuation_rate,
			sle.stock_value_difference,
			sle.voucher_type,
			sle.voucher_no
		)
		.where(
			(sle.docstatus < 2)
			& (sle.is_cancelled == 0)
			& (sle.has_batch_no == 1)
			& (sle.posting_date <= filters["to_date"])
		)
		.orderby(sle.item_code, sle.warehouse, sle.posting_date)
	)

	query = apply_warehouse_filter(query, sle, filters)
	if filters.warehouse_type and not filters.warehouse:
		warehouses = frappe.get_all(
			"Warehouse",
			filters={"warehouse_type": filters.warehouse_type, "is_group": 0},
			pluck="name",
		)

		if warehouses:
			query = query.where(sle.warehouse.isin(warehouses))

	for field in ["item_code", "batch_no", "company"]:
		if filters.get(field):
			if field == "batch_no":
				query = query.where(batch_package[field] == filters.get(field))
			else:
				query = query.where(sle[field] == filters.get(field))


	sles = query.run(as_dict=True) or []
	# for sle in sles:
	# 	if sle.voucher_type in ["Delivery Note", "Purchase Receipt", "Purchase Receipt"]:
	# 		frappe.msgprint(frappe.get_desk_link("Stock Ledger Entry", sle.name))

	return sles 


def get_item_warehouse_batch_map(filters, float_precision):
	sle = get_stock_ledger_entries(filters)
	iwb_map = {}

	from_date = getdate(filters["from_date"])
	to_date = getdate(filters["to_date"])

	for d in sle:
		iwb_map.setdefault(d.item_code, {}).setdefault(d.warehouse, {}).setdefault(
			d.batch_no, frappe._dict({
				"opening_qty": 0.0, 
				"opening_rate": 0.0, 
				"opening_amt": 0.0,
				"in_qty": 0.0, 
				"out_qty": 0.0, 
				"bal_qty": 0.0,
				"in_rate": 0.0,  # Added in_rate
				"out_rate": 0.0,  # Added out_rate
				"balance_rate": 0.0,  # Added balance_rate
				"balance_amt": 0.0,   # Added balance_amt
				"opening_transactions": [],
				"in_transactions": [],
				"out_transactions": []
			})
		)
		
		qty_dict = iwb_map[d.item_code][d.warehouse][d.batch_no]
		
		if d.posting_date < from_date:
			# Opening stock calculations
			qty_dict.opening_qty = flt(qty_dict.opening_qty, float_precision) + flt(
				d.actual_qty, float_precision
			)
			
			# Store opening transactions for weighted average rate calculation
			if flt(d.actual_qty) != 0:
				rate = 0
				if flt(d.actual_qty) > 0:
					# Incoming transaction - use incoming_rate or valuation_rate
					rate = flt(d.incoming_rate) or flt(d.valuation_rate)
				else:
					# Outgoing transaction - use outgoing_rate or valuation_rate
					rate = flt(d.outgoing_rate) or flt(d.valuation_rate)
				
				qty_dict.opening_transactions.append({
					'qty': flt(d.actual_qty),
					'rate': rate,
					'amount': flt(d.actual_qty) * rate
				})

		elif d.posting_date >= from_date and d.posting_date <= to_date:
			if flt(d.actual_qty) > 0:
				qty_dict.in_qty = flt(qty_dict.in_qty, float_precision) + flt(d.actual_qty, float_precision)
				
				# Store incoming transaction details for rate calculation
				rate = 0
				if d.voucher_type == "Purchase Receipt":
					rate = flt(d.incoming_rate) or flt(d.valuation_rate)
				elif d.voucher_type == "Delivery Note":
					rate = flt(d.valuation_rate)
				else:
					rate = flt(d.incoming_rate) or flt(d.valuation_rate)
				
				qty_dict.in_transactions.append({
					'qty': flt(d.actual_qty),
					'rate': rate,
					'amount': flt(d.actual_qty) * rate,
					'voucher_type': d.voucher_type
				})
			else:
				qty_dict.out_qty = flt(qty_dict.out_qty, float_precision) + abs(flt(d.actual_qty, float_precision))
				
				# Store outgoing transaction details for rate calculation
				rate = 0
				if d.voucher_type == "Delivery Note":
					rate = flt(d.valuation_rate)
				elif d.voucher_type == "Purchase Receipt":
					rate = flt(d.incoming_rate) or flt(d.valuation_rate)
				else:
					rate = flt(d.outgoing_rate) or flt(d.valuation_rate)
				
				qty_dict.out_transactions.append({
					'qty': abs(flt(d.actual_qty)),
					'rate': rate,
					'amount': abs(flt(d.actual_qty)) * rate,
					'voucher_type': d.voucher_type
				})

		qty_dict.bal_qty = flt(qty_dict.bal_qty, float_precision) + flt(d.actual_qty, float_precision)

	# Calculate weighted average rates and amounts
	for item_code in iwb_map:
		for warehouse in iwb_map[item_code]:
			for batch_no in iwb_map[item_code][warehouse]:
				qty_dict = iwb_map[item_code][warehouse][batch_no]
				
				# Calculate weighted average opening rate
				total_opening_amount = 0
				total_opening_qty = 0
				
				for txn in qty_dict.opening_transactions:
					if txn['qty'] > 0:  # Only consider positive quantities for rate calculation
						total_opening_amount += txn['amount']
						total_opening_qty += txn['qty']
				
				if total_opening_qty > 0:
					qty_dict.opening_rate = flt(
						total_opening_amount / total_opening_qty, float_precision
					)
				else:
					qty_dict.opening_rate = 0.0
				
				# Calculate opening amount
				qty_dict.opening_amt = flt(
					qty_dict.opening_qty * qty_dict.opening_rate, 
					float_precision
				)
				
				# Calculate weighted average in_rate
				total_in_amount = 0
				total_in_qty = 0
				
				for txn in qty_dict.in_transactions:
					total_in_amount += txn['amount']
					total_in_qty += txn['qty']
				
				if total_in_qty > 0:
					qty_dict.in_rate = flt(
						total_in_amount / total_in_qty, float_precision
					)
				else:
					qty_dict.in_rate = 0.0
				
				# Calculate weighted average out_rate
				total_out_amount = 0
				total_out_qty = 0
				
				for txn in qty_dict.out_transactions:
					total_out_amount += txn['amount']
					total_out_qty += txn['qty']
				
				if total_out_qty > 0:
					qty_dict.out_rate = flt(
						total_out_amount / total_out_qty, float_precision
					)
				else:
					qty_dict.out_rate = 0.0
				
				# Calculate balance rate and amount
				total_balance_value = qty_dict.opening_amt + (qty_dict.in_rate * qty_dict.in_qty) - (qty_dict.out_rate * qty_dict.out_qty)
				if qty_dict.bal_qty > 0:
					qty_dict.balance_rate = flt(
						total_balance_value / qty_dict.bal_qty, float_precision
					)
				else:
					qty_dict.balance_rate = 0.0
				
				# Clean up temporary data
				del qty_dict.opening_transactions
				del qty_dict.in_transactions
				del qty_dict.out_transactions

	return iwb_map


def get_item_details(filters):
	item_map = {}
	for d in (frappe.qb.from_("Item").select("name", "item_name", "description", "stock_uom")).run(as_dict=1):
		item_map.setdefault(d.name, d)

	return item_map
