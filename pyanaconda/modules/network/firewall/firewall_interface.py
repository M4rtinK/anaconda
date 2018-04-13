#
# DBus interface for the disk selection module.
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
from pyanaconda.dbus.interface import dbus_interface
from pyanaconda.dbus.property import emits_properties_changed
from pyanaconda.dbus.typing import *  # pylint: disable=wildcard-import
from pyanaconda.modules.common.base import KickstartModuleInterfaceTemplate
from pyanaconda.modules.common.constants.objects import FIREWALL


@dbus_interface(FIREWALL.interface_name)
class FirewallInterface(KickstartModuleInterfaceTemplate):
    """DBus interface for the firewall module."""

    def connect_signals(self):
        """Connect the signals."""
        super().connect_signals()
        self.watch_property("FirewallKickstarted", self.implementation.firewall_seen_changed)
        self.watch_property("UseSystemDefaults", self.implementation.use_system_defaults_changed)
        self.watch_property("FirewallEnabled", self.implementation.firewall_enabled_changed)
        self.watch_property("EnabledPorts", self.implementation.enabled_ports_changed)
        self.watch_property("Trusts", self.implementation.trusts_changed)
        self.watch_property("EnabledServices", self.implementation.enabled_services_changed)
        self.watch_property("DisabledServices", self.implementation.disabled_services_changed)

    @property
    def FirewallKickstarted(self) -> Bool:
        """Was the firewall command present in the input kickstart ?"""
        return self.implementation.firewall_seen

    @property
    def UseSystemDefaults(self) -> Bool:
        """Should system defaults be used for firewall configuration ?

        This effectively means Anaconda will not configure Firewall in any way
        and installed system defaults will be used.
        """
        return self.implementation.use_system_defaults

    @emits_properties_changed
    def SetUseSystemDefaults(self, use_system_defaults: Bool):
        """Set if system defaults should be used for the firewall configuration."""
        self.implementation.set_use_system_defaults(use_system_defaults)

    @property
    def FirewallEnabled(self) -> Bool:
        """Should firewall be enabled ?"""
        return self.implementation.firewall_enabled

    @emits_properties_changed
    def SetFirewallEnabled(self, firewall_enabled: Bool):
        """Set if the firewall should be enabled or disabled."""
        self.implementation.set_firewall_enabled(firewall_enabled)

    @property
    def EnabledPorts(self) -> List[Str]:
        """List of ports to be allowed through the firewall."""
        return self.implementation.enabled_ports

    @emits_properties_changed
    def SetEnabledPorts(self, enabled_ports: List[Str]):
        """Set the list of ports to be allowed thorough the firewall.

        :param enabled_ports: a list of ports to be enabled
        """
        self.implementation.set_enabled_ports(enabled_ports)

    @property
    def Trusts(self) -> List[Str]:
        """List of trusted devices to be allowed through the firewall."""
        return self.implementation.enabled_ports

    @emits_properties_changed
    def SetTrusts(self, trusts: List[Str]):
        """Set the list of trusted devices to be allowed through the firewall.

        :param trusts: a list of trusted devices
        """
        self.implementation.set_trusts(trusts)

    @property
    def EnabledServices(self) -> List[Str]:
        """List of services to be allowed through the firewall."""
        return self.implementation.enabled_services

    @emits_properties_changed
    def SetEnabledServices(self, enabled_services: List[Str]):
        """Set the list of services to be allowed through the firewall.

        :param enabled_services: a list of services to be enabled
        """
        self.implementation.set_enabled_services(enabled_services)

    @property
    def DisabledServices(self) -> List[Str]:
        """List of services to be explicitly disabled on the firewall."""
        return self.implementation.disabled_services

    @emits_properties_changed
    def SetDisabledServices(self, disabled_services: List[Str]):
        """Set the list of services to be explicitly disabled on the firewall.

        :param enabled_services: a list of services to be enabled
        """
        self.implementation.set_disabled_services(disabled_services)
