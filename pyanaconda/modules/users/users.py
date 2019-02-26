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
from pyanaconda.core.kickstart.commands import GroupData as GroupKickstartData
from pyanaconda.core.kickstart.commands import SshKeyData as SshKeyKickstartData
from pyanaconda.modules.common.base import KickstartModule
from pyanaconda.modules.common.constants.services import USERS
from pyanaconda.modules.common.structures.user import UserData
from pyanaconda.modules.common.structures.group import GroupData
from pyanaconda.modules.common.structures.sshkey import SshKeyData
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

        self.groups_changed = Signal()
        self._groups = []

        self.ssh_keys_changed = Signal()
        self._ssh_keys = []

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

        group_data_list = []
        for group_ksdata in data.group.groupList:
            group_data = self.create_group_data()
            group_data.name = ksdata.name
            if group_ksdata.gid == None:
                group_data.gid = -1
            else:
                group_data.gid = ksdata.gid
            group_data_list.append(group_data)
        self.set_groups(group_data_list)

        ssh_key_data_list = []
        for ssh_key_ksdata in data.sshkey.sshUserList:
            ssh_key_data = self.create_ssh_key_data()
            ssh_key_data.key = ksdata.key
            ssh_key_data.username = ksdata.username
            ssh_key_data_list.append(ssh_key_data)
        self.set_ssh_keys(ssh_key_data_list)

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

        for group_data in self.groups:
            group_ksdata = GroupKickstartData()
            group_ksdata.name = group_data.name
            if group_data.gid == -1:
                group_data.gid = None
            else:
                group_ksdata.gid = group_data.gid
            data.group.groupList.append(group_ksdata)

        for ssh_key_data in self.ssh_keys:
            ssh_key_ksdata = SshKeyKickstartData()
            ssh_key_ksdata.key = ssh_key_data.key
            ssh_key_ksdata.username = ssh_key_data.username
            data.sshkey.sshUserList.append(ssh_key_ksdata)

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
    def groups(self):
        """List of DBUS structures, one per group."""
        return self._groups

    def set_groups(self, groups):
        """Set the list of DBUS structures, one per group."""
        self._groups = groups
        self.groups_changed.emit()
        log.debug("A new group list has been set: %s", self._groups)

    def create_group_data(self):
        """Create an empty GroupData instance."""
        return GroupData()

    @property
    def ssh_keys(self):
        """List of DBUS structures, one per ssh key."""
        return self._ssh_keys

    def set_ssh_keys(self, ssh_keys):
        """Set the list of DBUS structures, one per ssh keys."""
        self._ssh_keys = ssh_keys
        self.ssh_keys_changed.emit()
        log.debug("A new ssh key list has been set: %s", self._ssh_keys)

    def create_ssh_key_data(self):
        """Create an empty SshKeyData instance."""
        return SshKeyData()

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
