# coding: utf-8

import json
import logging
import urlparse

import dateutil.parser
import pytz

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment_checkout.controllers.main import CheckoutController
from odoo.tools.float_utils import float_compare


_logger = logging.getLogger(__name__)


class AcquirerPaypal(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('checkout', 'Checkout.com')])
    checkout_username = fields.Char('UserName')
    checkout_password = fields.Char('Password')
    checkout_url = fields.Char('Web Link',help="pass link of website to go for payment.")
    
    @api.multi
    def checkout_get_form_action_url(self):
        """ Returns the form action URL, for form-based acquirer implementations. """
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        return self.checkout_url+"?url='%s'"% urlparse.urljoin(base_url)#CheckoutController._cancel_url)
        
    @api.multi
    def checkout_form_generate_values(self, values):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')

        checkout_tx_values = dict(values)
        checkout_tx_values.update({
            'cmd': '_xclick',
            'business': self.checkout_username,
            'item_name': '%s: %s' % (self.company_id.name, values['reference']),
            'item_number': values['reference'],
            'amount': values['amount'],
            'currency_code': values['currency'] and values['currency'].name or '',
            'address1': values.get('partner_address'),
            'city': values.get('partner_city'),
            'country': values.get('partner_country') and values.get('partner_country').code or '',
            'state': values.get('partner_state') and (values.get('partner_state').code or values.get('partner_state').name) or '',
            'email': values.get('partner_email'),
            'zip_code': values.get('partner_zip'),
            'first_name': values.get('partner_first_name'),
            'last_name': values.get('partner_last_name'),
            'checkout_return': '%s' % urlparse.urljoin(base_url, CheckoutController._return_url),
            'cancel_return': '%s' % urlparse.urljoin(base_url, CheckoutController._cancel_url),
            'custom': json.dumps({'return_url': '%s' % checkout_tx_values.pop('return_url')}) if checkout_tx_values.get('return_url') else False,
        })
        return checkout_tx_values


