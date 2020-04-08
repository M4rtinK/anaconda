#
# Copyright (C) 2020  Red Hat, Inc.
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
# Red Hat Author(s): Martin Kolman <mkolman@redhat.com>
#
import time
import unittest
from unittest.mock import patch, Mock
from threading import Thread

from dasbus.client.observer import DBusObserverError

from pyanaconda.modules.subscription.service_observer import ServiceObserver

class ServiceObserverTestCase(unittest.TestCase):
    """Test the service observer."""

    def _thread_success(self, observer):
        """Request a proxy from the observer and expect success."""
        proxy = observer.get_proxy()
        self.assertIsNotNone(proxy)

    def _thread_failure(self, observer):
        """Request a proxy from the observer and expect failure."""
        with self.assertRaises(DBusObserverError):
            observer.get_proxy()

    @patch("pyanaconda.core.util.start_service")
    def service_started_in_time_test(self, start_service):
        """Test that a service_observer - service started in time."""

        dbus = Mock()
        observer = ServiceObserver(dbus, "my.test.module", "test.service", 1)

	# proxy and timer should be none at this point
        self.assertIsNone(observer._proxy)
        self.assertIsNone(observer._timer)

        # start a couple threads and let them wait for the proxy the
        # become available
        thread1 = Thread(target=self._thread_success, args=[observer], daemon=True)
        thread2 = Thread(target=self._thread_success, args=[observer], daemon=True)
        thread3 = Thread(target=self._thread_success, args=[observer], daemon=True)
        thread1.start()
        thread2.start()
        thread3.start()

        # give the threads some time to run
        time.sleep(0.01)

        # check the system unit was started once
        start_service.called_once_with("test.service")

        # timer should exist now as well
        self.assertIsNotNone(observer._timer)

        # make the service available
        # - this should turn off the timer
        # - and also make the threads terminate as their
        #   join() on the timer will stop blocking
        observer.service_available.emit()

        # give the threads some time to run
        time.sleep(0.01)

        # check the proxy
        dbus.get_proxy.assert_called_with("my.test.module", "/my/test/module")
        self.assertIsNotNone(observer._proxy)

        # and finally, get_proxy() calls should not block
        # and should return a proxy that is not None
        self.assertIsNotNone(observer.get_proxy())

    @patch("pyanaconda.core.util.start_service")
    def service_timed_out_test(self, start_service):
        """Test that a service_observer - service timed out."""

        dbus = Mock()
        observer = ServiceObserver(dbus, "my.test.module", "test.service", 0.1)

	# proxy and timer should be none at this point
        self.assertIsNone(observer._proxy)
        self.assertIsNone(observer._timer)

        # start a couple threads and let them wait for the proxy the
        # become available
        thread1 = Thread(target=self._thread_failure, args=[observer], daemon=True)
        thread2 = Thread(target=self._thread_failure, args=[observer], daemon=True)
        thread3 = Thread(target=self._thread_failure, args=[observer], daemon=True)
        thread1.start()
        thread2.start()
        thread3.start()

        # give the threads some time to run
        time.sleep(0.01)

        # check the system unit was started once
        start_service.called_once_with("test.service")

        # timer should exist now as well
        self.assertIsNotNone(observer._timer)

        # do not make the service available and wait for the
        # timer to time out
        time.sleep(0.15)

        # check the proxy
        dbus.get_proxy.assert_not_called()
        self.assertIsNone(observer._proxy)

        # service should be marked as unavailable
        self.assertFalse(observer.is_service_available)

        # and finally, get_proxy() calls should not block
        # and should throw DBusObserverError immediately
        with self.assertRaises(DBusObserverError):
            observer.get_proxy()
