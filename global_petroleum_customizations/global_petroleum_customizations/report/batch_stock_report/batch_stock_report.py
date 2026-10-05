# Copyright (c) 2025, Venture Up Technology and contributors
# For license information, please see license.txt

import frappe
from global_petroleum_customizations.global_petroleum_customizations.report.itemwise_batchwise_stock_report.itemwise_batchwise_stock_report import execute as gp_execute


def execute(filters=None):
	columns, data = gp_execute(filters)

	return columns, data