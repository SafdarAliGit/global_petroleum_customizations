# Copyright (c) 2025, Venture Up Technology and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns()
	data = []

	so_filters={
		"docstatus": 1,
	}

	if filters.get("sales_order"):
		so_filters["name"] = filters.get("sales_order")
	else:

		from_date = filters.get("from_date")
		end_date = filters.get("end_date")
		if not (from_date and end_date):
			frappe.throw("Please set From Date and To Date")

		so_filters["transaction_date"] = ["between", [from_date, end_date]]

	sales_orders = frappe.get_all(
		"Sales Order",
		filters=so_filters,
		fields=["name", "transaction_date"],
		order_by="transaction_date asc"
	)

	if not sales_orders:
		return columns, []

	sales_order_names = [so.name for so in sales_orders]

	sales_order_items = frappe.get_all(
		"Sales Order Item",
		filters={"parent": ["in", sales_order_names]},
		fields=["parent", "item_code", "qty", "rate", "amount", "warehouse"]
	)

	delivery_note_items = frappe.db.sql("""
		SELECT
			dn.name AS delivery_note,
			dn.posting_date,
			dni.against_sales_order,
			dni.item_code,
			dni.qty,
			dni.rate,
			dni.amount,
			dni.warehouse
		FROM
			`tabDelivery Note` dn
		INNER JOIN
			`tabDelivery Note Item` dni ON dni.parent = dn.name
		WHERE
			dni.against_sales_order IN %(sales_orders)s
			AND dn.docstatus = 1
		ORDER BY
			dn.posting_date asc
	""", {
		"sales_orders": tuple(sales_order_names)
	}, as_dict=True)

	so_items_map = {}
	for item in sales_order_items:
		so_items_map.setdefault(item.parent, []).append(item)

	dn_items_map = {}
	for dn in delivery_note_items:
		dn_items_map.setdefault(dn.against_sales_order, []).append(dn)

	for so in sales_orders:
		so_name = so.name
		so_date = so.transaction_date

		for item in so_items_map.get(so_name, []):
			data.append([
				so_name,                 # Bill No. (Sales Order)
				item.item_code,
				so_date,                 # Sales Order Date
				item.qty,
				item.rate,
				item.amount,
				item.warehouse
			])

		data.append(["", "", "", "", "", "", ""])
		dn_qty = 0
		dn_rate = 0
		dn_amount = 0
		for dn in dn_items_map.get(so_name, []):
			dn_qty += dn.qty
			dn_amount += dn.amount
			dn_rate = dn.amount / dn.qty if dn.qty else 0
			data.append([
				dn.delivery_note,         # Bill No. (Delivery Note)
				dn.item_code,
				dn.posting_date,          # Delivery Note Date
				dn.qty,
				dn.rate,
				dn.amount,
				dn.warehouse
			])
		
		if dn_items_map.get(so_name):
			data.append(["", "", "", dn_qty, dn_rate, dn_amount, ""])

	return columns, data


def get_columns():
	return [
		{
			"fieldname": "bill_no",
			"label": "Bill No.",
			"fieldtype": "Data",
			"width": 190
		},
		{
			"fieldname": "item",
			"label": "Item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 150
		},
		{
			"fieldname": "date",
			"label": "Date",
			"fieldtype": "Date",
			"width": 120
		},
		{
			"fieldname": "qty",
			"label": "Qty",
			"fieldtype": "Float",
			"width": 100
		},
		{
			"fieldname": "rate",
			"label": "Rate",
			"fieldtype": "Currency",
			"width": 100
		},
		{
			"fieldname": "amount",
			"label": "Amount",
			"fieldtype": "Currency",
			"width": 120
		},
		{
			"fieldname": "storage_tank",
			"label": "Storage Tank",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 150
		},
	]
