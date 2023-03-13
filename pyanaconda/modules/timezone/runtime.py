#
# Copyright (C) 2023 Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#
import datetime

from pyanaconda.anaconda_loggers import get_module_logger
from pyanaconda.timezone import set_system_date_time, get_all_regions_and_timezones
from pyanaconda.modules.common.task import Task
from pyanaconda.modules.timezone.constants import NTPStatus

__all__ = ["GetNTPStatusTask", "GetSystemDateTimeTask", "SetSystemDateTimeTask", "GetTimezonesTask"]

log = get_module_logger(__name__)


class GetNTPStatusTask(Task):
    """Runtime task for checking the current status of the NTP service."""

    def __init__(self):
        """Create a new task."""
        super().__init__()

    @property
    def name(self):
        return "Check status of the NTP service"

    def run(self):
        """Check the status of the NTP service."""
        log.debug("FIXME: NTP service monitoring not yet implemented!")
        ntp_status = NTPStatus.SYNCHRONIZED
        log.debug("Current NTP service status: %s", ntp_status)
        return ntp_status


class GetSystemDateTimeTask(Task):
    """Runtime task for getting ISO 8601 system date & time local to a timezone."""

    def __init__(self, timezone):
        """Create a new task.

        :param str timezone: timezone reference for the system date and time
        """
        super().__init__()
        self._timezone = timezone

    @property
    def name(self):
        return "Return system date and time"

    def run(self):
        """Return system date and time in ISO 8601 format."""
        return datetime.datetime.now(tz=self._timezone).isoformat()


class SetSystemDateTimeTask(Task):
    """Runtime task for setting system date & time in the ISO 8601 format, with timezone."""

    def __init__(self, date_time_spec, timezone):
        """Create a new task.

        :param str date_time_spec: new date & time in ISO 8601 format to be set
        :param str timezone: timezone reference for the system date and time
        """
        super().__init__()
        self._date_time_spec = date_time_spec
        self._timezone = timezone

    @property
    def name(self):
        return "Set system date and time"

    def run(self):
        """Set system date and time."""
        log.debug("Setting system time to: %s, with timezone: %s", self._date_time_spec, self._timezone)
        # first convert the ISO 8601 time string to a Python date object
        date = datetime.datetime.fromisoformat(self._date_time_spec)
        # set the date to the system
        set_system_date_time(
            year=date.year,
            month=date.month,
            day=date.day,
            hour=date.hour,
            minute=date.minute,
            tz=self._timezone
        )

class GetTimezonesTask(Task):
    """Runtime task for getting all valid timezones."""

    def __init__(self):
        """Create a new task."""
        super().__init__()

    @property
    def name(self):
        return "Return a list of all valid timezones"

    def run(self):
        """Return a list of valid timezones."""
        return get_all_regions_and_timezones()
