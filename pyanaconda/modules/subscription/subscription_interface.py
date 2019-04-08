#
# DBus interface for the subscription module.
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
from pyanaconda.modules.common.constants.services import SUBSCRIPTION
from pyanaconda.dbus.property import emits_properties_changed
from pyanaconda.dbus.typing import *  # pylint: disable=wildcard-import
from pyanaconda.modules.common.base import KickstartModuleInterface
from pyanaconda.dbus.interface import dbus_interface

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)

@dbus_interface(SUBSCRIPTION.interface_name)
class SubscriptionInterface(KickstartModuleInterface):
    """DBus interface for Subscription module."""

    def connect_signals(self):
        log.debug("SI CONNECT SIGNALS")
        super().connect_signals()
        log.debug("SI CONNECT SIGNALS SUPER DONE")
        self.watch_property("Role", self.implementation.role_changed)
        self.watch_property("SLA", self.implementation.sla_changed)
        self.watch_property("Usage", self.implementation.usage_changed)
        self.watch_property("Addons", self.implementation.addons_changed)
        #self.watch_property("IsRegistered", self.implementation.registered_changed)
        #self.watch_property("IsSubscriptionAttached", self.implementation.subscription_attached_changed)
        #self.watch_property("Organization", self.implementation.organization_changed)
        #self.watch_property("IsActivationKeySet", self.implementation.activation_key_changed)
        #self.watch_property("AccountUsername", self.implementation.red_hat_account_username_changed)
        #self.watch_property("IsAccountPasswordSet", self.implementation.red_hat_account_password_changed)
        #self.watch_property("SubscriptionUrl", self.implementation.subscription_url_changed)

        # the SystemPurposeWillBeSet property depends on the value of
        # all other system purpose properties
        self.watch_property("IsSystemPurposeSet", self.implementation.is_system_purpose_set_changed)
        log.debug("SI CONNECT SIGNALS ALL DONE")

    # system purpose

    @property
    def ValidRoles(self) -> List[Str]:
        """Return all valid roles."""
        return self.implementation.valid_roles

    @property
    def Role(self) -> Str:
        """Role for system subscription purposes."""
        return self.implementation.role

    @emits_properties_changed
    def SetRole(self, role: Str):
        """Set the intended role.

        Sets the role intent for subscription purposes.

        This setting is optional.

        :param str role: a role string
        """
        self.implementation.set_role(role)

    @property
    def ValidSLAs(self) -> List[Str]:
        """Return all valid SLAs."""
        return self.implementation.valid_slas

    @property
    def SLA(self) -> Str:
        """SLA for system subscription purposes."""
        return self.implementation.sla

    @emits_properties_changed
    def SetSLA(self, sla: Str):
        """Set the intended SLA.

        Sets the SLA intent for subscription purposes.

        This setting is optional.

        :param str sla: a SLA string
        """
        self.implementation.set_sla(sla)

    @property
    def ValidUsageTypes(self) -> List[Str]:
        """List all valid usage types."""
        return self.implementation.valid_usage_types

    @property
    def Usage(self) -> Str:
        """Usage for system subscription purposes."""
        return self.implementation.usage

    @emits_properties_changed
    def SetUsage(self, usage: Str):
        """Set the intended usage.

        Sets the usage intent for subscription purposes.

        This setting is optional.

        :param str usage: a usage string
        """
        self.implementation.set_usage(usage)

    @property
    def Addons(self) -> List[Str]:
        """Addons for system subscription purposes."""
        return self.implementation.addons

    @emits_properties_changed
    def SetAddons(self, addons: List[Str]):
        """Set the intended addons (additional layered products and features).

        This setting is optional.

        :param addons: a list of strings, one per layered product/feature
        :type addons: list of strings
        """
        self.implementation.set_addons(addons)

    @property
    def IsSystemPurposeSet(self) -> Bool:
        """Report if at least one system purpose value is set.

        This is basically a shortcut so that the DBUS API users don't
        have to query Role, Sla, Usage & Addons every time they want
        to check if at least one system purpose value is set.
        """
        return self.implementation.is_system_purpose_set

    def SetSystemPurposeWithTask(self, sysroot: Str) -> ObjPath:
        """Set system purpose for the installed system with an installation task.

        FIXME: This is just a temporary method.

        :return: a DBus path of an installation task
        """
        return self.implementation.set_system_purpose_with_task(sysroot)

    # subscription

    @property
    def IsRegistered(self) -> Bool:
        """Report if the system has been registered."""
        return self.implementation.registered

    @property
    def IsSubscriptionAttached(self) -> Bool:
        """Report if subscription has been attached."""
        return self.implementation.subscription_attached

    @property
    def Organization(self) -> Str:
        """Organization name for subscription purposes."""
        return self.implementation.organization

    @emits_properties_changed
    def SetOrganization(self, organization: Str):
        """Set organization name.

        :param str organization: organization name
        """
        self.implementation.organization = organization

    @property
    def IsActivationKeySet(self) -> Bool:
        """Report if activation key has been set."""
        return bool(self.implementation.activation_key)

    @emits_properties_changed
    def SetActivationKey(self, activation_key: Str):
        """Set activation key for subscription purposes.

        :param str activation_key: an activation key
        """
        self.implementation.activation_key = activation_key

    @property
    def AccountUsername(self) -> Str:
        """Red Hat account name for subscription purposes."""
        return self.implementation.red_hat_account_username

    @emits_properties_changed
    def SetAccountUsername(self, account_username: Str):
        """Set Red Hat account name.

        :param str account_name: Red Hat account name
        """
        self.implementation.red_hat_account_username = account_username

    @property
    def IsAccountPasswordSet(self) -> Bool:
        """Report if Red Hat account password has been set."""
        return bool(self.implementation.red_hat_account_password)

    @emits_properties_changed
    def SetAccountPassword(self, password: Str):
        """Set Red Hat account password.

        :param str password: a Red Hat account password
        """
        self.implementation.red_hat_account_password = password

    @property
    def SubscriptionUrl(self) -> Str:
        """Red Hat subscription service URL."""
        return self.implementation.subscription_url

    @emits_properties_changed
    def SetSubscriptionUrl(self, url: Str):
        """Set Red Hat subscription service URL.

        :param str url: Red Hat subscription service URL
        """
        self.implementation.subscription_url = url

    def StartRHSMWithTask(self) -> ObjPath:
        """Start RHSM with an installation task.

        FIXME: This is just a temporary method.

        :return: a DBus path of an installation task
        """
        return self.implementation.start_rhsm_with_task()

    def RegisterWithTask(self) -> ObjPath:
        """Register with an installation task.

        FIXME: This is just a temporary method.

        :return: a DBus path of an installation task
        """
        return self.implementation.register_with_task()

    def AttachWithTask(self) -> ObjPath:
        """Attach subscription with an installation task.

        FIXME: This is just a temporary method.

        :return: a DBus path of an installation task
        """
        return self.implementation.attach_subscription_with_task()

    def TransferTokensWithTask(self, sysroot: Str) -> ObjPath:
        """Transfer subscription tokens with an installation task.

        FIXME: This is just a temporary method.

        :return: a DBus path of an installation task
        """
        return self.implementation.transfer_tokens_with_task(sysroot)
