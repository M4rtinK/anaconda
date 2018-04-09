#
# Disk selection module.
#
# Copyright (C) 2018 Red Hat, Inc.
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
from pyanaconda.core.signal import Signal
from pyanaconda.dbus import DBus
from pyanaconda.modules.common.base import KickstartBaseModule
from pyanaconda.modules.common.constants.objects import FIREWALL
from pyanaconda.modules.network.firewall.firewall_interface import FirewallInterface

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)

class FirewallModule(KickstartBaseModule):
    """The firewall module."""

    def __init__(self):
        super().__init__()

        self.firewall_seen_changed = Signal()
        self._firewall_seen = False

        self.firewall_enabled_changed = Signal()
        self._firewall_enabled = True

        self.enabled_ports_changed = Signal()
        self._enabled_ports = []

        self.trusts_changed = Signal()
        self._trusts = []

        # services to allow
        self.enabled_services_changed = Signal()
        self._enabled_services = []

        # services to explicitly disallow
        self.disabled_services_changed = Signal()
        self._disabled_services = []

        self.use_system_defaults_changed = Signal()
        self._use_system_defaults = False

    def publish(self):
        """Publish the module."""
        DBus.publish_object(FIREWALL.object_path, FirewallInterface(self))

    def process_kickstart(self, data):
        """Process the kickstart data."""
        self.set_firewall_seen(self.seen)
        self.set_use_system_defaults = data.use_system_defaults
        self.set_firewall_enabled = data.enabled
        self.set_enabled_ports = data.ports
        self.set_trusts = data.trusts
        self.set_enabled_services = data.services
        self.set_disabled_services = data.remove_services

    def setup_kickstart(self, data):
        """Setup the kickstart data."""
        data.use_system_defaults = self.use_system_defaults
        data.enabled = self.firewall_enabled
        data.ports = self.enabled_ports
        data.trusts = self.trusts
        data.services = self.enabled_services
        data.remove_services = self.disabled_services
        return data

    @property
    def firewall_seen(self):
        return self._firewall_seen

    def set_firewall_seen(self, firewall_seen):
        self._firewall_seen = firewall_seen
        self.firewall_seen_changed.emit()
        log.debug("Firewall command considered seen in kickstart: %s.", self._firewall_seen)

    @property
    def use_system_defaults(self):
        return self._use_system_defaults

    def set_use_system_defaults(self, use_system_defaults):
        self._use_system_defaults = use_system_defaults
        self.use_system_defaults_changed.emit()
        if self.use_system_defaults:
           log.debug("System default will be used for firewall.")
        else:
           log.debug("Anaconda will configure firewall.")

    @property
    def firewall_enabled(self):
        return self._firewall_enabled

    def set_firewall_enabled(self, firewall_enabled):
        self._firewall_enabled = firewall_enabled
        self.firewall_enabled_changed.emit()
        if self.firewall_enabled:
            log.debug("Firewall will be enabled.")
        else:
            log.debug("Firewall will be disabled.")

    @property
    def enabled_ports(self):
        return self._enabled_ports

    def set_enabled_ports(self, enabled_ports):
        self._enabled_ports = list(enabled_ports)
        self.enabled_ports_changed.emit()
        log.debug("Ports that will be allowed through the firewall: %s", self._enabled_ports)

    @property
    def trusts(self):
        return self._trusts

    def set_trusts(self, trusts):
        self._trusts = list(trusts)
        self.trusts_changed.emit()
        log.debug("Trusted devices that will be allowed through the firewall: %s", self._trusts)

    @property
    def enabled_services(self):
        return self._enabled_services

    def set_enabled_services(self, enabled_services):
        self._enabled_services = list(enabled_services)
        self.enabled_services_changed.emit()
        log.debug("Services that will be allowed through the firewall: %s", self._enabled_services)

    @property
    def disabled_services(self):
        return self._disabled_services

    def set_disabled_services(self, disabled_services):
        self._disabled_services = list(disabled_services)
        self.disabled_services_changed.emit()
        log.debug("Services that will be explicitly disabled on the firewall: %s", self._disabled_services)
