from erpnext.stock.doctype.putaway_rule.putaway_rule import PutawayRule


class CustomPutawayRule(PutawayRule):
	def validate(self):
		self.validate_duplicate_rule()
		self.validate_warehouse_and_company()
		self.set_stock_capacity()
		self.validate_capacity()
		self.validate_priority()
