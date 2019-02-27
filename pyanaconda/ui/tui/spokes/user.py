# User creation text spoke
#
# Copyright (C) 2013-2014  Red Hat, Inc.
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
from pyanaconda.core.constants import FIRSTBOOT_ENVIRON, PASSWORD_SET
from pyanaconda.flags import flags
from pyanaconda.core.i18n import N_, _
from pyanaconda.core.regexes import GECOS_VALID
from pyanaconda.modules.common.constants.services import USERS
from pyanaconda.modules.common.structures.user import UserData
from pyanaconda.dbus.structure import apply_structure, get_structure

from pyanaconda.ui.categories.user_settings import UserSettingsCategory
from pyanaconda.ui.common import FirstbootSpokeMixIn
from pyanaconda.ui.tui.spokes import NormalTUISpoke
from pyanaconda.ui.tui.tuiobject import Dialog, PasswordDialog, report_if_failed, report_check_func
from pyanaconda.core.users import guess_username, check_username, check_grouplist

from simpleline.render.screen import InputState
from simpleline.render.containers import ListColumnContainer
from simpleline.render.widgets import CheckboxWidget, EntryWidget

__all__ = ["UserSpoke"]


FULLNAME_ERROR_MSG = N_("Full name can't contain the ':' character")


class UserSpoke(FirstbootSpokeMixIn, NormalTUISpoke):
    """
       .. inheritance-diagram:: UserSpoke
          :parts: 3
    """
    helpFile = "UserSpoke.txt"
    category = UserSettingsCategory

    @classmethod
    def should_run(cls, environment, data):
        if FirstbootSpokeMixIn.should_run(environment, data):
            return True

        # the user spoke should run always in the anaconda and in firstboot only
        # when doing reconfig or if no user has been created in the installation
        user_list = self._get_user_list()
        if environment == FIRSTBOOT_ENVIRON and data and not user_list:
            return True

        return False

    def _get_user_list(self):
            return [apply_structure(user_struct, UserData) for user_struct in self._users_module.proxy.Users]

    def _set_user_list(self, user_data_list):
        """Properly set the user list in the Users DBUS module.

        Internally we are working with a list of UserData instances, while the SetUsers DBUS API
        requires a list of DBUS structures.

        Doing the conversion each time we need to set a new user list would be troublesome so
        this method takes a list of UserData instances, converts them to list of DBUS structs
        and then forwards the list to the Users module.

        :param user_data_list: list of user data objects
        :type user_data_list: list of UserData instances
        """
        self._users_module.proxy.SetUsers([get_structure(user_data) for user_data in user_data_list])


    def __init__(self, data, storage, payload):
        FirstbootSpokeMixIn.__init__(self)
        NormalTUISpoke.__init__(self, data, storage, payload)

        self.initialize_start()

        # connect to the Users DBUS module
        self._users_module = USERS.get_observer()
        self._users_module.connect()

        self.title = N_("User creation")
        self._container = None

        # was user creation requested by the Users DBUS module
        # - at the moment this basically means user creation was
        #   requested via kickstart
        self._user_requested = False

        # should a user be created ?
        self._create_user = False

        user_list = self._get_user_list()
        if user_list:
            # User creation was requested by the DBUS module and we have all the information needed
            # to create a user, even without further user interaction.
            self._user_data = user_list[0]
            self._create_user = True
            self._user_requested = True
        else:
            self._user_data = UserData()

        self._use_password = self._user_data.is_crypted or self._user_data.password
        self._groups = ""
        self._is_admin = False
        self._policy = self.data.anaconda.pwpolicy.get_policy("user", fallback_to_default=True)

        self.errors = []

        self._users_module = USERS.get_observer()
        self._users_module.connect()

        self.initialize_done()

    def refresh(self, args=None):
        NormalTUISpoke.refresh(self, args)
        self._is_admin = "wheel" in self._user_data.groups
        self._groups = ", ".join(self._user_data.groups)

        self._container = ListColumnContainer(1)

        w = CheckboxWidget(title=_("Create user"), completed=self._create_user)
        self._container.add(w, self._set_create_user)

        if self._create_user:
            dialog = Dialog(title=_("Full name"), conditions=[self._check_fullname])
            self._container.add(EntryWidget(dialog.title, self._user_data.gecos), self._set_fullname, dialog)

            dialog = Dialog(title=_("User name"), conditions=[self._check_username])
            self._container.add(EntryWidget(dialog.title, self._user_data.name), self._set_username, dialog)

            w = CheckboxWidget(title=_("Use password"), completed=self._use_password)
            self._container.add(w, self._set_use_password)

            if self._use_password:
                password_dialog = PasswordDialog(title=_("Password"), policy=self._policy)
                if self._user_data.password:
                    entry = EntryWidget(password_dialog.title, _(PASSWORD_SET))
                else:
                    entry = EntryWidget(password_dialog.title)

                self._container.add(entry, self._set_password, password_dialog)

            msg = _("Administrator")
            w = CheckboxWidget(title=msg, completed=self._is_admin)
            self._container.add(w, self._set_administrator)

            dialog = Dialog(title=_("Groups"), conditions=[self._check_groups])
            self._container.add(EntryWidget(dialog.title, self._groups), self._set_groups, dialog)

        self.window.add_with_separator(self._container)

    @report_if_failed(message=FULLNAME_ERROR_MSG)
    def _check_fullname(self, user_input, report_func):
        return GECOS_VALID.match(user_input) is not None

    @report_check_func()
    def _check_username(self, user_input, report_func):
        return check_username(user_input)

    @report_check_func()
    def _check_groups(self, user_input, report_func):
        return check_grouplist(user_input)

    def _set_create_user(self, args):
        self._create_user = not self._create_user

    def _set_fullname(self, dialog):
        self._user_data.gecos = dialog.run()

    def _set_username(self, dialog):
        self._user_data.name = dialog.run()

    def _set_use_password(self, args):
        self._use_password = not self._use_password

    def _set_password(self, password_dialog):
        password = password_dialog.run()

        while password is None:
            password = password_dialog.run()

        self._user_data.password = password

    def _set_administrator(self, args):
        self._is_admin = not self._is_admin

    def _set_groups(self, dialog):
        self._groups = dialog.run()

    def show_all(self):
        NormalTUISpoke.show_all(self)
        # if we have any errors, display them
        while self.errors:
            print(self.errors.pop())

    @property
    def completed(self):
        """ Verify a user is created; verify pw is set if option checked. """
        user_list = self._get_user_list()
        if len(user_list) > 0:
            if self._use_password and not bool(self._user_data.password or self._user_data.is_crypted):
                return False
            else:
                return True
        else:
            return False

    @property
    def showable(self):
        return not (self.completed and flags.automatedInstall
                    and self._user_requested and not self._policy.changesok)

    @property
    def mandatory(self):
        """ Only mandatory if the root pw hasn't been set in the UI
            eg. not mandatory if the root account was locked in a kickstart
        """
        return not self._users_module.proxy.IsRootPasswordSet and not self._users_module.proxy.IsRootAccountLocked

    @property
    def status(self):
        user_list = self._get_user_list()
        if len(user_list) == 0:
            return _("No user will be created")
        elif self._use_password and not bool(self._user_data.password or self._user_data.is_crypted):
            return _("You must set a password")
        elif "wheel" in user_list[0].groups:
            return _("Administrator %s will be created") % user_list[0].name
        else:
            return _("User %s will be created") % user_list[0].name

    def input(self, args, key):
        if self._container.process_user_input(key):
            self.apply()
            return InputState.PROCESSED_AND_REDRAW

        return super().input(args, key)

    def apply(self):
        if self._user_data.gecos and not self._user_data.name:
            username = guess_username(self._user_data.gecos)
            valid, msg = check_username(username)
            if not valid:
                self.errors.append(_("Invalid user name: %(name)s.\n%(error_message)s")
                                   % {"name": username, "error_message": msg})
            else:
                self._user_data.name = guess_username(self._user_data.gecos)

        self._user_data.groups = [g.strip() for g in self._groups.split(",") if g]

        # Add or remove the user from wheel group
        if self._is_admin and "wheel" not in self._user_data.groups:
            self._user_data.groups.append("wheel")
        elif not self._is_admin and "wheel" in self._user_data.groups:
            self._user_data.groups.remove("wheel")

        # Add or remove the user from userlist as needed
        user_list = self._get_user_list()
        if self._create_user and (self._user_data not in user_list and self._user_data.name):
            new_user_list = user_list
            new_user_list.append(self._user_data)
            self._set_user_list(new_user_list)
        elif (not self._create_user) and (self._user_data in user_list):
            new_user_list = user_list
            new_user_list.remove(self._user_data)
            self._set_user_list(new_user_list)

        # encrypt and store password only if user entered anything; this should
        # preserve passwords set via kickstart
        if self._use_password and self._user_data.password and len(self._user_data.password) > 0:
            self._user_data.password = self._user_data.password
            self._user_data.is_crypted = True
        # clear pw when user unselects to use pw
        else:
            self._user_data.password = ""
            self._user_data.is_crypted = False
