# browsershots.org - Test your web design in different browsers
# Copyright (C) 2007 Johann C. Rocholl <johann@browsershots.org>
#
# Browsershots is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Browsershots is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
Request models.
"""

__revision__ = "$Rev$"
__date__ = "$Date$"
__author__ = "$Author$"

from datetime import datetime, timedelta
import os
from xmlrpclib import Fault
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.timesince import timesince, timeuntil
from django.utils.text import capfirst
from django.contrib.auth.models import User
from django.template.defaultfilters import filesizeformat
from shotserver04.websites.models import Website
from shotserver04.platforms.models import Platform
from shotserver04.factories.models import Factory
from shotserver04.browsers.models import BrowserGroup, Browser
from shotserver04.features.models import Javascript, Java, Flash
from shotserver04.screenshots.models import Screenshot
from shotserver04.screenshots import storage
from shotserver04.common import lock_timeout
from shotserver04.common.preload import preload_foreign_keys


class RequestGroup(models.Model):
    """
    Common options for a group of screenshot requests.
    """

    website = models.ForeignKey(Website,
        verbose_name=_('website'), raw_id_admin=True)
    width = models.IntegerField(
        _('screen width'), null=True, blank=True)
    height = models.IntegerField(
        _('screen height'), null=True, blank=True)
    bits_per_pixel = models.IntegerField(
        _('bits per pixel'), null=True, blank=True)
    javascript = models.ForeignKey(Javascript,
        verbose_name=_('Javascript'), blank=True, null=True)
    java = models.ForeignKey(Java,
        verbose_name=_('Java'), blank=True, null=True)
    flash = models.ForeignKey(Flash,
        verbose_name=_('Flash'), blank=True, null=True)
    user = models.ForeignKey(User,
        verbose_name=_('submitter'), blank=True, null=True)
    ip = models.IPAddressField(
        _('IP'))
    submitted = models.DateTimeField(
        _('submitted'), auto_now_add=True)
    expire = models.DateTimeField(
        _('expire'))

    class Admin:
        fields = (
            (None, {'fields': (
            'website',
            ('width', 'bits_per_pixel'),
            ('javascript', 'java', 'flash'),
            'user', 'expire',
            )}),
            )
        list_display = ('__unicode__', 'width',
                        'javascript', 'java', 'flash',
                        'user', 'ip')
        search_fields = ('website__url', )
        date_hierarchy = 'submitted'

    class Meta:
        verbose_name = _('request group')
        verbose_name_plural = _('request groups')
        ordering = ('-submitted', )

    def __unicode__(self):
        """
        Get string representation.
        """
        return u'%s %d' % (capfirst(_("screenshot request group")),
                           self.index())

    def get_absolute_url(self):
        """
        Get absolute URL.
        """
        return '/requests/%d/' % self.id

    def is_pending(self):
        """True if there are pending screenshot requests in this group."""
        return self.expire > datetime.now() and self.request_set.filter(
            screenshot__isnull=True).count()

    def time_since_submitted(self):
        """Human-readable formatting of interval since submitted."""
        return '<li>%s</li>' % (
            capfirst(_("submitted %(interval)s ago")) %
            {'interval': timesince(self.submitted)})

    def time_until_expire(self):
        """
        Human-readable formatting of interval before expiration.
        """
        now = datetime.now()
        remaining = self.expire - now
        almost_fresh = remaining >= timedelta(minutes=29, seconds=50)
        if almost_fresh:
            remaining = timedelta(minutes=30)
        interval = timeuntil(now + remaining, now)
        text = capfirst(_("expires in %(interval)s")) % {'interval': interval}
        if not almost_fresh:
            text = """
<form action="/requests/extend/" method="post">
<div>
%s
<input type="hidden" name="request_group_id" value="%d" />
<input type="submit" name="submit" value="%s" />
</div>
</form>
""".strip() % (text, self.id, unicode(capfirst(_("extend"))))
        return '<li>%s</li>' % text

    def options(self):
        """
        Human-readable output of requested options.
        """
        result = []
        for attr in ('javascript', 'java', 'flash',
                     'width', 'bits_per_pixel'):
            option = getattr(self, attr)
            if option is None:
                continue
            name = self._meta.get_field(attr).verbose_name
            if attr == 'width':
                result.append(_("%(width)d pixels wide") %
                              {'width': option})
            elif attr == 'bits_per_pixel':
                result.append(_("%(color_depth)d bits per pixel") %
                              {'color_depth': option})
            else:
                result.append(u'%s %s' % (name, option))
        if not result:
            return ''
        return '<li>%s</li>' % ', '.join(result)

    def preload_cache(self):
        """
        Load database objects to save many SQL queries later.
        """
        if not hasattr(self, '_browser_groups_cache'):
            self._browser_groups_cache = BrowserGroup.objects.all()
        if not hasattr(self, '_browsers_cache'):
            self._browsers_cache = Browser.objects.all()
            preload_foreign_keys(self._browsers_cache,
                browser_group=self._browser_groups_cache)
        if not hasattr(self, '_factories_cache'):
            self._factories_cache = Factory.objects.all()
            preload_foreign_keys(self._factories_cache,
                operating_system=True)

    def previews(self):
        """
        Thumbnails of screenshots for this request group.
        """
        screenshots = []
        requests = self.request_set.filter(screenshot__isnull=False)
        # Preload browsers and factories from cache.
        self.preload_cache()
        preload_foreign_keys(requests,
            screenshot__browser=self._browsers_cache)
        preload_foreign_keys(requests,
            screenshot__factory=self._factories_cache)
        total_bytes = sum([
            os.path.getsize(storage.png_filename(request.screenshot.hashkey))
            for request in requests])
        # Get screenshots and sort by id.
        screenshots = [(request.screenshot_id, request.screenshot)
                       for request in requests]
        if screenshots:
            screenshots.sort()
            max_height = max([screenshot.height * 80 / screenshot.width
                              for index, screenshot in screenshots])
            result = [screenshot.preview_div(height=max_height, caption=True)
                      for index, screenshot in screenshots]
            if len(screenshots) > 1:
                result.append(self.zip_link(len(screenshots), total_bytes))
            return '\n'.join(result)
        elif self.is_pending():
            return u'<p class="admonition hint">%s<br />\n%s</p>' % (
_("Your screenshots will appear here when they are uploaded."),
bracket_link(self.website.get_absolute_url(),
_("[Reload this page] or bookmark it and come back later.")))
        else:
            hint = _(u"Your screenshot requests have expired.")
            return u'<p class="admonition warning">%s</p>' % hint

    def queue_overview(self):
        """
        Quick overview of queuing screenshots requests.
        """
        parts = []
        requests = self.request_set.all()
        count = requests.count()
        parts.append(_("%(count)d browsers selected") % locals())
        queuing = requests.filter(screenshot__isnull=True)
        count = queuing.filter(factory__isnull=False,
                               browser__isnull=True).count()
        if count:
            parts.append(', ' + _("%(count)d starting") % locals())
        count = queuing.filter(browser__isnull=False).count()
        if count:
            parts.append(', ' + _("%(count)d loading") % locals())
        count = requests.filter(screenshot__isnull=False).count()
        if count:
            parts.append(', ' + _("%(count)d uploaded") % locals())
        parts.append(u' (<a href="%s">%s</a>)' % (
            self.get_absolute_url(), capfirst(_("details"))))
        return u"<li>%s</li>" % ''.join(parts)

    def index(self):
        """
        Get the number among all request groups for the same website.
        """
        if not hasattr(self, '_index'):
            self._index = RequestGroup.objects.filter(
                id__lte=self.id, website=self.website).count()
        return self._index

    def zip_filename(self):
        """Filename for ZIP file with screenshots."""
        return '-'.join((
            self.submitted.strftime('%y%m%d-%H%M%S'),
            self.website.domain.name,
            '%d.zip' % self.id,
            ))

    def zip_link(self, count=None, bytes=None):
        """
        Link to ZIP file with screenshots.
        """
        if count is None:
            text = unicode(capfirst(_("download all screenshots")))
        else:
            text = unicode(capfirst(
                _("download %(count)d screenshots") % locals()))
        if bytes is not None:
            text += ' (%s)' % filesizeformat(bytes).replace(' ', '&nbsp;')
        return u'<p><a href="/screenshots/%s">%s</a></p>' % (
            self.zip_filename(), text)


class Request(models.Model):
    """
    Request for a screenshot of a specified browser.
    Contains state during processing.
    """

    request_group = models.ForeignKey(RequestGroup,
        verbose_name=_('request group'), raw_id_admin=True)
    platform = models.ForeignKey(Platform,
        verbose_name=_('platform'))
    browser_group = models.ForeignKey(BrowserGroup,
        verbose_name=_('browser group'))
    major = models.IntegerField(
        _('major'), blank=True, null=True)
    minor = models.IntegerField(
        _('minor'), blank=True, null=True)
    priority = models.IntegerField(
        _('priority'))
    factory = models.ForeignKey(Factory,
        verbose_name=_('factory'), blank=True, null=True)
    locked = models.DateTimeField(
        _('locked'), blank=True, null=True)
    browser = models.ForeignKey(Browser,
        verbose_name=_('browser'), raw_id_admin=True,
        blank=True, null=True)
    redirected = models.DateTimeField(
        _('redirected'), blank=True, null=True)
    screenshot = models.ForeignKey(Screenshot,
        verbose_name=_('screenshot'), raw_id_admin=True,
        blank=True, null=True)

    class Admin:
        fields = (
            (None, {'fields': (
            'request_group',
            'platform',
            ('browser_group', 'major', 'minor'),
            'priority',
            )}),
            )
        list_display = ('browser_group', 'major', 'minor',
                        'platform', 'priority')
        list_filter = ('browser_group', 'platform')

    class Meta:
        verbose_name = _('request')
        verbose_name_plural = _('requests')

    def __unicode__(self):
        return u'%s on %s' % (self.browser_string(), self.platform.name)

    def browser_string(self):
        """
        Human-readable formatting of requested browser.
        """
        result = [self.browser_group.name]
        if self.major is not None:
            result.append(u' ' + unicode(self.major))
            if self.minor is not None:
                result.append(u'.' + unicode(self.minor))
        return u''.join(result)

    def status(self):
        """
        Human-readable output of request status.
        """
        if self.screenshot_id is not None:
            return _("uploaded")
        if self.locked and self.locked < lock_timeout():
            return _("failed")
        if self.redirected:
            return _("loading")
        if self.locked:
            return _("starting")
        return ''

    def check_factory_lock(self, factory):
        """
        Check that the request is locked by this factory.
        """
        if self.factory is None:
            raise Fault(409,
                u"Request %d was not locked." % self.id)
        if factory != self.factory:
            raise Fault(423,
                u"Request %d was locked by factory %s." %
                (self.id, self.factory.name))


def bracket_link(href, text):
    """Replace square brackets with a HTML link."""
    return text.replace('[', u'<a href="%s">' % href).replace(']', '</a>')