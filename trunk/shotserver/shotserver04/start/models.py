# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.

"""
Start page models.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

from django.db import models


class NewsItem(models.Model):
    """
    RSS news entry for caching in the database.
    """
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200)
    pubdate = models.DateTimeField()

    class Admin:
        pass

    class Meta:
        ordering = ('-pubdate', 'url')

    def __unicode__(self):
        return self.title

    def get_absolute_url(self):
        """Get absolute URL."""
        return self.url
