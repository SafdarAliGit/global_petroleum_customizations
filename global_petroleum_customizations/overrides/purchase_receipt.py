from global_petroleum_customizations.overrides.global_petroleum_utils import validate_tank_lease_warehouse


def validate_warehouse(doc, method):
	for item in doc.items:
		validate_tank_lease_warehouse(item.warehouse, item.item_code, doc.posting_date)