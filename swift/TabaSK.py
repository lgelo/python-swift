#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import MT940

class MT940TransactionSK(MT940.MT940Transaction):
    
    __slots__ = ['vs', 'ks', 'ss', 'message', 'other_account', 'other_name']


class MT940StatementSK(MT940.MT940Statement):

    _transaction_class = MT940TransactionSK


class TabaParser940(MT940.MT940Parser):

    _statement_class = MT940StatementSK

    RE20 = re.compile("^MC940(\d{6})00000$")
    RE25 = re.compile("^SK(\d{2})(\d{4})(\d{6})(\d{10})$")

    def __init__(self):
        super(TabaParser940, self).__init__()
        self.name = 'Tatrabanka SK'

    def _field_25(self, value, subfields=[]):
        m = super(TabaParser940, self)._field_25(value, subfields)
        self.current_statement.account = "%s-%s/%s" % (m.group(2), m.group(3), m.group(4))

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
