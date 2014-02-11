#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, re
from decimal import Decimal

from . import JSONObject

class RunawayField(Exception):
    pass

class NoTransaction(Exception):
    pass

class InvalidFieldValue(Exception):
    pass

class MissingFieldParser(Exception):
    pass

class InvalidSwift(Exception):
    pass

class UnfinishedStatement(Exception):
    pass

class MTTransaction(JSONObject):

    __slots__ = ['value_date', 'entry_date', 'amount', 'sign','type_code', 'cust_ref', 'bank_ref']

    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, None)

    def update(self, *args, **kwargs):
        for key, val in kwargs.items():
            if args and args[0]:
                old_val = getattr(self, key, '')
                setattr(self, key, str(old_val) + str(val))
            else:
                setattr(self, key, val)

class MTStatement(JSONObject):

    __slots__ = ['transaction_ref', 'number', 'account', '_transactions']
    _transaction_class = MTTransaction

    def __init__(self, tref):
        self.transaction_ref = tref
        self.number = None
        self.account = None
        self._transactions = []

    def update(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
            
    def transactions(self):
        return self._transactions

    def add_transaction(self, **kwargs):
        self._current_transaction = self._transaction_class()
        self._current_transaction.update(**kwargs)
        self._transactions.append(self._current_transaction)

    def update_transaction(self, *args, **kwargs):
        if self._current_transaction:
            self._current_transaction.update(*args, **kwargs)
        else:
            raise NoTransaction("No current transaction defined")

    def current_transaction(self):
        return self._current_transaction        

    def to_json(self):
        json = super(MTStatement, self).to_json()
        json['transactions'] = list(s.to_json() for s in self._transactions)
        return json

    #def __str__(self):
    #    return ''.join('%s: %s\n' % (k, getattr(self,k,'')) for k in self._attrs() if not k.startswith('_') )

class MT940Statement(MTStatement):

    __slots__ = ['opening_balance', 'closing_balance', 'closing_available_balance', ]

    def __init__(self, tref):
        super(MT940Statement, self).__init__(tref)
        self.opening_balance = (None, None, None)
        self.closing_balance = (None, None, None)
        self.closing_available_balance = (None, None, None)


class MT942Statement(MTStatement):

    __slots__ = ['date', 'credit_transactions', 'debit_transactions',  
                 'credit_minimum_amount', 'debit_minimum_amount', ]

    def __init__(self, tref):
        super(MT942Statement, self).__init__(tref)
        self.date = None
        self.credit_transactions = (None, None, None)
        self.debit_transactions = (None, None, None)
        self.credit_minimum_amount = (None, None)
        self.debit_minimum_amount = (None, None)

class MTStatementParser(object):

    _header = '{1:'
    _trailer = '-}'
    _encoding = None
    _statement_class = MTStatement

    RE_HEADER = re.compile("^\{1\:F01([A-Z]{12})([0-9]{4})([0-9]{6})\}"
                      "\{2\:I([0-9]{3})([A-Z]{12})([A-Z])\}"
                      "\{3\:(\{[0-9]{3}\:.+\})*}"
                      "\{4\:$"
                    )

    RE_FIELD = re.compile("^\:([0-9A-Z]+)\:(.*)$")
    RE_20 = re.compile("^(.{1:16})$")
    RE_25 = re.compile("^(.{1:35})$")
    RE_28C = re.compile("^([0-9]{1,4})(\/([0-9]{1,5}))?$")
    RE_61 = re.compile("^([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})([0-9]{2})"
                      "([CD])([0-9,]+)([A-Z]{4})([\w\/\. -]{0,16})"
                      "(\/\/([\w\/\. -]{0,16}))?$")
    
    def __init__(self):
        self._name = 'MTStatementParser'
        self.current_statement = None   
        self.statements = []

    def parse(self, lines=[]):

        statement_lines = []

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if self._encoding:
                line = line.decode(self._encoding).encode('utf-8')
            if self._header and line.startswith(self._header):
                self._parse_header(line)       
            elif line.startswith(self._trailer):
                self._parse_statement(statement_lines)
                self._statement_parsed()
                statement_lines = []
            else:
                statement_lines.append(line)

        if len(statement_lines):
            raise UnfinishedStatement("Statement trailer `%s` not found." % self._trailer)

        return self.statements

    def _parse_statement(self, lines=[]):

        field = (None, None, [])

        for line in lines:
            match = self.RE_FIELD.match(line)
            if match:
                if field[0]:
                    try: 
                        field_parser = getattr(self, '_field_%s' % field[0].lower())
                    except AttributeError:
                        raise MissingFieldParser("Field parser %s not implemented" % field[0])
                    else:
                        if not (field[0] == '20' or self.current_statement):
                            raise RunawayField("Runaway field %c `%s`" % (field[0], value))

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

            
    def _parse_header(self, line):
        if not self.RE_HEADER.match(line):
            raise InvalidSwiftHeader("Invalid swift header `%s`" % line)

    def _statement_parsed(self):
        pass

    def _field_20(self, value, subfields=[]):
        m = self.RE_20.match(value)
        if m:
            self.current_statement = self._statement_class(m.group(1))
            self.statements.append(self.current_statement)
        else:
            raise InvalidFieldValue("Invalid field 20 value `%s`" % value)
        return m


    def _field_25(self, value, subfields=[]):
        m = self.RE_25.match(value)
        if m:
            self.current_statement.account = m.group(1)
        else:
            raise InvalidFieldValue("Invalid field 25 value `%s`" % value)
        return m


    def _field_28c(self, value, subfields=[]):
        m = self.RE_28C.match(value)
        if m:
            self.current_statement.number = m.group(1)
        else:
            raise InvalidFieldValue("Invalid field 28C value `%s`" % value)
        return m


    def _field_61(self, value, subfields=[]):
        m = self.RE_61.match(value)
        if m:
            value_date = datetime.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
            entry_date = datetime.date(value_date.year, int(m.group(4)), int(m.group(5)))
            amount = Decimal(m.group(7).replace(',','.'))
            sign = '-' if m.group(6) == 'D' else '+'
            type_code = m.group(8)
            cust_ref = m.group(9)
            bank_ref = m.group(10)
            self.current_statement.add_transaction(value_date = value_date, entry_date = entry_date, 
                    amount = amount, sign = sign, type_code = type_code, cust_ref = cust_ref, bank_ref = bank_ref)
        else:
            raise InvalidFieldValue("Invalid field 61 value `%s`" % value)
        return m

    def _field_86(self, value, subfields=[]):
        raise MissingFieldParser("Please define parser for field 86")


class MT940Parser(MTStatementParser):

    _statement_class = MT940Statement

    # matches 60F, 60M, 62F, 62M, 64, 65
    RE_6XX = re.compile("^([CD])([0-9]{2})([0-9]{2})([0-9]{2})([A-Z]{3})([0-9,]+)$")


    def _field_6xx_balance(self, value, field):
        m = self.RE_6XX.match(value)
        if m:
            value_date = datetime.date(2000 + int(m.group(2)), int(m.group(3)), int(m.group(4)))
            currency = m.group(5)
            amount = Decimal(m.group(6).replace(',', '.'))
            if m.group(1) == 'D':
                amount = -amount
            if field.startswith('60'):
                self.current_statement.opening_balance= (amount, currency, value_date)
            elif field.startswith('62'):
                self.current_statement.closing_balance = (amount, currency, value_date)
            elif field.startswith('64'):
                self.current_statement.closing_available_balance = (amount, currency, value_date)
            else:
                raise InvalidFieldValue("Invalid field %s value `%s`" % (field, value))
        else:
            raise InvalidFieldValue("Invalid field %s value `%s`" % (field, value))
    
        return m


    def _field_60f(self, value, subfields=[]):
        return self._field_6xx_balance(value, '60f')


    def _field_62f(self, value, subfields=[]):
        return self._field_6xx_balance(value, '62f')


    def _field_64(self, value, subfields=[]):
        return self._field_6xx_balance(value, '64')


class MT942Parser(MTStatementParser):

    _statment_class = MT942Statement

    RE_13D = re.compile("^([0-9]{10})([+-])([0-9]{4})$")
    RE_34F = re.compile("^([A-Z]{3})([CD])?([0-9,]+)$")
    RE_90X = re.compile("^([0-9]{1,5})([A-Z]{3})([0-9,]+)$")

    # todo fix
    def _field_13d(self, value, subfields=[]):
        m = self.RE_13D.match(value)
        if m:
            try:
                self.current_statement.date = datetime.datetime.strptime(m.group(0),"%y%m%d%H%M%z")  
            except ValueError:
                raise InvalidFieldValue("Invalid field 13D value `%s`" % value)
        else:
            raise InvalidFieldValue("Invalid field 13D value `%s`" % value)
        return m


    def _field_90c(self, value, subfields=[]):
        m = self.RE_90X.match(value)
        if m:
            self.credit_transactions = (m.group(1), m.group(2), m.group(2))
        else:
            raise InvalidFieldValue("Invalid field 90C value `%s`" % value)
        return m

    def _field_90d(self, value, subfields=[]):
        m = self.RE_90X.match(value)
        if m:
            self.debit_transactions = (m.group(1), m.group(2), m.group(2))
        else:
            raise InvalidFieldValue("Invalid field 90D value `%s`" % value)
        return m


    def _field_34f(self, value, subfields=[]):
        m = self.RE_34F.match(value)
        if m:
            # first occurence => debit, second occurence => credit (or according to indicator)
            if m.group(2) == 'C' or self.current_statement.debit_minimum_amount[0]:
                self.current_statement.credit_minimum_amount = (m.group(1),m.group(3))
            else:
                self.current_statement.debit_minimum_amount = (m.group(1),m.group(3))                    
        else:
            raise InvalidFieldValue("Invalid field 34F value `%s`" % value)
        return m