from django.db import models
from ldap3 import Server, Connection, ALL_ATTRIBUTES
import re

class Census(models.Model):
    voting_id = models.PositiveIntegerField()
    voter_id = models.PositiveIntegerField()

    def get_all_objects(self): 
        queryset=self._meta.model.objects.all() 
        return queryset

    class Meta:
        unique_together = (('voting_id', 'voter_id'),)


class LdapCensus:
    def ldapConnection(self, urlServer, auth, psw):
        server = Server(urlServer)
        conn = Connection(server, auth, psw, auto_bind=True)
        return conn

    def ldapGroups(self, LdapUrl, auth, psw, branch):
        conn = LdapCensus().ldapConnection(LdapUrl, auth, psw)
        conn.search(search_base=branch, search_filter='(objectclass=*)', attributes=[ALL_ATTRIBUTES])
        ldapList = []
        for entries in conn.entries:
            text = str(entries)
            group = re.findall('uid=(.+?),', text, re.DOTALL)
            for element in group:
                if group and ldapList.count(element) == 0:ldapList.append(element)
        return ldapList
