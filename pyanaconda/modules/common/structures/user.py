#
# DBus structures for describing the user.
#
# Copyright (C) 2019  Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from pyanaconda.dbus.structure import dbus_structure
from pyanaconda.dbus.typing import *  # pylint: disable=wildcard-import

__all__ = ["UserData"]


@dbus_structure
class UserData(object):
    """User data."""

    def __init__(self):
        self._name = ""
        self._uid = -1
        self._groups = list()
        self._gid = -1
        self._homedir = ""
        self._password = ""
        self._is_crypted = True
        self._lock = False
        self._shell = ""
        self._gecos = ""

    @property
    def name(self) -> Str:
        """Username."

        For example: 'user'

        Should comply with the usual limitations for Linux usernames.

        :return: a username
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name: Str):
        self._name = name

    @property
    def uid(self) -> Int:
        """The users UID.

        If not provided, this defaults to the next available non-system UID.

        For examples: 1234

        Negative UID means that a valid UID has not been set.

        :return: users UID
        :rtype: int
        """
        return self._uid

    @uid.setter
    def uid(self, uid: Int):
        self._uid = uid

    @property
    def groups(self) -> List[Str]:
        """List of additional groups (in additional to the default group named after
        the user) the user should be a member of. Any groups that do not already
        exist will be created.

        For example: ['mock', 'dialout']

        :return: a list of groups the user should be a member of
        :rtype: a list of str
        """
        return self._groups

    @groups.setter
    def groups(self, groups: List[Str]):
        self._groups = groups

    @property
    def gid(self) -> Int:
        """The GID of the user’s primary group.

        If not provided,  defaults to the next available non-system GID.

        Negative GID means that a valid GID has not been set.

        For examples: 1234

        :return: primary group GID
        :rtype: int
        """
        return self._gid

    @gid.setter
    def gid(self, gid: Int):
        self._gid = gid


    @property
    def homedir(self) -> Str:
        """The home directory of the user.

        If not provided, this defaults to /home/.

        For example: 'user_home'

        :return: home directory of the user
        :rtype: str
        """
        return self._homedir

    @homedir.setter
    def homedir(self, homedir: Str):
        self._homedir = homedir

    @property
    def password(self) -> Str:
        """The user password.

        If not provided, the account will be locked by default. If this is set,
        the password argument is assumed to already be encrypted.

        If the plaintext property has been set, it has the opposite effect,
        the user password is assumed to not be encrypted.

        To create an encrypted password you can use python:

        python3 -c 'import crypt; print(crypt.crypt("My Password", "$6$My Sault"))'

        This will generate sha512 crypt of your password using your provided salt.

        For example: "CorrectHorseBatteryStaple"

        :return: user password
        :rtype: str
        """
        return self._password

    @password.setter
    def password(self, password: Str):
        self._password = password

    @property
    def is_crypted(self) -> Bool:
        """Reports if the password is already crypted.

        A password is considered to be crypted by default.

        For example: True

        :return: if password is already crypted
        :rtype: bool
        """
        return self._is_crypted

    @is_crypted.setter
    def is_crypted(self, is_crypted: Bool):
        self._is_crypted = is_crypted

    @property
    def lock(self) -> Bool:
        """If lock is True, this user account will be locked be locked.

        That is, the user will not be able to login from the console.

        For example: False

        :rtype: if the user account should be locked
        :rtype: bool
        """
        return self._lock

    @lock.setter
    def lock(self, lock: Bool):
        self._lock = lock

    @property
    def shell(self) -> Str:
        """The users login shell.

        If not provided this defaults to the system default.

        For example: "/bin/bash"

        :return: user login shell
        :rtype: str
        """
        return self._shell

    @shell.setter
    def shell(self, shell: Str):
        self._shell = shell

    @property
    def gecos(self) -> Str:
        """Provides the GECOS information for the user.

        This is a string of various system-specific fields separated by a comma.
        It is frequently used to specify the user’s full name, office number, and the like.
        See man 5 passwd for more details.

        For examples: "foo"

        :return: GECOS information for the user
        :rtype: str
        """
        return self._gecos

    @gecos.setter
    def gecos(self, gecos: Str):
        self._gecos = gecos
