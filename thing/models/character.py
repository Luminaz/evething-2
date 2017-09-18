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

from django.db import models
from django.db.models import Sum
from datetime import datetime

from thing.models.corporation import Corporation


class Character(models.Model):
    id = models.IntegerField(primary_key=True)

    name = models.CharField(max_length=64)
    corporation = models.ForeignKey(Corporation, blank=True, null=True)

    class Meta:
        app_label = 'thing'
        ordering = ('name',)

    def __unicode__(self):
        return self.name


    @staticmethod
    def get_or_create(id):
        from thing.esi import ESI

        db_char = Character.objects.filter(id=id)
        if len(db_char) == 0:
            api = ESI()
            char = api.get("/characters/%s/" % id)
            db_char = Character(
                id=id,
                name=char['name'],
                corporation=Corporation.get_or_create(char['corporation_id'])
            )
            db_char.save()
        else:
            db_char = db_char[0]

        return db_char


    def is_training(self):
        return self.skillqueue.filter(
            end_time__gte=datetime.utcnow()
        ).count() > 0


    @models.permalink
    def get_absolute_url(self):
        return ('character', (), {'character_name': self.name, })

    def get_jc_slots(self):
        return self.skills.filter(skill_id__in=[24242, 33407]).\
            aggregate(
                jc_slots=Sum('level')
            )['jc_slots']

    def get_total_skill_points(self):
        from thing.models.characterskill import CharacterSkill
        return CharacterSkill.objects.filter(character=self).aggregate(total_sp=Sum('points'))['total_sp']
