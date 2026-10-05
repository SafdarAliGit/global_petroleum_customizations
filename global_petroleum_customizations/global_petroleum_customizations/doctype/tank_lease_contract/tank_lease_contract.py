# Copyright (c) 2025, Venture Up Technology and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, get_datetime, today, month_diff, flt


class TankLeaseContract(Document):
	def validate(self):
		self.validate_dates()
		self.validate_warehouse()
		self.calculate_lease_fee()
		self.set_tank_capacity_and_rate_in_metric_ton()
		# self.calculate_lease_duration_months()
		self.set_status()

	def validate_dates(self):
		if self.booking_date > self.expiry_date:
			frappe.throw(
				"Booking date {} cannot be before available for Expiry date {}.".format(self.booking_date, self.expiry_date)
			)

	def validate_warehouse(self):
		warehouse = frappe.get_doc("Warehouse", self.warehouse)
		if self.warehouse:
			if warehouse.is_group:
				frappe.throw(_("Please select a warehouse, not a warehouse group."))

			if not warehouse.custom_is_tank_lease_warehouse:
				frappe.throw(_("Please select a warehouse, with 'Is Tank Lease Warehouse' checked."))

			# if warehouse.custom_tank_lease_contract and warehouse.custom_status != "Expired" and not warehouse.disabled:
			# 	frappe.throw(_("Warehouse already booked against {0}, please select another warehouse.").format(frappe.get_desk_link("Tank Lease Contract", warehouse.custom_tank_lease_contract)))

	def set_status(self):
		if self.docstatus == 0:
			self.db_set("status", "Draft")

		elif self.docstatus == 1:
			if get_datetime(self.expiry_date) < now_datetime():
				self.db_set("status", "Expired")
			else:
				self.db_set("status", "Active")
		elif self.docstatus == 2:
			self.db_set("status", "Cancelled")

	def set_tank_capacity_and_rate_in_metric_ton(self):
		self.tank_capacity_in_metric_ton = self.tank_capacity * self.base_oil_density

	def calculate_lease_fee(self):
		self.total_contract_amount = self.tank_capacity * flt(self.lease_duration_in_months) * self.rate

	def calculate_lease_duration_months(self):
		self.lease_duration_in_months = month_diff(self.expiry_date, self.booking_date)

	def before_submit(self):
		self.expire_existing_tlc()
		self.book_warehouse()
		self.create_putaway_rule()

	def on_cancel(self):
		frappe.db.set_value("Warehouse", self.warehouse, "custom_base_oil_item", "")
		frappe.db.set_value("Warehouse", self.warehouse, "custom_tank_lease_contract", "")
		frappe.db.set_value("Warehouse", self.warehouse, "custom_booking_date", None)
		frappe.db.set_value("Warehouse", self.warehouse, "custom_expiry_date", None)
		frappe.db.set_value("Warehouse", self.warehouse, "custom_status", "Available")
		frappe.db.set_value("Warehouse", self.warehouse, "disabled", 0)
		self.delete_putaway_rule()

	def book_warehouse(self):
		frappe.db.set_value("Warehouse", self.warehouse, "custom_base_oil_item", self.base_oil_item)
		frappe.db.set_value("Warehouse", self.warehouse, "custom_tank_lease_contract", self.name)
		frappe.db.set_value("Warehouse", self.warehouse, "custom_booking_date", self.booking_date)
		frappe.db.set_value("Warehouse", self.warehouse, "custom_expiry_date", self.expiry_date)
		frappe.db.set_value("Warehouse", self.warehouse, "custom_status", "Booked")
		frappe.db.set_value("Warehouse", self.warehouse, "disabled", 0)


	def create_putaway_rule(self):
		tank_capacity_in_metric_ton = frappe.db.get_value("Warehouse", self.warehouse, "custom_tank_capacity_in_metric_ton")
		if not tank_capacity_in_metric_ton:
			frappe.throw(_("Tank Capacity not set for the {}").format(frappe.get_desk_link("Warehouse", self.warehouse)))

		if frappe.db.exists("Putaway Rule", {"warehouse": self.warehouse, "item_code": self.base_oil_item, "company":	self.company, "custom_tank_lease_putaway_rule": 1}):
			putaway_rule = frappe.get_doc("Putaway Rule", {"warehouse": self.warehouse, "item_code": self.base_oil_item, "company":	self.company, "custom_tank_lease_putaway_rule": 1})		
		else:
			putaway_rule = frappe.new_doc("Putaway Rule")
			putaway_rule.company =	self.company
			putaway_rule.warehouse = self.warehouse
			putaway_rule.item_code = self.base_oil_item
			putaway_rule.custom_tank_lease_putaway_rule = 1

		putaway_rule.capacity = tank_capacity_in_metric_ton
		putaway_rule.custom_tank_lease_contract = self.name
		putaway_rule.save()

		return putaway_rule
	
	def expire_existing_tlc(self):
		if frappe.db.exists("Tank Lease Contract", {"warehouse": self.warehouse, "item_code": self.base_oil_item, "company": self.company, "custom_tank_lease_putaway_rule": 1}):
			pass

	def delete_putaway_rule(self):
		putaway_rules = frappe.get_all("Putaway Rule", filters={"warehouse": self.warehouse, "item_code": self.base_oil_item, "custom_tank_lease_putaway_rule": 1, "custom_tank_lease_contract": self.name})
		for putaway_rule in putaway_rules:
			frappe.delete_doc("Putaway Rule", putaway_rule.name)


def update_expired_tank_lease_contracts():
	"""Background job to update expired Tank Lease Contracts and disable linked warehouses."""
	expired_contracts = frappe.get_all(
		"Tank Lease Contract",
		filters={"expiry_date": ("<=", now_datetime()), "status": ("!=", "Expired"), "docstatus": ("=", 1)},
		fields=["name", "warehouse"]
	)
	
	for contract in expired_contracts:
		contract = frappe.get_doc("Tank Lease Contract", contract.name)
		contract.set_status()
		if contract.warehouse:
			frappe.db.set_value("Warehouse", contract.warehouse, "disabled", 1)
			frappe.db.set_value("Warehouse", contract.warehouse, "custom_status", "Expired")
			
		frappe.db.commit()


def expire_tank_lease_contracts():
	"""Schedule the job to run daily."""
	frappe.enqueue("global_petroleum_customizations.global_petroleum_customizations.doctype.tank_lease_contract.tank_lease_contract.update_expired_tank_lease_contracts", queue='long', timeout=600, job_name="Update Tank Lease Contracts")


@frappe.whitelist()
def create_purchase_invoice(source_name, target_doc=None):
	from frappe.model.mapper import get_mapped_doc

	def post_process(source, target):
		target.posting_date = today()

	def set_items(source, target):
		target.append("items", {
			"item_code": source.lease_item,
			"qty": 1,
			"rate": source.total_contract_amount,
			"cost_center": source.cost_center,
			"custom_tank_lease_contract": source.name,
			"custom_name_of_tank": source.warehouse
		})

	doc = get_mapped_doc(
		"Tank Lease Contract",
		source_name,
		{
			"Tank Lease Contract": { 
				"doctype": "Purchase Invoice", 
				"validation": {
					"docstatus": ["=", 1]
				}
			}
		},
		target_doc,
		post_process
	)

	set_items(frappe.get_doc("Tank Lease Contract", source_name), doc)

	return doc


@frappe.whitelist()
def create_purchase_invoice_for_multiple_tlc(docnames):
	if isinstance(docnames, str):
		import json
		docnames = json.loads(docnames)
	else:
		docnames = docnames

	if not docnames:
		frappe.throw("No Tank Lease Contracts selected.")

	tlc_data = [frappe.db.get_value("Tank Lease Contract", docname, ["supplier", "cost_center", "company", "currency", "conversion_rate"], as_dict=1) for docname in docnames]
	currency = set([d.currency for d in tlc_data])
	conversion_rate = set([d.conversion_rate for d in tlc_data])
	supplier = [d.supplier for d in tlc_data]
	cost_center = [d.cost_center for d in tlc_data]
	company = [d.company for d in tlc_data]

	if len(set(supplier)) > 1:
		frappe.throw(_("All selected contracts must have the same supplier."))

	if len(set(currency)) > 1:
		frappe.throw(_("All selected contracts must have the same same Currency."))

	if len(set(conversion_rate)) > 1:
		frappe.throw(_("All selected contracts must have the same same Currency Rate."))
	
	if len(set(cost_center)) > 1:
		frappe.throw(_("All selected contracts must have the same cost center."))
	
	if len(set(company)) > 1:
		frappe.throw(_("All selected contracts must have the same company."))
	
	supplier = supplier[0]
	cost_center = cost_center[0]
	company = company[0]

	pi = frappe.new_doc("Purchase Invoice")
	pi.supplier = supplier
	pi.company = company
	pi.cost_center = cost_center
	pi.posting_date = today()

	for name in docnames:
		doc = frappe.get_doc("Tank Lease Contract", name)

		if doc.docstatus != 1:
			frappe.throw(f"Tank Lease Contract {name} must be submitted.")

		if doc.supplier != supplier or doc.company != company:
			frappe.throw("All selected contracts must have the same supplier and company.")

		pi.append("items", {
			"item_code": doc.lease_item,
			"qty": 1,
			"rate": doc.total_contract_amount,
			"cost_center": cost_center,
			"custom_tank_lease_contract": doc.name,
			"custom_name_of_tank": doc.warehouse
		})

	pi.set_missing_values()

	return pi
