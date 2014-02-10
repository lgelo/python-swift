#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, re
import MT940

class MT940TransactionSK(MT940.MTTransaction):
    __slots__ = ['vs', 'ks', 'ss', 'message', 'other_account', 
                 'other_name', 'message', 'pos_number', 'other_ref']

class MT940StatementSK(MT940.MT940Statement):
    _transaction_class = MT940TransactionSK

# todo
class MT942StatementSK(MT940.MT942Statement):
    pass

class TabaParser940(MT940.MT940Parser):

    _statement_class = MT940StatementSK
    _header = None
    _trailer = '-'
    _encoding = 'ibm852'

    RE20 = re.compile("^MC940([0-9]{6})00000$")
    RE25 = re.compile("^SK([0-9]{2})([0-9]{4})([0-9]{6})([0-9]{10})$")

    def __init__(self):
        super(TabaParser940, self).__init__()
        self._name = 'TaBaSK MT942 Parser'

    def _field_25(self, value, subfields=[]):
        m = super(TabaParser940, self)._field_25(value, subfields)
        self.current_statement.update(account = "%s-%s/%s" % (m.group(3), m.group(4), m.group(2)))

    def _field_86(self, value, subfields=[]):
        statement = self.current_statement
        type_code = getattr(statement.current_transaction(), 'type_code', None)
        cust_ref = getattr(statement.current_transaction(), 'cust_ref', None)

        for line in subfields:
            if re.match('^\?\d\d$', line):
                continue
            if line.startswith('?20VS'):
                statement.update_transaction(vs=line[5:])
            elif line.startswith('?21SS'):
                statement.update_transaction(ss=line[5:])
            elif line.startswith('?22KS'):
                statement.update_transaction(ks=line[5:])
            elif line.startswith('?23POS'):
                statement.update_transaction(pos_number=line[6:])                
            elif line.startswith('?24'):
                statement.update_transaction(message = line[3:])
            elif line.startswith('?25') or line.startswith('?26') or line.startswith('?27') \
                                        or line.startswith('?28') or line.startswith('?29'):
                if line[3:]:
                    statement.update_transaction(True, message = line[3:])
            elif line.startswith('?31'):
                if cust_ref in ('DEPOSIT', 'FEES'):
                    statement.update_transaction(other_name =  line[3:])
                elif cust_ref in ('COLLECTION', 'INTER.CAPITALIS.'):
                    pass
                else:
                    m = self.RE25.match(line[3:])
                    if m:
                        statement.update_transaction(other_account = "%s-%s/%s" % 
                                                    (m.group(3), m.group(4), m.group(2)))
                    else:
                        raise MT940.InvalidFieldValue("Invalid field 86:31 value `%s`" % line[3:])
            elif line.startswith('?32'):
                statement.update_transaction(other_name=line[3:])
            elif line.startswith('?33'):
                statement.update_transaction(True, other_name=" " +line[3:])
            elif line.startswith('?38') and cust_ref not in ('COLLECTION', 'INTER.CAPITALIS.', 'DEPOSIT', 'FEES'):
                m = self.RE25.match(line[3:])
                if m:
                    statement.update(other_account = "%s-%s/%s" % (m.group(3), m.group(4), m.group(2)))
                else:
                    raise MT940.InvalidFieldValue("Invalid field 86:38 value `%s`" % line[3:])           
            elif line.startswith('?60'):
                statement.update_transaction(other_ref = line[3:])

class TabaParser942(MT940.MT942Parser):

    _statement_class = MT942StatementSK

    RE13 = re.compile("^([0-9]{10})$")
    RE20 = re.compile("^([0-9]{4})-([0-9]{2})-([0-9]{2})-([0-9]{2})\.([0-9]{2})$")
    RE25 = re.compile("^([0-9]{4})\/([0-9]{10})$")

    def __init__(self):
        super(TabaParser942, self).__init__()
        self._name = 'TaBa SK MT942 Parser'

    def _field_13(self, value, subfields=[]):
        m = self.RE13.match(value)
        if m:
            try:
              self.current_statement.date = datetime.datetime.strptime(m.group(1),"%y%m%d%H%M")  
            except ValueError:
                raise MT940.InvalidFieldValue("Invalid field %s value `%s`" % (field, value))
        else:
            raise MT940.InvalidFieldValue("Invalid field 13 value `%s`" % value)

    def _field_20(self, value, subfields=[]):
        m = super(TabaParser942, self)._field_20(value, subfields)
        self.current_statement.update(transaction_ref = m.group(0))

    def _field_25(self, value, subfields=[]):
        m = super(TabaParser942, self)._field_25(value, subfields)
        self.current_statement.update(account = "000000-%s/%s" % (m.group(2), m.group(1)))

    # todo
    def _field_86(self, value, subfields=[]):
        pass

    def _field_90c(self, value, subfields=[]):
        pass

    def _field_90d(self, value, subfields=[]):
        pass

