#
# Kickstart module for subscription handling.
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
import os

import time

import pydbus

from pyanaconda.core import util

from pyanaconda.dbus import DBus
from pyanaconda.dbus.typing import get_variant, Str
from pyanaconda.dbus.connection import Connection
from pyanaconda.core.signal import Signal
from pyanaconda.modules.common.base import KickstartModule
from pyanaconda.modules.common.constants.services import SUBSCRIPTION
from pyanaconda.modules.common.constants.services import RHSM
from pyanaconda.modules.common.constants.objects import RHSM_CONFIG, RHSM_REGISTER_SERVER, RHSM_ATTACH
from pyanaconda.modules.subscription.subscription_interface import SubscriptionInterface
from pyanaconda.modules.subscription.kickstart import SubscriptionKickstartSpecification
from pyanaconda.modules.subscription.installation import SystemPurposeConfigurationTask
from pyanaconda.modules.subscription.installation import StartRHSMTask, RegisterWithUsernamePasswordTask
from pyanaconda.modules.subscription.installation import RegisterWithOrganizationKeyTask, AttachSubscriptionTask
from pyanaconda.modules.subscription.installation import TransferSubscriptionTokensTask
from pyanaconda.modules.subscription import system_purpose

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)


class RHSMPrivateBusConnection(Connection):
    """Representation of a RHSM private bus connection."""

    def __init__(self, rhsm_private_bus_address):
        super().__init__()
        self._rhsm_private_bus_address = rhsm_private_bus_address

    def get_new_connection(self):
        """Connect to the RHSM private bus."""
        log.info("Connecting to RHSM private bus at %s.", self._rhsm_private_bus_address)
        connection = pydbus.bus.Gio.DBusConnection.new_for_address_sync(self._rhsm_private_bus_address,
                                                                        pydbus.bus.Gio.DBusConnectionFlags.AUTHENTICATION_CLIENT,
                                                                        None, None)
        connection.pydbus.autoclose = False
        return connection.pydbus


class SubscriptionModule(KickstartModule):
    """The Subscription module."""

    def __init__(self):
        super().__init__()
        log.debug("SUBSCRIPTION INIT START")

        # system purpose
        self._valid_roles = {}
        self.role_changed = Signal()
        self._role = ""

        self._valid_slas = {}
        self.sla_changed = Signal()
        self._sla = ""

        self._valid_usage_types = {}
        self.usage_changed = Signal()
        self._usage = ""

        self.addons_changed = Signal()
        self._addons = []

        self.is_system_purpose_set_changed = Signal()
        self.role_changed.connect(self.is_system_purpose_set_changed.emit)
        self.sla_changed.connect(self.is_system_purpose_set_changed.emit)
        self.usage_changed.connect(self.is_system_purpose_set_changed.emit)
        self.addons_changed.connect(self.is_system_purpose_set_changed.emit)

        self._load_valid_values()

        # subscription
        self.registered_changed = Signal()
        self._registered = False
        self.subscription_attached_changed = Signal()
        self._subscription_attached = False

        self.organization_changed = Signal()
        self._organization = ""

        self.activation_key_changed = Signal()
        self._activation_key = ""

        self.red_hat_account_username_changed = Signal()
        self._red_hat_account_username = ""

        self.red_hat_account_password_changed = Signal()
        self._red_hat_account_password = ""

        self.subscription_url_changed = Signal()
        self._subscription_url = ""

        self._rhsm_private_bus_address = ""

        log.debug("SUBSCRIPTION INIT DONE")

    def _load_valid_values(self):
        """Load lists of valid roles, SLAs and usage types.

        About role/sla/validity:
        - an older installation image might have older list of valid fields,
          missing fields that have become valid after the image has been released
        - fields that have been valid in the past might be dropped in the future
        - there is no list of valid addons

        Due to this we need to take into account that the listing might not always be
        comprehensive and that we need to allow what might on a first glance look like
        invalid values to be written to the target system.
        """
        roles, slas, usage_types = system_purpose.get_valid_fields()
        self._valid_roles = roles
        self._valid_slas = slas
        self._valid_usage_types = usage_types

    def publish(self):
        """Publish the module."""
        log.debug("SUBSCRIPTION PUBLISH START")
        interface_instance = SubscriptionInterface(self)
        log.debug("SUBSCRIPTION PUBLISH INTERFACE DONE")
        log.debug("DBUS")
        log.debug(DBus)
        log.debug("SUBSCRIPTION INTERFACE")
        log.debug(interface_instance)
        DBus.publish_object(SUBSCRIPTION.object_path, interface_instance)
        #DBus.publish_object(SUBSCRIPTION.object_path, SubscriptionInterface(self))
        log.debug("SUBSCRIPTION PUBLISH OBJECT DONE")
        DBus.register_service(SUBSCRIPTION.service_name)
        log.debug("SUBSCRIPTION PUBLISH DONE")

    @property
    def kickstart_specification(self):
        """Return the kickstart specification."""
        log.debug("RETURN KS SPEC")
        return SubscriptionKickstartSpecification

    def process_kickstart(self, data):
        """Process the kickstart data."""
        log.debug("Processing kickstart data...")

        # system purpose
        #
        # Try if any of the values in kickstart match a valid field.
        # If it does, write the valid field value instead of the value from kickstart.
        #
        # This way a value in kickstart that has a different case and/or trailing white space
        # can still be used to preselect a value in a UI instead of being marked as a custom
        # user specified value.
        self._process_role(data)
        self._process_sla(data)
        self._process_usage(data)

        # we don't have any list of valid addons and addons are not shown in the UI,
        # so we just forward the values from kickstart
        if data.syspurpose.addons:
            self.set_addons(data.syspurpose.addons)

        # subscription
        self.organization = data.rhsm.organization
        self.activation_key = data.rhsm.activation_key
        self.subscription_url = data.rhsm.url

        # TODO: find if there is a more appropriate place to call the RHSM service from
        #       than kickstart parsing

        # prepare the RHSM service for use
        self._start_rhsm_service()

        # if an alternate subscription URL is specified via kickstart, set it
        self._set_subscription_url()

        # start the RHSM private bus (needed for credential passing)
        self._start_private_bus()

        # if org and activation key are set, register at once
        # TODO: we might want to eventually trigger this from a spoke
        if self.organization and self.activation_key:
            self.registered = self._register_with_org_key(self._rhsm_private_bus_address, self.organization, self.activation_key)

        # attach a subscription in case we are registered
        if self.registered:
            self.subscription_attached = self._auto_attach_subscription()

    def _process_role(self, data):
        if data.syspurpose.role:
            role_match = system_purpose.match_field(data.syspurpose.role, self.valid_roles)
        else:
            role_match = None

        if role_match:
            log.info("role value %s from kickstart matched to know valid field %s", data.syspurpose.role, role_match)
            self.set_role(role_match)
        elif data.syspurpose.role:
            log.info("using custom role value from kickstart: %s", data.syspurpose.role)
            self.set_role(data.syspurpose.role)

    def _process_sla(self, data):
        if data.syspurpose.sla:
            sla_match = system_purpose.match_field(data.syspurpose.sla, self.valid_slas)
        else:
            sla_match = None

        if sla_match:
            log.info("SLA value %s from kickstart matched to know valid field %s", data.syspurpose.sla, sla_match)
            self.set_sla(sla_match)
        elif data.syspurpose.sla:
            log.info("using custom SLA value from kickstart: %s", data.syspurpose.sla)
            self.set_sla(data.syspurpose.sla)

    def _process_usage(self, data):
        if data.syspurpose.usage:
            usage_match = system_purpose.match_field(data.syspurpose.usage, self._valid_usage_types)
        else:
            usage_match = None

        if usage_match:
            log.info("usage value %s from kickstart matched to know valid field %s", data.syspurpose.usage, usage_match)
            self.set_usage(usage_match)
        elif data.syspurpose.usage:
            log.info("using custom usage value from kickstart: %s", data.syspurpose.usage)
            self.set_usage(data.syspurpose.usage)

    def generate_kickstart(self):
        """Return the kickstart string."""
        log.debug("Generating kickstart data...")

        # system purpose
        data = self.get_kickstart_handler()
        data.syspurpose.role = self.role
        data.syspurpose.sla = self.sla
        data.syspurpose.usage = self.usage
        data.syspurpose.addons = self.addons

        # subscription
        data.rhsm.organization = self.organization
        data.rhsm.activation_key = self.activation_key
        data.rhsm.subscription_url = self.subscription_url

        return str(data)

    # system purpose

    @property
    def valid_roles(self):
        """Return a list of valid roles.

        :return: list of valid roles
        :rtype: list of strings
        """
        return self._valid_roles

    @property
    def role(self):
        """Return the intended role (if any)."""
        return self._role

    def set_role(self, role):
        """Set the role."""
        self._role = role
        self.role_changed.emit()
        log.debug("Role is set to %s.", role)

    @property
    def valid_slas(self):
        """Return a list of valid SLAs.

        :return: list of valid SLAs
        :rtype: list of strings
        """
        return self._valid_slas

    @property
    def sla(self):
        """Return the intended SLA (if any)."""
        return self._sla

    def set_sla(self, sla):
        """Set the SLA."""
        self._sla = sla
        self.sla_changed.emit()
        log.debug("SLA is set to %s.", sla)

    @property
    def valid_usage_types(self):
        """Return a list of valid usage types.

        :return: list of valid usage types
        :rtype: list of strings
        """
        return self._valid_usage_types

    @property
    def usage(self):
        """Return the intended usage (if any)."""
        return self._usage

    def set_usage(self, usage):
        """Set the intended usage."""
        self._usage = usage
        self.usage_changed.emit()
        log.debug("Usage is set to %s.", usage)

    @property
    def addons(self):
        """Return list of additional layered products or features (if any)."""
        return self._addons

    def set_addons(self, addons):
        """Set the intended layered products or features."""
        self._addons = addons
        self.addons_changed.emit()
        log.debug("Addons set to %s.", addons)

    @property
    def is_system_purpose_set(self):
        """Report if system purpose will be set.

        This basically means at least one of role, SLA, usage or addons
        has a user-set non-default value.
        """
        return any((self.role, self.sla, self.usage, self.addons))

    def set_system_purpose_with_task(self, sysroot):
        """Set system purpose for the installed system with an installation task.

        FIXME: This is just a temporary method.

        :param sysroot: a path to the root of the installed system
        :return: a DBus path of an installation task
        """
        task = SystemPurposeConfigurationTask(sysroot, self.role, self.sla, self.usage, self.addons)
        path = self.publish_task(SUBSCRIPTION.namespace, task)
        return path

    # subscription

    @property
    def registered(self):
        """Return True if the system has been registered, False otherwise.

        :return: if the system can be considered as registered
        :rtype: bool
        """
        return self._registered

    @registered.setter
    def registered(self, system_registered):
        """Set that the system has been registered.

        :param bool system_registered: system registered state
        """
        self._registered = system_registered
        self.registered_changed.emit()

    @property
    def subscription_attached(self):
        """Return True if a subscription has been attached to the system.

        :return: if a subscription has been attached to the system
        :rtype: bool
        """
        return self._subscription_attached

    @subscription_attached.setter
    def subscription_attached(self, system_subscription_attached):
        """Set a subscription has been attached to the system.

        :param bool system_registered: system attached subscription state
        """
        self._subscription_attached = system_subscription_attached
        self.subscription_attached_changed.emit()

    @property
    def organization(self):
        """Return organization name for subscription purposes.

        Organization name is needed when using an activation key
        and is not needed when registering via Red Hat account
        credentials.

        :return: organization name
        :rtype: str
        """
        return self._organization

    @organization.setter
    def organization(self, organization):
        """Set organization name.

        :param str organization: new organization name
        """
        self._organization = organization
        self.organization_changed.emit()
        log.debug("Organization set to: %s", organization)

    @property
    def activation_key(self):
        """Return the activation key used for subscription purposes.

        You need to set organization name when using an activation key.
        :return: activation key
        :rtype: str
        """
        return self._activation_key

    @activation_key.setter
    def activation_key(self, activation_key):
        """Set the activation key.

        :param str activation_key: an activation key
        """
        self._activation_key = activation_key
        self.activation_key_changed.emit()
        log.debug("An activation key has been set.")

    @property
    def red_hat_account_username(self):
        """A Red Hat account name for subscription purposes.

        :return: red hat account name
        :rtype: str
        """
        return self._red_hat_account_username

    @red_hat_account_username.setter
    def red_hat_account_username(self, account_username):
        """Set the Red Hat account name.

        :param str account_username: Red Hat account username
        """
        self._red_hat_account_username = account_username
        self.red_hat_account_username_changed.emit()
        log.debug("Red Hat account name set to: %s", account_username)

    @property
    def red_hat_account_password(self):
        """A Red Hat account password for subscription purposes.

        :return: red hat account password
        :rtype: str
        """
        return self._red_hat_account_password

    @red_hat_account_password.setter
    def red_hat_account_password(self, password):
        """Set the Red Hat account name.

        :param str password: Red Hat account password
        """
        self._red_hat_account_password = password
        self.red_hat_account_password_changed.emit()
        log.debug("Red Hat account password has been set.")

    @property
    def subscription_url(self):
        """Get the Red Hat subscription service URL.

        Empty string means that the default subscription service
        URL will be used.

        :return: subscription service URL
        :rtype: str
        """
        return self._subscription_url


    @subscription_url.setter
    def subscription_url(self, url):
        """Set the Red Hat subscription service URL.

        This can be used to override the default subscription
        service URL to a custom one, for testing and
        other use cases.

        :param str url: subscription service URL
        """
        self._subscription_url = url
        self.subscription_url_changed.emit()
        log.debug("Red Hat subscription service URL set to: %s", url)

    def start_rhsm_with_task(self):
        task = StartRHSMTask(self.subscription_url)
        path = self.publish_task(SUBSCRIPTION.namespace, task)
        return path

    def register_with_username_password_with_task(self):
        task = RegisterWithUsernamePasswordTask(self.red_hat_account_username, self.red_hat_account_password)
        path = self.publish_task(SUBSCRIPTION.namespace, task)
        return path

    def register_with_org_key_with_task(self):
        task = RegisterWithOrganizationKeyTask(self.organization, self.activation_key)
        path = self.publish_task(SUBSCRIPTION.namespace, task)
        return path

    def attach_subscription_with_task(self):
        task = AttachSubscriptionTask()
        path = self.publish_task(SUBSCRIPTION.namespace, task)
        return path

    def transfer_tokens_with_task(self, sysroot):
        task = TransferSubscriptionTokensTask(sysroot)
        path = self.publish_task(SUBSCRIPTION.namespace, task)
        return path

    def _start_rhsm_service(self):
        """ Start the RHSM DBUS service.

        The RHSM DBUS service is not yet running by default,
        so we need to start it by ourselves. Also we
        need to make sure /etc/yum.repos.d/ exists.

        Both of these operation might no longer bee
        needed for final version of RHSM support.
        """
        # make sure /etc/yum.repos.d exists
        # - otherwise RHSM will not write out the repo file
        # - this is a know issues and it might be possible to
        #   drop this code from Anaconda once RHSM handles
        #   the missing folder better
        if not os.path.exists("/etc/yum.repos.d"):
            log.debug("RHSM: creating /etc/yum.repos.d")
            os.makedirs("/etc/yum.repos.d")

        # start the service
        log.debug("RHSM: starting the RHSM service")
        util.start_service("rhsm.service")

    def _set_subscription_url(self):
        """ There is currently a bug in the RHSM service not taking changes from DBUS
        API into account until service restart, so we need to:
        - set the staging URL
        - restart the RHSM service
        After that the RHSM service should be ready for use.
        """
        log.debug("RHSM: setting main subscription URL to: %s", self._subscription_url)
        rhsm_proxy = RHSM.get_proxy()
        config_proxy = RHSM.get_proxy(RHSM_CONFIG)
        config_proxy.Set("server.hostname", get_variant(Str, self.subscription_url), "")
        config_proxy.Set("server.insecure", get_variant(Str, "1"), "")
        # also enable RHSM debugging
        config_proxy.Set("logging.default_log_level", get_variant(Str, "DEBUG"), "")
        config_proxy.Set("logging.subscription_manager", get_variant(Str, "DEBUG"), "")
        config_proxy.Set("logging.rhsm", get_variant(Str, "DEBUG"), "")
        config_proxy.Set("logging.rhsm.connection", get_variant(Str, "DEBUG"), "")
        config_proxy.Set("logging.rhsm-app", get_variant(Str, "DEBUG"), "")
        config_proxy.Set("logging.rhsm-app.rhsmd", get_variant(Str, "DEBUG"), "")

        # restart the service
        log.debug("RHSM: restarting RHSM service")
        util.restart_service("rhsm.service")
        log.debug("RHSM: RHSM service should be now ready for use")

    def _start_private_bus(self):
        """Start the RHSM private DBus session.

        This used by RHSM for secure credential passing.
        """
        log.debug("RHSM: starting RHSM private DBus session")
        rhsm_proxy = RHSM.get_proxy()
        register_server_proxy = RHSM.get_proxy(RHSM_REGISTER_SERVER)
        private_bus_address = register_server_proxy.Start("")
        self._rhsm_private_bus_address = private_bus_address
        log.debug("RHSM: RHSM private DBus session started")

    def _register_with_org_key(self, private_bus_address, organization, activation_key):
        """Register using organization name and activation key.

        :return: True if registration was successful, False otherwise
        :rtype: bool
        """
        log.debug("RHSM: connecting to RHSM private bus")
        private_connection = RHSMPrivateBusConnection(private_bus_address)
        private_register_proxy = private_connection.get_proxy("com.redhat.RHSM1","/com/redhat/RHSM1/Register")
        log.debug("RHSM: registering with organization and activation key")
        try:
            private_register_proxy.RegisterWithActivationKeys(organization, [activation_key], {}, {}, "")
            # TODO: better error handling
            log.debug("RHSM: registered with organization and activation key")
            return True
        except:
            log.exception("RHSM: failed to register with organization and activation key")
            return False

    def _register_with_username_password(self, private_bus_address, organization, username, password):
        """Register using Red Hat account username and password.

        :return: True if registration was successful, False otherwise
        :rtype: bool
        """
        log.debug("RHSM: connecting to RHSM private bus")
        private_connection = RHSMPrivateBusConnection(private_bus_address)
        private_register_proxy = private_connection.get_proxy("com.redhat.RHSM1","/com/redhat/RHSM1/Register")
        log.debug("RHSM: registering with username and password")
        try:
            private_register_proxy.Register(organization, username, password, {}, {}, "")
            # TODO: better error handling
            log.debug("RHSM: registered with username and password")
            return True
        except:
            log.exception("RHSM: failed to register with username and password")
            return False

    def _auto_attach_subscription(self, service_level=""):
        """Automatically attach a subscription.

        :param str service_level: an optional service level string

        :return: True if we managed to attach a subscription successfully, False otherwise
        :rtype: bool
        """
        log.debug("RHSM: auto-attaching a subscription")
        try:
            rhsm_proxy = RHSM.get_proxy()
            attach_proxy = RHSM.get_proxy(RHSM_ATTACH)
            attach_proxy.AutoAttach(service_level, {}, "")
            log.debug("RHSM: auto-attached a subscription")
            return True
        except:
            log.exception("RHSM: auto-attach failed")
            return False






