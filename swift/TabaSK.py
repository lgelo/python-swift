#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime, re
import MT940

class MT940TransactionSK(MT940.MTTransaction):
    __slots__ = ['vs', 'ks', 'ss', 'message', 'other_account', 'other_name']


class MT940StatementSK(MT940.MT940Statement):
    _transaction_class = MT940TransactionSK

# todo
class MT942StatementSK(MT940.MT942Statement):
    pass

class TabaParser940(MT940.MT940Parser):

    _statement_class = MT940StatementSK
    _header = None
    _trailer = '-'

    RE20 = re.compile("^MC940([0-9]{6})00000$")
    RE25 = re.compile("^SK([0-9]{2})([0-9]{4})([0-9]{6})([0-9]{10})$")

    def __init__(self):
        super(TabaParser940, self).__init__()
        self._name = 'TaBaSK MT942 Parser'

    def _field_25(self, value, subfields=[]):
        m = super(TabaParser940, self)._field_25(value, subfields)
        self.current_statement.update(account = "%s-%s/%s" % (m.group(2), m.group(3), m.group(4)))

    def _field_86(self, value, subfields=[]):
        for line in subfields:
            if line.startswith('?24'):
                self.current_statement.update_transaction(message=line[3:])
            elif line.startswith('?31'):
                m = self.RE25.match(line[3:])
                if m:
                    self.current_statement.update_transaction(other_account = "%s-%s/%s" % 
                                                              (m.group(2), m.group(3), m.group(4)))
                else:
                    pass
                    #raise InvalidFieldValue("Invalid field 86:31 value `%s`" % line[3:])
            elif line.startswith('?32'):
                self.current_statement.update_transaction(other_name=line[3:])
            elif line.startswith('?60'):
                (vs, ss, ks) = (None, None, None)
                symbols = filter(None, line[3:].split('/'))
                for symbol in symbols:
                    if symbol.startswith('VS'):
                        vs = symbol[3:] or None
                    elif symbol.startswith('SS'):
                        ss = symbol[3:] or None
                    elif symbol.startswith('KS'):
                        ks = symbol[3:] or None
                    else:
                        pass
                        #raise InvalidFieldValue("Invalid field 86:60 value `%s`" % line[3:])

                self.current_statement.update_transaction(vs = vs, ss = ss, ks = ks)

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

