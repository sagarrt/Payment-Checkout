# -*- coding: utf-8 -*-

import json
import logging
import pprint
import urllib
import urllib2
import werkzeug

from odoo import http
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class CheckoutController(http.Controller):
    _return_url = '/payment/checkout/return/'
    _cancel_url = '/payment/checkout/cancel/'

    def _get_return_url(self, **post):
        """ Extract the return URL from the data coming from Checkout. """
        return_url = post.pop('return_url', '')
        if not return_url:
            custom = json.loads(urllib.unquote_plus(post.pop('custom', False) or post.pop('cm', False) or '{}'))
            return_url = custom.get('return_url', '/')
        return return_url

    def _parse_pdt_response(self, response):
        """ Parse a text response for a PDT verification .

            :param response str: text response, structured in the following way:
                STATUS\nkey1=value1\nkey2=value2...\n
             or STATUS\nError message...\n
            :rtype tuple(str, dict)
            :return: tuple containing the STATUS str and the key/value pairs
                     parsed as a dict
        """
        lines = filter(None, response.split('\n'))
        status = lines.pop(0)

        pdt_post = {}
        for line in lines:
            split = line.split('=', 1)
            if len(split) == 2:
                pdt_post[split[0]] = urllib.unquote_plus(split[1]).decode('utf8')
            else:
                _logger.warning('Paypal: error processing pdt response: %s', line)

        return status, pdt_post

    def checkout_validate_data(self, **post):
        res = False
        new_post = dict(post, cmd='_notify-validate')
        reference = post.get('item_number')
        tx = None
        if reference:
            tx = request.env['payment.transaction'].search([('reference', '=', reference)])
        paypal_urls = request.env['payment.acquirer']._get_paypal_urls(tx and tx.acquirer_id.environment or 'prod')
        pdt_request = bool(new_post.get('amt'))  # check for spefific pdt param
        if pdt_request:
            # this means we are in PDT instead of DPN like before
            # fetch the PDT token
            new_post['at'] = request.env['ir.config_parameter'].sudo().get_param('payment_paypal.pdt_token')
            new_post['cmd'] = '_notify-synch'  # command is different in PDT than IPN/DPN
        validate_url = paypal_urls['paypal_form_url']
        urequest = urllib2.Request(validate_url, werkzeug.url_encode(new_post))
        uopen = urllib2.urlopen(urequest)
        resp = uopen.read()
        if pdt_request:
            resp, post = self._parse_pdt_response(resp)
        if resp == 'VERIFIED' or pdt_request and resp == 'SUCCESS':
            _logger.info('Checkout: validated data')
            res = request.env['payment.transaction'].sudo().form_feedback(post, 'checkout')
        elif resp == 'INVALID' or pdt_request and resp == 'FAIL':
            _logger.warning('Checkout: answered INVALID/FAIL on data verification')
        else:
            _logger.warning('Checkout: unrecognized paypal answer, received %s instead of VERIFIED/SUCCESS or INVALID/FAIL (validation: %s)' % (resp, 'PDT' if pdt_request else 'IPN/DPN'))
        return res

    @http.route('/payment/checkout/return', type='http', auth="public", methods=['POST', 'GET'], csrf=False)
    def checkout_dpn(self, **post):
    	print "kkkk"
        _logger.info('Beginning Checkout DPN form_feedback with post data %s', pprint.pformat(post))  # debug
        return_url = self._get_return_url(**post)
        self.checkout_validate_data(**post)
        return werkzeug.utils.redirect(return_url)

    @http.route('/payment/checkout/cancel', type='http', auth="user", csrf=False)
    def checkout_cancel(self, **post):
        """ When the user cancels its Checkout payment: GET on this route """
        _logger.info('Beginning Checkout cancel with post data %s', pprint.pformat(post))  # debug
        return_url = self._get_return_url(**post)
        return werkzeug.utils.redirect(return_url)
        
        
    @http.route('/website/check_gengo_set', type='json', auth='user', website=True)
    def new_route_test(self,**post):
    	print 'testing/..................'
    	return [{'status': 'test',
                 }]
    
    
