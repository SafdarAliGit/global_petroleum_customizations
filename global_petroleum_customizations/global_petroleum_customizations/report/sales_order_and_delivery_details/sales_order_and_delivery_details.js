// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order and Delivery Details"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.month_start()
		},
		{
			"fieldname": "end_date",
			"label": "End Date",
			"fieldtype": "Date",
			"default": frappe.datetime.month_end()
		},
		{
			"fieldname": "sales_order",
			"label": "Sales Order",
			"fieldtype": "Link",
			"options": "Sales Order"
		}
	]
};
