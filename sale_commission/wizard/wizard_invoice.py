from odoo import _, fields, models


class SaleCommissionMakeInvoice(models.TransientModel):
    _name = "sale.commission.make.invoice"
    _description = "Wizard for making an invoice from a settlement"

    def _default_journal_id(self):
        return self.env["account.journal"].search([("type", "=", "purchase")])[:1]

    def _default_product_name(self):
        pro_n = self.env['product.template'].search([('name', '=', "Commission")], limit=1).id 
        pro_id = self.env['product.product'].search([('product_tmpl_id', '=', pro_n)], limit=1).id

        return pro_id

    def _default_settlement_ids(self):
        return self.env.context.get("settlement_ids", [])

    def _default_from_settlement(self):
        return bool(self.env.context.get("settlement_ids"))

    journal_id = fields.Many2one(
        comodel_name="account.journal",
        required=True,
        domain="[('type', '=', 'purchase')]",
        default=_default_journal_id,
    )
    company_id = fields.Many2one(
        comodel_name="res.company", related="journal_id.company_id", readonly=True
    )
    product_id = fields.Many2one(
        string="Product for billing", default=_default_product_name, comodel_name="product.product", required=True
    )
    settlement_ids = fields.Many2many(
        comodel_name="sale.commission.settlement",
        relation="sale_commission_make_invoice_settlement_rel",
        column1="wizard_id",
        column2="settlement_id",
        domain="[('state', '=', 'settled'),"
        "('company_id', '=', company_id)]",
        default=_default_settlement_ids,
    )
    from_settlement = fields.Boolean(default=_default_from_settlement)
    date = fields.Date(default=fields.Date.context_today)

    def button_create(self):
        self.ensure_one()
        if self.settlement_ids:
            settlements = self.settlement_ids
        else:
            settlements = self.env["sale.commission.settlement"].search(
                [
                    ("state", "=", "settled"),
                    ("company_id", "=", self.journal_id.company_id.id),
                ]
            )
        invoices = settlements.make_invoices(
            self.journal_id, self.product_id, date=self.date
        )
        # go to results
        if len(settlements):
            return {
                "name": _("Created Invoices"),
                "type": "ir.actions.act_window",
                "views": [[False, "list"], [False, "form"]],
                "res_model": "account.move",
                "domain": [["id", "in", invoices.ids]],
            }