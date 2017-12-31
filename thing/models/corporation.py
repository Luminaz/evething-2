# ------------------------------------------------------------------------------
# Copyright (c) 2010-2013, EVEthing team
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
#     Redistributions of source code must retain the above copyright notice, this
#       list of conditions and the following disclaimer.
#     Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGE.
# ------------------------------------------------------------------------------

from datetime import datetime, timedelta

from django.db import models
from django.db.models import Sum

from thing.models.alliance import Alliance


class Corporation(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=64)
    ticker = models.CharField(max_length=5, default='')

    alliance = models.ForeignKey(Alliance, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, default=datetime(0001, 1, 1, 1, 0))

    division1 = models.CharField(max_length=64, default='')
    division2 = models.CharField(max_length=64, default='')
    division3 = models.CharField(max_length=64, default='')
    division4 = models.CharField(max_length=64, default='')
    division5 = models.CharField(max_length=64, default='')
    division6 = models.CharField(max_length=64, default='')
    division7 = models.CharField(max_length=64, default='')

    class Meta:
        app_label = 'thing'
        ordering = ('name',)

    def __unicode__(self):
        return self.name

    def get_total_balance(self):
        return self.corpwallet_set.aggregate(Sum('balance'))['balance_sum']


    @staticmethod
    def get_or_create(corporation_id):
        from thing.esi import ESI

        corporation = Corporation.objects.filter(id=corporation_id)
        if len(corporation) == 0:
            api = ESI()
            corporation = api.get("/v4/corporations/%s/" % corporation_id)
            db_corporation = Corporation(
                id=corporation_id,
                name=corporation['corporation_name']
                )

            if "alliance_id" in corporation:
                db_corporation.alliance = Alliance.get_or_create(corporation['alliance_id'])
            else:
                db_corporation.alliance = None

            db_corporation.save()

            return db_corporation
        else:
            db_corporation = corporation[0]
            if db_corporation.last_updated < datetime.now() - timedelta(days=2):
                api = ESI()
                corporation = api.get("/v4/corporations/%s/" % corporation_id)
                db_corporation.name = corporation['corporation_name']

                if "alliance_id" in corporation:
                    db_corporation.alliance = Alliance.get_or_create(corporation['alliance_id'])
                else:
                    db_corporation.alliance = None

                db_corporation.save()
            return db_corporation


    @staticmethod
    def get_ids_with_access(user, access_mask):
        from thing.models.apikey import APIKey

        corp_apis = APIKey.objects.filter(
            user=user,
            key_type=APIKey.CORPORATION_TYPE,
            valid=True
        )

        corporation_ids = {}
        for api in corp_apis:
            if ((api.corporation_id not in corporation_ids) and
                    ((api.access_mask & access_mask) != 0)):
                corporation_ids[api.corporation_id] = api.corporation_id

        return corporation_ids
