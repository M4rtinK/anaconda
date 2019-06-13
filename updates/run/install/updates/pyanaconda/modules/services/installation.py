#
# Copyright (C) 2019 Red Hat, Inc.
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

from pyanaconda.core import util
from pyanaconda.core.constants import TEXT_ONLY_TARGET, GRAPHICAL_TARGET

from pyanaconda.modules.common.task import Task
from pyanaconda.modules.common.errors.installation import SystemdDefaultTargetConfigurationError
from pyanaconda.modules.services.constants import SetupOnBootAction

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)

__all__ = ["ConfigureInitialSetupTask", "ConfigureServicesTask", "ConfigureSystemdDefaultTargetTask",
           "ConfigureDefaultDesktopTask"]


class ConfigureInitialSetupTask(Task):
    """Installation task for Initial Setup configuration."""

    INITIAL_SETUP_UNIT_NAME = "initial-setup.service"

    def __init__(self, sysroot, setup_on_boot):
        """Create a new Initial Setup configuration task.

        :param str sysroot: a path to the root of the target system
        :param enum setup_on_boot: setup-on-boot mode for Initial Setup

        Modes are defined by the SetupOnBoot enum as distinct integers.

        """
        super().__init__()
        self._sysroot = sysroot
        self._setup_on_boot = setup_on_boot

    @property
    def name(self):
        return "Configure Initial Setup"

    def _unit_file_exists(self, service):
        """Check if unit file corresponding to the service exists in the chroot.

        The check works by taking the service name and checking if a file with
        such name exists in the folder where system wide unit files are stored.

        :param str service: name of the service (including the .service extension) to check
        """
        return os.path.exists(os.path.join(self._sysroot, "lib/systemd/system/", service))

    def _enable_service(self):
        """Enable the Initial Setup service."""
        if self._unit_file_exists(self.INITIAL_SETUP_UNIT_NAME):
            util.enable_service(self.INITIAL_SETUP_UNIT_NAME)
        else:
            log.debug("Initial Setup will not be started on first boot, because "
                      "its unit file (%s) is not installed.", self.INITIAL_SETUP_UNIT_NAME)

    def _disable_service(self):
        """Disable the Initial Setup service."""
        if self._unit_file_exists(self.INITIAL_SETUP_UNIT_NAME):
            util.disable_service(self.INITIAL_SETUP_UNIT_NAME, root=self._sysroot)

    def _enable_reconfig_mode(self):
        """Write the reconfig mode trigger file."""
        log.debug("Initial Setup reconfiguration mode will be enabled.")
        util.touch(os.path.join(self._sysroot, "etc/reconfigSys"))

    def run(self):
        if self._setup_on_boot == SetupOnBootAction.ENABLED:
            self._enable_service()
        elif self._setup_on_boot == SetupOnBootAction.RECONFIG:
            # reconfig implies enabled
            self._enable_service()
            self._enable_reconfig_mode()
        else:
            # the Initial Setup service is disabled by default
            self._disable_service()


class ConfigureServicesTask(Task):
    """Installation task for service configuration.

    We enable and disable services as specified.
    """

    def __init__(self, sysroot, disabled_services, enabled_services):
        """Create a new service configuration task.

        :param str sysroot: a path to the root of the target system
        :param disabled_services: services that should be disabled
        :param enabled_services: services that should be enabled

        NOTE: We always first disable all services that should be disabled
              and only then enable all services that should be enabled.
        """
        super().__init__()
        self._sysroot = sysroot
        self._disabled_services = disabled_services
        self._enabled_services = enabled_services

    @property
    def name(self):
        return "Configure services"

    def run(self):
        for service_name in self._disabled_services:
            log.debug("Disabling service: %s.", service_name)
            util.disable_service(service_name, root=self._sysroot)

        for service_name in self._enabled_services:
            log.debug("Enabling service: %s.", service_name)
            util.enable_service(service_name, root=self._sysroot)


class ConfigureSystemdDefaultTargetTask(Task):
    """Installation task for configuring systemd default target.

    Set the correct systemd default target for the target system.

    We support setting either the text only "multi-user"
    target or the graphical target called "graphical".
    """

    SUPPORTED_SYSTEMD_TARGETS = [TEXT_ONLY_TARGET, GRAPHICAL_TARGET]

    def __init__(self, sysroot, default_target):
        """Create a new systemd target configuration task.

        :param str sysroot: a path to the root of the target system
        :param default_target: systemd default target to be set
        """
        super().__init__()
        self._sysroot = sysroot
        # default to the text only target
        if not default_target:
            default_target = TEXT_ONLY_TARGET
        self._default_target = default_target

    @property
    def name(self):
        return "Configure systemd default target"

    def run(self):
        if self._default_target not in self.SUPPORTED_SYSTEMD_TARGETS:
            msg = "Unsupported systemd default target: {} Specify one of: {}".format(
                self._default_target, self.SUPPORTED_SYSTEMD_TARGETS
            )
            raise SystemdDefaultTargetConfigurationError(msg)
        else:
            log.debug("Setting systemd default target to: %s", self._default_target)

        if not os.path.isdir(os.path.join(self._sysroot, 'etc/systemd/system')):
            msg = "There is no /etc/systemd/system directory, cannot set systemd default target!"
            raise SystemdDefaultTargetConfigurationError(msg)

        default_target_path = os.path.join(self._sysroot, 'etc/systemd/system/default.target')
        # unlike an links already in place
        if os.path.islink(default_target_path):
            os.unlink(default_target_path)
        # symlink the selected target
        selected_target_path = os.path.join(self._sysroot, 'etc/systemd/system', self._default_target)
        log.debug("Linking %s as systemd default target.", selected_target_path)
        os.symlink(selected_target_path, default_target_path)


class ConfigureDefaultDesktopTask(Task):
    """Installation task for configuring the default desktop."""

    def __init__(self, sysroot, default_desktop):
        """Create a new default desktop configuration task.

        :param str sysroot: a path to the root of the target system
        :param str default_desktop: default desktop to be set
        """
        super().__init__()
        self._sysroot = sysroot
        self._default_desktop = default_desktop

    @property
    def name(self):
        return "Configure default desktop"

    def run(self):
        if self._default_desktop:
            with open(os.path.join(self._sysroot + "etc/sysconfig/desktop"), "wt") as f:
                f.write("DESKTOP=%s\n" % self._default_desktop)
