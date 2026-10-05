# Copyright (c) 2025, Venture Up Technology and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from frappe import _


class VATReconciliation(Document):
	def validate(self):
		self.get_purchase_sales_invoice_details()

	def on_submit(self):
		self.validate_sales_purchase_invoices()
		self.set_vat_reconciliation_in_sales_purchase_invoices()

	def get_purchase_sales_invoice_details(self):
		if not self.from_date or not self.to_date:
			frappe.throw(_("Please specify both From Date and To Date."))

		purchase_invoices = frappe.db.get_all(
			"Purchase Invoice",
			filters={
				"posting_date": ["between", [self.from_date, self.to_date]],
				"company": self.company,
				"docstatus": 1,
				"total_taxes_and_charges": [">", 0],
				"custom_vat_reconciliation": ["is", "not set"],
				"status": "Paid"
			},
			fields=[
				"name",
				"posting_date",
				"supplier",
				"total_taxes_and_charges",
				"net_total",
				"grand_total"
			]
		)

		self.purchase_detail = []
		self.purchase_tax_total = 0.0
		for invoice in purchase_invoices:
			self.purchase_tax_total += flt(invoice.total_taxes_and_charges)
			self.append("purchase_detail", {
				"purchase_invoice": invoice.name,
				"posting_date": invoice.posting_date,
				"supplier": invoice.supplier,
				"total_taxes_and_charges": flt(invoice.total_taxes_and_charges),
				"net_total": flt(invoice.net_total),
				"grand_total": flt(invoice.grand_total)
			})

		sale_invoices = frappe.db.get_all(
			"Sales Invoice",
			filters={
				"posting_date": ["between", [self.from_date, self.to_date]],
				"company": self.company,
				"docstatus": 1,
				"total_taxes_and_charges": [">", 0],
				"custom_vat_reconciliation": ["is", "not set"],
				"status": "Paid"
			},
			fields=[
				"name",
				"posting_date",
				"customer",
				"total_taxes_and_charges",
				"net_total",
				"grand_total"
			]
		)

		self.sales_details = []
		self.sales_tax_total = 0.0
		for invoice in sale_invoices:
			self.sales_tax_total += flt(invoice.total_taxes_and_charges)
			self.append("sales_details", {
				"sales_invoice": invoice.name,
				"posting_date": invoice.posting_date,
				"customer": invoice.customer,
				"total_taxes_and_charges": flt(invoice.total_taxes_and_charges),
				"net_total": flt(invoice.net_total),
				"grand_total": flt(invoice.grand_total)
			})

		self.tax_balance = self.purchase_tax_total - self.sales_tax_total
		self.tax_balance = flt(self.tax_balance)


	def validate_sales_purchase_invoices(self):
		if not self.purchase_detail and not self.sales_details:
			frappe.throw(_("No purchase or sales invoices found for the selected date range."))

	def set_vat_reconciliation_in_sales_purchase_invoices(self):
		for purchase in self.purchase_detail:
			frappe.db.set_value(
				"Purchase Invoice",
				purchase.purchase_invoice,
				"custom_vat_reconciliation",
				self.name
			)

		for sale in self.sales_details:
			frappe.db.set_value(
				"Sales Invoice",
				sale.sales_invoice,
				"custom_vat_reconciliation",
				self.name
			)

		frappe.db.commit()
