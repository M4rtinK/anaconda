#
# Copyright (C) 2019  Red Hat, Inc.
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
from blivet.formats import get_format
from pykickstart.errors import KickstartParseError

from pyanaconda.anaconda_loggers import get_module_logger
from pyanaconda.core.i18n import _
from pyanaconda.modules.common.constants.objects import MANUAL_PARTITIONING
from pyanaconda.modules.common.constants.services import STORAGE
from pyanaconda.modules.common.structures.partitioning import MountPointRequest
from pyanaconda.modules.storage.partitioning.noninteractive_partitioning import \
    NonInteractivePartitioningTask

log = get_module_logger(__name__)

__all__ = ["ManualPartitioningTask"]


class ManualPartitioningTask(NonInteractivePartitioningTask):
    """A task for the manual partitioning configuration."""

    def _configure_partitioning(self, storage):
        """Configure the partitioning.

        :param storage: an instance of Blivet
        """
        log.debug("Setting up the mount points.")
        manual_part_proxy = STORAGE.get_proxy(MANUAL_PARTITIONING)

        # Set up mount points.
        for mount_data in manual_part_proxy.Requests:
            self._setup_mount_point(storage, MountPointRequest.from_structure(mount_data))

    def _setup_mount_point(self, storage, mount_data):
        """Set up a mount point.

        :param storage: an instance of the Blivet's storage object
        :param mount_data: an instance of MountPointRequest
        """
        device_spec = mount_data.device_spec
        reformat = mount_data.reformat
        format_type = mount_data.format_type

        device = storage.devicetree.resolve_device(device_spec)
        if device is None:
            raise KickstartParseError(_("Unknown or invalid device '%s' specified") % device_spec)

        if reformat:
            if format_type:
                fmt = get_format(format_type)

                if not fmt:
                    raise KickstartParseError(
                        _("Unknown or invalid format '%(format)s' specified for device "
                          "'%(device)s'") % {"format": format_type, "device": device_spec}
                    )
            else:
                old_fmt = device.format

                if not old_fmt or old_fmt.type is None:
                    raise KickstartParseError(_("No format on device '%s'") % device_spec)

                fmt = get_format(old_fmt.type)
            storage.format_device(device, fmt)
            # make sure swaps end up in /etc/fstab
            if fmt.type == "swap":
                storage.add_fstab_swap(device)

        # only set mount points for mountable formats
        mount_point = mount_data.mount_point

        if device.format.mountable and mount_point and mount_point != "none":
            device.format.mountpoint = mount_point

        device.format.create_options = mount_data.format_options
        device.format.options = mount_data.mount_options
