# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from pytz import timezone, utc
from functools import partial
from datetime import timedelta
import time, datetime
import calendar
import json
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import AccessError
import requests

import logging
_logger = logging.getLogger(__name__)

def make_aware(dt):
    """ Return ``dt`` with an explicit timezone, together with a function to
        convert a datetime to the same (naive or aware) timezone as ``dt``.
    """
    if dt.tzinfo:
        return dt, lambda val: val.astimezone(dt.tzinfo)
    else:
        return dt.replace(tzinfo=utc), lambda val: val.astimezone(utc).replace(tzinfo=None)

class HelpdeskTicketA(models.Model):
    _inherit = 'helpdesk.ticket'


    poli_com = fields.Char(string="Policy Number")
    w_resolved = fields.Char(string="How it was Resolved")
    name_complaint = fields.Char(string="Complainant")
    phone = fields.Char(string="Phone Number")
    is_escalate = fields.Boolean(string='Is escalate?', default=False)
    count_escale = fields.Integer(string="count_escale", default=0)
    ticket_type_id = fields.Many2one('helpdesk.ticket.type', string="Ticket Type",domain="[('team', '=', team_id)]")
    
    partner_name = fields.Char(string='Beneficiary Name')
    partner_email = fields.Char(string='Beneficiary Email')

    commercial_partner_id = fields.Many2one(related='partner_id.commercial_partner_id')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', domain="[('partner_id', 'child_of', commercial_partner_id), ('company_id', '=', company_id)]",
        groups="sales_team.group_sale_salesman,account.group_account_invoice",
        help="Reference of the Sales Order to which this ticket refers. Setting this information aims at easing your After Sales process and only serves indicative purposes.")

    @api.onchange('team_id')
    def _onchange_ticket_type_id(self):
        if self.team_id:
            ticket_type_id = self.env['helpdesk.ticket.type'].search([('team', '=', self.team_id.id)], limit=1).id
            
            self.ticket_type_id = ticket_type_id

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id and not self.partner_id.parent_id:
            self.partner_name = self.partner_id.name
            self.email_cc = self.partner_id.email
            self.phone = self.partner_id.phone
            self.name_complaint = self.partner_id.name
            self.poli_com = self.partner_id.extbenid
        elif self.partner_id and self.partner_id.parent_id:
            self.partner_email = self.partner_id.email
            self.email_cc = self.partner_id.parent_id.email 
            self.phone = self.partner_id.phone
            self.name_complaint = self.partner_id.name
            self.poli_com = self.partner_id.extbenid   

    # @api.onchange('partner_id')
    # def _onchange_partner_id1(self):
    #     if self.partner_id:
            # self.phone = self.partner_id.phone
            # self.name_complaint = self.partner_id.name
            # self.poli_com = self.partner_id.extbenid
        # if self.partner_id and self.partner_id.parent_id:
        #     self.email_cc = self.partner_id.parent_id.email

    def _notify_get_reply_to(self, default=None, records=None, company=None, doc_names=None):
        """ Override to set alias of tickets to their team if any. """
        # aliases = self.mapped('user_id').sudo()._notify_get_reply_to(default=default, records=None, company=company, doc_names=None)
        res = {ticket.id: ticket.user_id.email for ticket in self}
        leftover = self.filtered(lambda rec: not rec.user_id)
        if leftover:
            res.update(super(HelpdeskTicketA, leftover)._notify_get_reply_to(default=default, records=None, company=company, doc_names=doc_names))
        return res 
    
    def send_email_from(self):
        outmails = self.env['ir.mail_server'].search([])
        for outmail in outmails:
            smtpuser = outmail.smtp_user

        return smtpuser    


    def send_email_cc_mail(self):
        self.env.ref('helpdesk.new_ticket_request_email_template').send_mail(self.id)


    @api.model
    def create(self, vals):
        tickets = super(HelpdeskTicketA, self).create(vals)
        # Check if email_cc has to be sent
        # ${object.email_cc}
        if vals.get('email_cc') and tickets:
            tickets.send_email_cc_mail()
        return tickets
   
    def escalate_ticket(self):
        now1 = datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        now =datetime.datetime.strptime(now1, '%Y-%m-%d %H:%M:%S')
        all_ticket = self.env['helpdesk.ticket'].search([])
        # _logger.info("all_ticket=== '" + str(all_ticket) + "' ok !")
        for ticket in all_ticket:
            if ticket.user_id:
                assign = self.env['helpdesk.team'].search([('id', '=', ticket.team_id.id)])
                times = self.env['helpdesk.sla'].search([('team_id', '=', ticket.team_id.id)])
                for time in times:
                    day = time.time_days
                    hour = time.time_hours
                    minute = time.time_minutes
                    if assign.escalate and assign.escalate1 and ticket.sla_deadline != False:
                        sladead = ticket.sla_deadline
                        sla_microsec = sladead.microsecond
                        sla_def = sladead - timedelta(microseconds= sla_microsec)
                        sla = datetime.datetime.strptime(str(sla_def), '%Y-%m-%d %H:%M:%S')
                        new_sla = datetime.datetime.strptime(str(now + timedelta(days = day, hours=hour, minutes=minute)), '%Y-%m-%d %H:%M:%S')
                        if now > sla and ticket.stage_id.name != "solved" and ticket.is_escalate == False:
                            if ticket.count_escale == 0:
                                ticket.user_id = assign.escalate
                                ticket.sla_deadline = new_sla
                                ticket.is_escalate = False
                                ticket.count_escale += 1
                            else:
                                if ticket.count_escale == 1:
                                    ticket.user_id = assign.escalate1
                                    ticket.sla_deadline = new_sla
                                    ticket.is_escalate = True  
                                    ticket.count_escale += 1
                                else:
                                    ticket.user_id = None
                                    ticket.sla_deadline = new_sla
                                    ticket.is_escalate = True  
                                    ticket.count_escale = 1

    
   
class HelpdeskTicketTypeA(models.Model):
    _inherit = 'helpdesk.ticket.type'
    
    categories = fields.Selection([
        ('enquiry', 'Enquiry')
        , ('request', 'Request')
        , ('complaints', 'Complaints')
        , ('feedback', 'Feedback')
        , ('recommendations', 'Recommendations')
        ], string='Category', required=True, help="the subtypes linked to the type of helpdesk")
    team = fields.Many2one('helpdesk.team', string='Team ', required=True)  

class HelpdeskTicketslaA(models.Model):
    _inherit = 'helpdesk.sla'
    
    categories = fields.Char(string='Category', readonly=True , compute='onchange_cat')
    time_minutes = fields.Integer('Minutes', default=0, required=True, help="Minutes to reach given stage based on ticket creation date")

    @api.depends('ticket_type_id')
    def onchange_cat(self):
        self.categories = self.ticket_type_id.categories 
        
    @api.onchange('time_minutes')
    def _onchange_time_minutes(self):
        if self.time_minutes >= 60:
            self.time_hours += self.time_minutes / 60
            self.time_minutes = self.time_minutes % 60     


class ResourceCalendar1(models.Model):
    _inherit = "resource.calendar" 

    def plan_minutes(self, minutes, day_dt, compute_leaves=False, domain=None, resource=None):
        day_dt, revert = make_aware(day_dt)
        # which method to use for retrieving intervals
        if compute_leaves:
            get_intervals = partial(self._work_intervals, domain=domain, resource=resource)
        else:
            get_intervals = self._attendance_intervals

        if minutes >= 0:
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt + delta * n
                for start, stop, meta in get_intervals(dt, dt + delta):
                    interval_minutes = (stop - start).total_seconds() / 60
                    if minutes <= interval_minutes:
                        return revert(start + timedelta(minutes=minutes))
                    minutes -= interval_minutes
            return False
        else:
            minutes = abs(minutes)
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt - delta * n
                for start, stop, meta in reversed(get_intervals(dt - delta, dt)):
                    interval_minutes = (stop - start).total_seconds() / 60
                    if minutes <= interval_minutes:
                        return revert(stop - timedelta(minutes=minutes))
                    minutes -= interval_minutes
            return False 
            
    def plan_hours(self, hours, day_dt, minute, compute_leaves=False, domain=None, resource=None):
        day_dt, revert = make_aware(day_dt)
        # which method to use for retrieving intervals
        #if minute >= 0:
        
        if compute_leaves:
            get_intervals = partial(self._work_intervals, domain=domain, resource=resource)
        else:
            get_intervals = self._attendance_intervals
        if hours >= 0:
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt + delta * n
                #_logger.info("hours=== '" + str(hours) + "' ok !")               
                for start, stop, meta in get_intervals(dt, dt + delta):
                    minute_to_second = minute / 60
                    #hours = hours+minute_to_second
                    interval_hours = ((stop - start).total_seconds() / 3600)
                    # _logger.info("stop=== '" + str(stop) + "' ok !")                   
                    if hours <= interval_hours:
                        #_logger.info("revert=== '" + str(revert(start + timedelta(hours=hours, minutes=minute))) + "' ok !")
                        _logger.info("start=== '" + str(start) + "' ok !")
                        _logger.info("stop=== '" + str(stop) + "' ok !")
                        _logger.info("hours et minute === '" + str(timedelta(hours=hours, minutes=minute)) + "' ok !")
                        _logger.info("minutes=== '" + str(timedelta(minutes=minute)) + "' ok !")    
                        _logger.info("revert=== '" + str(revert(start + timedelta(hours=hours, minutes=minute))) + "' ok !")      
                        return revert(start + timedelta(hours=hours, minutes=minute))
                    hours -= interval_hours
            return False
        else:
            hours = abs(hours)
            delta = timedelta(days=14)
            for n in range(100):
                dt = day_dt - delta * n
                for start, stop, meta in reversed(get_intervals(dt - delta, dt)):
                    minute_to_second = minute / 60
                    #hours = hours+minute_to_second
                    interval_hours = (stop - start).total_seconds() / 3600
                    if hours <= interval_hours:
                        return revert(stop - timedelta(hours=hours, minutes=minute))
                    hours -= interval_hours
            return False

        

class HelpdeskSLAStatus(models.Model):
    _inherit = 'helpdesk.sla.status'            

    @api.depends('ticket_id.create_date', 'sla_id')
    def _compute_deadline(self):
        for status in self:
            deadline = status.ticket_id.create_date
            working_calendar = status.ticket_id.team_id.resource_calendar_id
            if not working_calendar:
                status.deadline = deadline
                continue
            if status.sla_id.time_days > 0:
                deadline = working_calendar.plan_days(status.sla_id.time_days + 1, deadline, compute_leaves=True)
                create_dt = status.ticket_id.create_date
                _logger.info("create_dt=== '" + str(create_dt) + "' ok !")
                deadline = deadline.replace(hour=create_dt.hour, minute=create_dt.minute, second=create_dt.second, microsecond=create_dt.microsecond)
            # if status.sla_id.time_hours > 0:
                # deadline = deadline.replace(hour=status.sla_id.time_hours + 1)
            # status.deadline = working_calendar.plan_minutes(status.sla_id.time_minutes, deadline, compute_leaves=True)                
            status.deadline = working_calendar.plan_hours(status.sla_id.time_hours, deadline, status.sla_id.time_minutes, compute_leaves=True)



class HelpdeskTeamA(models.Model):
    _inherit = 'helpdesk.team' 


    escalate = fields.Many2one('res.users', string='Level 1',required=True)
    escalate1 = fields.Many2one('res.users', string='Level 2',required=True)           
    # delay = fields.Many2one('res.users', string='Level 2',required=True)           