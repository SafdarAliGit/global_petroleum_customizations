// Copyright (c) 2025, Venture Up Technology and contributors
// For license information, please see license.txt

frappe.query_reports["Itemwise batchwise stock report"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			width: "80",
			default: erpnext.utils.get_fiscal_year(frappe.datetime.get_today(), true)[1],
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			width: "80",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "item_code",
			label: __("Item Code"),
			fieldtype: "Link",
			options: "Item",
			get_query: function () {
				return {
					filters: {
						has_batch_no: 1,
					},
				};
			},
		},
		{
			fieldname: "warehouse",
			label: __("Warehouse"),
			fieldtype: "Link",
			options: "Warehouse",
		},
		{
			fieldname: "hide_zero_balance",
			label: __("Hide Zero Balance"),
			fieldtype: "Check",
			width: "80",
			default: 1,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		if (column.fieldname == "Batch" && data && !!data["Batch"]) {
			value = data["Batch"];
			column.link_onclick =
				"frappe.query_reports['Batch-Wise Balance History'].set_batch_route_to_stock_ledger(" +
				JSON.stringify(data) +
				")";
		}

		value = default_formatter(value, row, column, data);
		return value;
	},
	set_batch_route_to_stock_ledger: function (data) {
		frappe.route_options = {
			batch_no: data["Batch"],
		};

		frappe.set_route("query-report", "Stock Ledger");
	},
};
