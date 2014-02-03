#!/usr/bin/env python
# -*- coding: utf-8 -*-

from datetime import date
from decimal import Decimal
import re

class RunawayField(Exception):
    pass

class NoTransaction(Exception):
    pass

class InvalidFieldValue(Exception):
    pass

class MissingFieldParser(Exception):
    pass


class MT940Transaction(object):

    __slots__ = ['value_date', 'entry_date', 'amount', 'type_code', 'cust_ref', 'bank_ref']

    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, None)

    def update(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


class MT940Statement(object):

    __slots__ = ['transaction_ref', 'number', 'account', 'opening_balance', 'closing_balance', 
                 'closing_available_balance', 'transaction' ]

    _transaction_class = MT940Transaction

    def __init__(self, tref):
        self.transaction_ref = tref
        self.number = None
        self.account = None
        self.opening_balance = (None, None, None)
        self.closing_balance = (None, None, None)
        self.closing_available_balance = (None, None, None)
        self.transactions = []

    def add_transaction(self, **kwargs):
        self._current_transaction = self._transaction_class()
        self._current_transaction.update(**kwargs)
        self.transactions.append(self._current_transaction)

    def update_transaction(self, **kwargs):
        if self._current_transaction:
            self._current_transaction.update(**kwargs)
        else:
            raise NoTransaction("No current transaction defined")
            

class MT940Parser(object):

    _statement_class = MT940Statement

    RE20 = re.compile("^(.{1:16})$")
    RE25 = re.compile("^(.{1:35})$")
    RE28C = re.compile("^(\d{1,4})(\/(\d{1,5}))?$")
    RE61 = re.compile("^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})"
                      "([CD])([0-9,]+)([A-Z]{4})([\w\/\. -]{0,16})"
                      "(\/\/([\w\/\. -]{0,16}))?$")
    # matches 60F, 60M, 62F, 62M, 64, 65
    RE6XX = re.compile("^([CD])(\d{2})(\d{2})(\d{2})([A-Z]{3})([0-9,]+)$")
    
    def __init__(self):
        self._name = 'MT940Parser'
        self.current_statement = None   
        self.statements = []

    def parse(self, lines=[], parse_transactions = True):

        statement_lines = []

        for line in lines:
            if line.startswith(':20:'):
                statement_lines.append(line)
            elif line.startswith('-'):
                self._parse_statement(statement_lines)
                statement_lines = []
            else:
                if statement_lines:
                    statement_lines.append(line)

        return self.statements

    def _parse_statement(self, lines=[]):

        field_re = re.compile("^\:(\w+)\:(.*)$")
        field = (None, None, [])

        for line in lines:
            line = line.rstrip()
            match = field_re.match(line)
            if match:
                if field[0]:
                    try: 
                        field_parser = getattr(self, '_field_%s' % field[0].lower())
                    except AttributeError:
                        raise MissingFieldParser("Field parser %s not implemented" % field[0])
                    else:
                        field_parser(field[1], field[2])

                field = (match.group(1), match.group(2), [])
            else:
                field[2].append(line)

        if field[0]:
            try: 
                field_parser = getattr(self, '_field_%s' % field[0].lower())
            except AttributeError:
                raise NotImplementedError("Field parser %s not implemented" % field[0])
            else:
                field_parser(field[1], field[2])


    def _field_20(self, value, subfields=[]):
        m = self.RE20.match(value)
        if m:
            self.current_statement = self._statement_class(m.group(1))
            self.statements.append(self.current_statement)
        else:
            raise InvalidFieldValue("Invalid field 20 value `%s`" % value)

        return m


    def _field_25(self, value, subfields=[]):
        m = self.RE25.match(value)
        if m:
            if self.current_statement:
                self.current_statement.account = m.group(1)
            else:
                raise RunawayField("Runaway field 25 `%s`" % value)
        else:
            raise InvalidFieldValue("Invalid field 25 value `%s`" % value)

        return m


    def _field_28c(self, value, subfields=[]):
        m = self.RE28C.match(value)
        if m:
            if self.current_statement:
                self.current_statement.number = m.group(1)
            else:
                raise RunawayField("Runaway field 25 `%s`" % value)
        else:
            raise InvalidFieldValue("Invalid field 28C value `%s`" % value)

        return m


    def _field_61(self, value, subfields=[]):
        m = self.RE61.match(value)
        if m:
            value_date = date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
            entry_date = date(value_date.year, int(m.group(4)), int(m.group(5)))
            amount = Decimal(m.group(7).replace(',','.'))
            if m.group(6) == 'D':
                amount = -amount
            type_code = m.group(8)
            cust_ref = m.group(9)
            bank_ref = m.group(10)
            self.current_statement.add_transaction(value_date = value_date, entry_date = entry_date, 
                    amount= amount, type_code = type_code, cust_ref = cust_ref, bank_ref = bank_ref)
        else:
            raise InvalidFieldValue("Invalid field 61 value `%s`" % value)

        return m


    def _field_6xx_balance(self, value, field):
        m = self.RE6XX.match(value)
        if m:
            value_date = date(2000 + int(m.group(2)), int(m.group(3)), int(m.group(4)))
            currency = m.group(5)
            amount = Decimal(m.group(6).replace(',','.'))
            if m.group(1) == 'D':
                amount = -amount
            if self.current_statement:
                if field.startswith('60'):
                    self.current_statement.opening_balance= (amount, currency, value_date)
                elif field.startswith('62'):
                    self.current_statement.closing_balance = (amount, currency, value_date)
                elif field.startswith('64'):
                    self.current_statement.closing_available_balance = (amount, currency, value_date)
                else:
                    raise InvalidFieldValue("Invalid field %s value `%s`" % (field, value))
            else:
                raise RunawayField("Runaway field %s `%s`" % (field, value))

        else:
            raise InvalidFieldValue("Invalid field %s value `%s`" % (field, value))
    
        return m


    def _field_60f(self, value, subfields=[]):
        return self._field_6xx_balance(value, '60f')


    def _field_62f(self, value, subfields=[]):
        return self._field_6xx_balance(value, '62f')


    def _field_64(self, value, subfields=[]):
        return self._field_6xx_balance(value, '64')


    def _field_86(self, value, subfields=[]):
        raise MissingFieldParser("Please define parser for field 86")

