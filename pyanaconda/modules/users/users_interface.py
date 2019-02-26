#
# DBus interface for the users module.
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

from pyanaconda.modules.common.constants.services import USERS
from pyanaconda.dbus.property import emits_properties_changed
from pyanaconda.dbus.typing import *  # pylint: disable=wildcard-import
from pyanaconda.modules.common.base import KickstartModuleInterface
from pyanaconda.dbus.interface import dbus_interface
from pyanaconda.dbus.structure import get_structure, apply_structure


@dbus_interface(USERS.interface_name)
class UsersInterface(KickstartModuleInterface):
    """DBus interface for Users module."""

    def connect_signals(self):
        super().connect_signals()
        self.watch_property("Users", self.implementation.users_changed)
        self.watch_property("Groups", self.implementation.groups_changed)
        self.watch_property("SshKeys", self.implementation.ssh_keys_changed)
        self.watch_property("IsRootPasswordSet", self.implementation.root_password_is_set_changed)
        self.watch_property("IsRootAccountLocked", self.implementation.root_account_locked_changed)
        self.watch_property("IsRootpwKickstarted", self.implementation.rootpw_seen_changed)

    @property
    def IsRootpwKickstarted(self) -> Bool:
        """Was the rootpw command seen in kickstart ?

        NOTE: this property should be only temporary and should be
              dropped once the users module itself can report
              if the password changed from kickstart

        :return: True, if the rootpw was present in input kickstart, otherwise False
        """
        return self.implementation.rootpw_seen

    @emits_properties_changed
    def SetRootpwKickstarted(self, rootpw_seen: Bool):
        """Set if rootpw should be considered as coming from kickstart.

        NOTE: this property should be only temporary and should be
              dropped once the users module itself can report
              if the password changed from kickstart

        :param bool rootpw_seen: if rootpw should be considered as coming from kickstart
        """
        self.implementation.set_rootpw_seen(rootpw_seen)

    @property
    def RootPassword(self) -> Str:
        """Root password.

        NOTE: this property should be only temporary and should be
              dropped once the users module itself can configure the root password

        :return: root password (might be crypted)
        """
        return self.implementation.root_password

    @property
    def IsRootPasswordCrypted(self) -> Bool:
        """Is the root password crypted ?

        NOTE: this property should be only temporary and should be
              dropped once the users module itself can configure the root password

        :return: True, if the root password is crypted, otherwise False
        """
        return self.implementation.root_password_is_crypted

    @emits_properties_changed
    def SetCryptedRootPassword(self, crypted_root_password: Str):
        """Set the root password.

        The password is expected to be provided in already crypted.

        :param crypted_root_password: already crypted root password
        """
        self.implementation.set_root_password(crypted_root_password, crypted=True)

    @emits_properties_changed
    def ClearRootPassword(self):
        """Clear any set root password."""
        self.implementation.clear_root_password()

    @property
    def IsRootPasswordSet(self) -> Bool:
        """Is the root password set ?

        :return: True, if the root password is set, otherwise False
        """
        return self.implementation.root_password_is_set

    @emits_properties_changed
    def SetRootAccountLocked(self, root_account_locked: Bool):
        """Lock or unlock the root account."""
        self.implementation.set_root_account_locked(root_account_locked)

    @property
    def IsRootAccountLocked(self) -> Bool:
        """Is the root account locked ?

        :return: True, if the root account is locked, otherwise False
        """
        return self.implementation.root_account_locked


    @property
    def Users(self) -> List[Structure]:
        """List of DBUS structures, each describing a single user.

        :return: a list of user describing DBUS Structures
        """
        # internally we hold the data about users as a list of structures,
        # which we need to turn into a list of dicts before returning it
        # over DBUS
        user_dicts = []

        for user_struct in self.implementation.users:
            user_dicts.append(get_structure(user_struct))
        return user_dicts

    @emits_properties_changed
    def SetUsers(self, users: List[Structure]):
        """Set a list of DBUS structures, each corresponding to a single user.

        :param users: a list of user describing DBUS structures
        """
        user_data_list = []
        for user_struct in users:
            user_data = self.implementation.create_user_data()
            apply_structure(user_struct, user_data)
            user_data_list.append(user_data)
        self.implementation.set_users(user_data_list)

    @property
    def Groups(self) -> List[Structure]:
        """List of DBUS structures, each describing a single group.

        :return: a list of group describing DBUS Structures
        """
        # internally we hold the data about groups as a list of structures,
        # which we need to turn into a list of dicts before returning it
        # over DBUS
        group_dicts = []

        for group_struct in self.implementation.groups:
            group_dicts.append(get_structure(group_struct))
        return group_dicts

    @emits_properties_changed
    def SetGroups(self, groups: List[Structure]):
        """Set a list of DBUS structures, each corresponding to a single group.

        :param groups: a list of group describing DBUS structures
        """
        group_data_list = []
        for group_struct in groups:
            group_data = self.implementation.create_group_data()
            apply_structure(group_struct, group_data)
            group_data_list.append(group_data)
        self.implementation.set_groups(group_data_list)

    @property
    def SshKeys(self) -> List[Structure]:
        """List of DBUS structures, each describing a single SSH key.

        :return: a list of SSH key describing DBUS Structures
        """
        # internally we hold the data about SSH keys as a list of structures,
        # which we need to turn into a list of dicts before returning it
        # over DBUS
        ssh_key_dicts = []

        for ssh_key_struct in self.implementation.ssh_keys:
            ssh_key_dicts.append(get_structure(ssh_key_struct))
        return ssh_key_dicts

    @emits_properties_changed
    def SetSshKeys(self, ssh_keys: List[Structure]):
        """Set a list of DBUS structures, each corresponding to a single SSH key.

        :param ssh_keys: a list of SSH key describing DBUS structures
        """
        ssh_key_data_list = []
        for ssh_key_struct in ssh_keys:
            ssh_key_data = self.implementation.create_ssh_key_data()
            apply_structure(ssh_key_struct, ssh_key_data)
            ssh_key_data_list.append(ssh_key_data)
        self.implementation.set_ssh_keys(ssh_key_data_list)
