app_name = "global_petroleum_customizations"
app_title = "Global Petroleum Customizations"
app_publisher = "Venture Up Technology"
app_description = "Global Petroleum Customizations"
app_email = "info@ventureuptechnology.com"
app_license = "mit"
required_apps = ["erpnext"]

app_logo_url = "/assets/global_petroleum_customizations/png/gp_logo.png"

doctype_js = {
    "Purchase Invoice" : "public/js/purchase_invoice.js",
    "Delivery Note" : "public/js/delivery_note.js",
    "Stock Entry" : "public/js/stock_entry.js",
    "Payment Reconciliation" : "public/js/payment_reconciliation.js"
    }

website_context = {
	"favicon": "/assets/global_petroleum_customizations/png/gp_logo.png",
	"splash_image": "/assets/global_petroleum_customizations/png/gp_logo.png",
}

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Delivery Note": "global_petroleum_customizations.overrides.delivery_note.CustomDeliveryNote",
	"Putaway Rule": "global_petroleum_customizations.overrides.putaway_rule.CustomPutawayRule",
	"Stock Entry": "global_petroleum_customizations.overrides.stock_entry.CustomStockEntry"
}

doc_events = {
	"Purchase Invoice": {
		"validate": [
            "global_petroleum_customizations.overrides.purchase_invoice.validate_warehouse",
            "global_petroleum_customizations.overrides.purchase_invoice.validate_pro_items",
		],
	},
	"Purchase Receipt": {
		"validate": "global_petroleum_customizations.overrides.purchase_receipt.validate_warehouse",
	}
}

# Scheduled Tasks
# ---------------
# scheduler_events = {
# 	"daily": [
# 		"global_petroleum_customizations.global_petroleum_customizations.doctype.tank_lease_contract.tank_lease_contract.expire_tank_lease_contracts"
# 	],
# }