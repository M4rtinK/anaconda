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

from pyanaconda.core import util

from pyanaconda.modules.common.task import Task
from pyanaconda.modules.common.constants.services import RHSM
from pyanaconda.modules.common.constants.objects import RHSM_CONFIG
from pyanaconda.modules.subscription import system_purpose

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)


def start_rhsm_private_bus():
    """Start the RHSM private DBus.

    The RHSM private DBus session is used for secure credential passing.

    return: address of the RHSM private DBus session
    rtype: str
    """
    rhsm_proxy = RHSM.get_proxy()
    register_server_result = rhsm_proxy.RegisterServer.Start()
    return register_server_result


class SystemPurposeConfigurationTask(Task):
    """Installation task for setting system purpose."""

    def __init__(self, sysroot, role, sla, usage, addons):
        """Create a new task.
        :param sysroot: a path to the root of the installed system
        :param lang: a value for LANG locale variable
        """
        super().__init__()
        self._sysroot = sysroot
        self._role = role
        self._sla = sla
        self._usage = usage
        self._addons = addons

    @property
    def name(self):
        return "Set system purpose"

    def run(self):
        system_purpose.give_the_system_purpose(self._sysroot,
                                               self._role,
                                               self._sla,
                                               self._usage,
                                               self._addons)


class StartRHSMTask(Task):
    """Start the RHSM DBUS service.

    TODO: this might not be needed once the RHSM DBUS services
          is a regular part of the installation environment
    """

    def __init__(self, subscription_url):
        """Create a new task.

        :param str subscription_url: Red Hat subscription service URL
        """
        super().__init__()
        self._subscription_url = subscription_url

    @property
    def name(self):
        return "Start the RHSM service"

    def run(self):
        """ There is currently a bug in the RHSM service not taking changes from DBUS
        API into account until service restart, so we need to:
        - start the RHSM service
        - set the staging URL
        - restart the RHSM service
        After that the RHSM service should be ready for use.
        """
        # make sure /etc/yum.repos.d exists
        # - othwerwise RHSM will not write out the repo file
        # - this is a know issues and it might be possible to
        #   drop this code from Anaconda once RHSM handles
        #   the missing folder better
        if not os.path.exists("/etc/yum.repos.d"):
            log.debug("start-rhsm-task: creating /etc/yum.repos.d")
            os.makedirs("/etc/yum.repos.d")

        # start the service
        log.debug("start-rhsm-task: starting the RHSM service")
        util.start_service("rhsm.service")

        time.sleep(5)

        # set the staging URL
        log.debug("start-rhsm-task: setting main subscription URL to: %s", self._subscription_url)
        rhsm_proxy = RHSM.get_proxy()
        config_proxy = RHSM.get_proxy(RHSM_CONFIG)
        config_proxy.Set("server.hostname", self._subscription_url, "")

        # restart the service
        log.debug("start-rhsm-task: restarting RHSM service")
        util.restart_service("rhsm.service")
        log.debug("start-rhsm-task: RHSM service should be now ready for use")


class RegisterWithUsernamePasswordTask(Task):
    """Register the system via username + password."""

    def __init__(self, username, password):
        """Create a new registration task.

        It is assumed the username and password have been
        validated before this task has been started.

        :param str username: Red Hat account username
        :param str password: Red Hat account password
        """
        super().__init__()
        self._username = username
        self._password = password

    @property
    def name(self):
        return "Register with Red Hat account username and password"

    def run(self):
        """Register the system with Red Hat account username and password."""

        # connect to the private DBus session
        private_bus_address = start_rhsm_private_bus()

        # register the system

        pass

class RegisterWithOrganizationKeyTask(Task):
    """Register the system via username + password."""

    def __init__(self, organization, activation_key):
        """Create a new registration task.

        :param str organization: organization name for subscription purposes
        :param str activation keys: activation key
        """
        super().__init__()
        self._organzation = organization
        self._activation_key = activation_key

    @property
    def name(self):
        return "Register with organization name and activation key"

    def run(self):
        """Register the system with organization name and activation key."""

        # connect to the RHSM private DBus session
        private_bus_address = start_rhsm_private_bus()

        # register the system

        pass


class AttachSubscriptionTask(Task):
    """Attach a subscription."""

    def __init__(self):
        """Create a new task."""
        super().__init__()

    @property
    def name(self):
        return "Attach a subscription"

    def run(self):
        """Attach a subscription to the installation environment.

        This subscription will be used to install the target system and then
        transferred to it via separate task.
        """
        # transfer a subscription
        log.debug("attach-subscription-task: attaching a subscription")


class TransferSubscriptionTokensTask(Task):
    """Transfer subscription tokens to the target system."""

    def __init__(self, sysroot):
        """Create a new task.

        :param str sysroot: target system root path
        """
        super().__init__()
        self._sysroot = sysroot

    @property
    def name(self):
        return "Transfer subscription tokens to target system"

    def run(self):
        """Transfer the subscription tokens to the target system.

        Otherwise the target system would have to be registered and subscribed again.
        """
        # transfer the certificates
        log.debug("transfer-subscription-task: transferring certificates")

        # transfer the repo file
        log.debug("transfer-subscription-task: transferring repo file")
