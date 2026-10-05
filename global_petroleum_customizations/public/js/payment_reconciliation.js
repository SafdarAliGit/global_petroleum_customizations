// Global Petroleum Customizations for Payment Reconciliation

frappe.ui.form.on("Payment Reconciliation", {
	refresh: function(frm) {
		add_total_fields(frm);
		update_totals(frm);
		setup_grid_events(frm);
	},

	get_unreconciled_entries: function(frm) {
		setTimeout(() => {
			update_totals(frm);
		}, 1000);
	},

	allocate: function(frm) {
		setTimeout(() => {
			update_totals(frm);
		}, 1000);
	}
});

function add_total_fields(frm) {
	if (frm.get_field("invoices") && !frm.get_field("invoices").$wrapper.next('.invoice-total-section').length) {
		frm.get_field("invoices").$wrapper.after(`
			<div class="invoice-total-section" style="padding: 10px; background-color: var(--bg-color, #f8f9fa); border: 1px solid var(--border-color, #dee2e6); margin-top: 5px; color: var(--text-color, #000);">
				<div class="row">
					<div class="col-md-6">
						<strong style="color: var(--heading-color, #212529);">Selected Invoices Total: <span class="invoice-total-amount" style="color: var(--text-color, #000);">0.00</span></strong>
					</div>
					<div class="col-md-6">
						<strong style="color: var(--heading-color, #212529);">All Invoices Total: <span class="invoice-grand-total" style="color: var(--text-color, #000);">0.00</span></strong>
					</div>
				</div>
			</div>
		`);
	}

	if (frm.get_field("payments") && !frm.get_field("payments").$wrapper.next('.payment-total-section').length) {
		frm.get_field("payments").$wrapper.after(`
			<div class="payment-total-section" style="padding: 10px; background-color: var(--bg-color, #f8f9fa); border: 1px solid var(--border-color, #dee2e6); margin-top: 5px; color: var(--text-color, #000);">
				<div class="row">
					<div class="col-md-6">
						<strong style="color: var(--heading-color, #212529);">Selected Payments Total: <span class="payment-total-amount" style="color: var(--text-color, #000);">0.00</span></strong>
					</div>
					<div class="col-md-6">
						<strong style="color: var(--heading-color, #212529);">All Payments Total: <span class="payment-grand-total" style="color: var(--text-color, #000);">0.00</span></strong>
					</div>
				</div>
			</div>
		`);
	}
}

function update_totals(frm) {
	update_invoice_totals(frm);
	update_payment_totals(frm);
}

function update_invoice_totals(frm) {
	let selected_total = 0;
	let grand_total = 0;

	let selected_invoices = frm.fields_dict.invoices?.grid?.get_selected_children() || [];
	
	selected_invoices.forEach(row => {
		selected_total += flt(row.outstanding_amount);
	});

	frm.doc.invoices?.forEach(row => {
		grand_total += flt(row.outstanding_amount);
	});

	frm.get_field("invoices")?.$wrapper?.next('.invoice-total-section')?.find('.invoice-total-amount')?.text(format_currency(selected_total, frm.doc.currency));
	frm.get_field("invoices")?.$wrapper?.next('.invoice-total-section')?.find('.invoice-grand-total')?.text(format_currency(grand_total, frm.doc.currency));
}

function update_payment_totals(frm) {
	let selected_total = 0;
	let grand_total = 0;

	let selected_payments = frm.fields_dict.payments?.grid?.get_selected_children() || [];
	
	selected_payments.forEach(row => {
		selected_total += flt(row.amount);
	});

	frm.doc.payments?.forEach(row => {
		grand_total += flt(row.amount);
	});

	frm.get_field("payments")?.$wrapper?.next('.payment-total-section')?.find('.payment-total-amount')?.text(format_currency(selected_total, frm.doc.currency));
	frm.get_field("payments")?.$wrapper?.next('.payment-total-section')?.find('.payment-grand-total')?.text(format_currency(grand_total, frm.doc.currency));
}

function setup_grid_events(frm) {
	if (frm.fields_dict['invoices'] && frm.fields_dict['invoices'].grid) {
		frm.fields_dict['invoices'].grid.wrapper.off('change', 'input[type="checkbox"]');
		frm.fields_dict['invoices'].grid.wrapper.on('change', 'input[type="checkbox"]', (e) => {
			setTimeout(() => {
				update_totals(frm);
			}, 100);
		});
	}

	if (frm.fields_dict['payments'] && frm.fields_dict['payments'].grid) {
		frm.fields_dict['payments'].grid.wrapper.off('change', 'input[type="checkbox"]');
		frm.fields_dict['payments'].grid.wrapper.on('change', 'input[type="checkbox"]', (e) => {
			setTimeout(() => {
				update_totals(frm);
			}, 100);
		});
	}
}

frappe.ui.form.on("Payment Reconciliation Invoice", {
	invoices_remove: function(frm) {
		setTimeout(() => {
			update_totals(frm);
		}, 100);
	}
});

frappe.ui.form.on("Payment Reconciliation Payment", {
	payments_remove: function(frm) {
		setTimeout(() => {
			update_totals(frm);
		}, 100);
	}
});