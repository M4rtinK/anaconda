#
# Kickstart module for the users module.
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
from pyanaconda.dbus import DBus
from pyanaconda.core.signal import Signal
from pyanaconda.core.kickstart.commands import User
from pyanaconda.core.kickstart.commands import UserData as UserKickstartData
from pyanaconda.modules.common.base import KickstartModule
from pyanaconda.modules.common.constants.services import USERS
from pyanaconda.modules.common.structures.user import UserData
from pyanaconda.modules.users.user import UserModule, UserInterface
from pyanaconda.modules.users.kickstart import UsersKickstartSpecification
from pyanaconda.modules.users.users_interface import UsersInterface

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)


def apply_ksdata_to_user_data(user_data, user_ksdata):
    """Apply kickstart user command data to UserData instance.

    :param user_data: a UserData instance
    :param user_ksdata: data for the kickstart user command
    :return: UserData instance with kickstart data applied
    """
    user_data.name = user_ksdata.name
    user_data.groups = user_ksdata.groups
    # To denote that a value has not been set:
    # - kickstart uses None
    # - our DBUS API uses -1
    # We need to make sure we correctly convert between these two.
    if user_ksdata.uid is None:
        user_data.uid = -1
    else:
        user_data.uid = user_ksdata.uid
    if user_ksdata.gid is None:
        user_data.gid = -1
    else:
        user_data.gid = user_ksdata.gid
    user_data.homedir = user_ksdata.homedir
    user_data.password = user_ksdata.password
    user_data.is_crypted = user_ksdata.isCrypted
    user_data.lock = user_ksdata.lock
    user_data.shell = user_ksdata.shell
    user_data.gecos = user_ksdata.gecos
    return user_data

def user_data_to_ksdata(user_data):
    """Convert UserData instance to kickstart user command data.

    :param user_structure: UserData instance
    :return: kickstart user command data for a single user
    """
    user_ksdata = UserKickstartData()
    user_ksdata.name = user_data.name
    user_ksdata.groups = user_data.groups
    # To denote that a value has not been set:
    # - kickstart uses None
    # - our DBUS API uses -1
    # We need to make sure we correctly convert between these two.
    if user_data.uid == -1:
        user_ksdata.uid = None
    else:
        user_ksdata.uid = user_data.uid
    if user_data.gid == -1:
        user_ksdata.gid = None
    else:
        user_ksdata.gid = user_data.gid
    user_ksdata.homedir = user_data.homedir
    user_ksdata.password = user_data.password
    user_ksdata.isCrypted = user_data.is_crypted
    user_ksdata.lock = user_data.lock
    user_ksdata.shell = user_data.shell
    user_ksdata.gecos = user_data.gecos
    return user_ksdata

class UsersModule(KickstartModule):
    """The Users module."""

    def __init__(self):
        super().__init__()
        self.rootpw_seen_changed = Signal()
        self._rootpw_seen = False

        self.root_password_is_set_changed = Signal()
        self._root_password_is_set = False
        self._root_password = ""
        self._root_password_is_crypted = False

        self.root_account_locked_changed = Signal()
        self._root_account_locked = False

        self.users_changed = Signal()
        self._users = []

    def publish(self):
        """Publish the module."""
        DBus.publish_object(USERS.object_path, UsersInterface(self))
        DBus.register_service(USERS.service_name)

    @property
    def kickstart_specification(self):
        """Return the kickstart specification."""
        return UsersKickstartSpecification

    def process_kickstart(self, data):
        """Process the kickstart data."""
        log.debug("Processing kickstart data...")
        self.set_root_password(data.rootpw.password, crypted=data.rootpw.isCrypted)
        self.set_root_account_locked(data.rootpw.lock)
        self.set_rootpw_seen(data.rootpw.seen)

        user_data_list = []
        for user_ksdata in data.user.userList:
            user_data = self.create_user_data()
            user_data = apply_ksdata_to_user_data(user_data, user_ksdata)
            user_data_list.append(user_data)
        self.set_users(user_data_list)

    # pylint: disable=arguments-differ
    def generate_kickstart(self):
        """Return the kickstart string."""
        log.debug("Generating kickstart data...")
        data = self.get_kickstart_handler()
        data.rootpw.password = self._root_password
        data.rootpw.isCrypted = self._root_password_is_crypted
        data.rootpw.lock = self.root_account_locked
        data.rootpw.seen = self.rootpw_seen

        for user_data in self.users:
            data.user.userList.append(user_data_to_ksdata(user_data))

        return str(data)

    @property
    def users(self):
        """List of DBUS structures, one per user."""
        return self._users

    def set_users(self, users):
        """Set the list of DBUS structures, one per user."""
        self._users = users
        self.users_changed.emit()
        log.debug("A new user list has been set (%d users).", len(self._users))

    def create_user_data(self):
        """Create an empty UserData instance."""
        return UserData()

    @property
    def rootpw_seen(self):
        return self._rootpw_seen

    def set_rootpw_seen(self, rootpw_seen):
        self._rootpw_seen = rootpw_seen
        self.rootpw_seen_changed.emit()
        log.debug("Root password considered seen in kickstart: %s.", rootpw_seen)

    @property
    def root_password(self):
        """The root password.

        :returns: root password (might be crypted)
        :rtype: str
        """
        return self._root_password

    @property
    def root_password_is_crypted(self):
        """Is the root password crypted ?

        :returns: if root password is crypted
        :rtype: bool
        """
        return self._root_password_is_crypted

    def set_root_password(self, root_password, crypted):
        """Set the crypted root password.

        :param str root_password: root password
        :param bool crypted: if the root password is crypted
        """
        self._root_password = root_password
        self._root_password_is_crypted = crypted
        self.root_password_is_set_changed.emit()
        log.debug("Root password set.")

    def clear_root_password(self):
        """Clear any set root password."""
        self._root_password = ""
        self._root_password_is_crypted = False
        self.root_password_is_set_changed.emit()
        log.debug("Root password cleared.")

    @property
    def root_password_is_set(self):
        """Is the root password set ?"""
        return bool(self._root_password)

    def set_root_account_locked(self, locked):
        """Lock or unlock the root account.

        :param bool locked: True id the account should be locked, False otherwise.
        """
        self._root_account_locked = locked
        self.root_account_locked_changed.emit()
        if locked:
            log.debug("Root account has been locked.")
        else:
            log.debug("Root account has been unlocked.")

    @property
    def root_account_locked(self):
        """Is the root account locked ?"""
        return self._root_account_locked
