# coding: utf-8

import json
import logging
import urlparse

import dateutil.parser
import pytz

from odoo import api, fields, models, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.tools.float_utils import float_compare


_logger = logging.getLogger(__name__)


class AcquirerPaypal(models.Model):
    _inherit = 'payment.acquirer'

    provider = fields.Selection(selection_add=[('checkout', 'Checkout')])
    checkout_secret_key = fields.Char('Secret Key')
    chekout_publishable_key = fields.Char('Published Key')

