#
# Copyright (C) 2020  Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
import time
from threading import RLock, Timer

from pyanaconda.core import util
from pyanaconda.anaconda_loggers import get_module_logger
from dasbus.namespace import get_namespace_from_name, get_dbus_path
from dasbus.client.observer import DBusObserver, DBusObserverError

from pyanaconda.modules.common.constants.services import RHSM

log = get_module_logger(__name__)

# How long to wait for a systemd unit backed DBus service
# to become available (in seconds). This timeout is based
# on the default 90 second timeout for manual systemd unit
# activation, which is also 90 seconds.
SERVICE_ACTIVATION_TIMEOUT = 90.0
# how often to check if service became available ? (in seconds)
SERVICE_CHECK_INTERVAL = 0.1

class ServiceObserver(DBusObserver):
    """Observer of a systemd unit backed DBus service."""

    def __init__(self, message_bus, dbus_service_name, systemd_unit_name,
                 timeout=SERVICE_ACTIVATION_TIMEOUT):
        """Creates a service observer.

        The service observer will try to start the underlying systemd
        service and then waits for the DBus API to become available.

        :param message_bus: a message bus
        :param dbus_service_name: a DBus service name
        :param systemd_unit_name: a systemd unit name corresponding to the DBus service
        :param float timeout: how long to wait for the DBus service to start in seconds
        """
        super().__init__(message_bus, dbus_service_name)
        self._message_bus = message_bus
        self._dbus_service_name = dbus_service_name
        self._systemd_unit_name = systemd_unit_name
        self._timeout = timeout

        namespace = get_namespace_from_name(dbus_service_name)
        self._object_path = get_dbus_path(*namespace)

        self._proxy = None
        self._proxy_lock = RLock()
        self._timer = None

    def get_proxy(self):
        """Returns a proxy of the remote object."""
        with self._proxy_lock:
            # if there is a proxy, return it (this also releases the lock)
            if self._proxy:
                return self._proxy
            # check if service startup is in progress
            elif not self._timer:
                # looks like service was not yet started, so start it's systemd unit
                util.start_service(self._systemd_unit_name)
                # start a timer that will mark service startup as failed if it is
                # not interrupted by successful service activation
                self._timer = Timer(self._timeout, self._service_timed_out)
                self._timer.start()
                # connect to the service_available signal of the Observer and
                # stop the timer once the DBus service becomes accessible
                self.service_available.connect(self._service_activated)
                # if the timer runs to the end without this signal activating,
                # all get_callers() that called join() on it will unblock, find
                # that proxy is not set & get an exception

        # if we got this far, it means we need to wait for the service to start
        # by joining the timer that waits for it
        self._timer.join()
        # check if service startup was successful (proxy is set)
        with self._proxy_lock:
            if self._proxy:
                return self._proxy
            else:
                # looks like something failed and prevented the thread from setting
                # a proxy, so raise an exception
                raise DBusObserverError("DBus service {} with unit {} failed to start."
                                        .format(self._dbus_service_name, self._systemd_unit_name))

    def _service_timed_out(self):
        with self._proxy_lock:
            # we don't need to set anything if the service failed
            # to start in time, the finished timer being there with
            # no proxy set is enough, so just log an error
            log.error("DBus service startup %s with unit %s timed out.",
                      self._dbus_service_name, self._systemd_unit_name)

    def _service_activated(self):
        with self._proxy_lock:
            # cancel the timer
            self._timer.cancel()
            # set the proxy
            self._proxy = self._message_bus.get_proxy(self._dbus_service_name,
                                                      self._object_path)
    def __repr__(self):
        """Returns a string representation."""
        return "{}({},{},{})".format(self.__class__.__name__,
                                     self._service_name,
                                     self._object_path,
                                     self._systemd_unit_name)
