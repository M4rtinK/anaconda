#
# Copyright (C) 2020  Red Hat, Inc.
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
# Red Hat Author(s): Martin Kolman <mkolman@redhat.com>
#
import os
import tempfile

import unittest
from unittest.mock import patch

from pyanaconda.core import util
from pyanaconda.core.constants import RHSM_SYSPURPOSE_FILE_PATH

from pyanaconda.subscription import check_subscription_module_available, check_system_purpose_set


class CheckSubscriptionAvailableTestCase(unittest.TestCase):
    """Test the check_subscription_module_available helper function."""

    @patch("pyanaconda.modules.common.constants.services.BOSS.get_proxy")
    def subcription_module_available_test(self, get_proxy):
        """Test the check_subscription_module_available() function - module available."""
        # mock the Boss proxy
        boss_proxy = get_proxy.return_value
        # make sure it returns a list containing the Subscription module
        running_modules = [
            "org.fedoraproject.Anaconda.Modules.Timezone",
            "org.fedoraproject.Anaconda.Modules.Network",
            "org.fedoraproject.Anaconda.Modules.Localization",
            "org.fedoraproject.Anaconda.Modules.Security",
            "org.fedoraproject.Anaconda.Modules.Users",
            "org.fedoraproject.Anaconda.Modules.Payloads",
            "org.fedoraproject.Anaconda.Modules.Storage",
            "org.fedoraproject.Anaconda.Modules.Services",
            "org.fedoraproject.Anaconda.Modules.Subscription",
         ]
        boss_proxy.GetModules.return_value = running_modules
        # call the function
        self.assertTrue(check_subscription_module_available())

    @patch("pyanaconda.modules.common.constants.services.BOSS.get_proxy")
    def subcription_module_not_available_test(self, get_proxy):
        """Test the check_subscription_module_available() function - module not available."""
        # mock the Boss proxy
        boss_proxy = get_proxy.return_value
        # make sure it returns a list not containing the Subscription module
        running_modules = [
            "org.fedoraproject.Anaconda.Modules.Timezone",
            "org.fedoraproject.Anaconda.Modules.Network",
            "org.fedoraproject.Anaconda.Modules.Localization",
            "org.fedoraproject.Anaconda.Modules.Security",
            "org.fedoraproject.Anaconda.Modules.Users",
            "org.fedoraproject.Anaconda.Modules.Payloads",
            "org.fedoraproject.Anaconda.Modules.Storage",
            "org.fedoraproject.Anaconda.Modules.Services",
         ]
        boss_proxy.GetModules.return_value = running_modules
        # call the function
        self.assertFalse(check_subscription_module_available())


class CheckSystemPurposeSetTestCase(unittest.TestCase):
    """Test the check_system_purpose_set helper function."""

    def check_system_purpose_set_test(self):
        """Test the check_system_purpose_set() helper function."""
        # system purpose set
        with tempfile.TemporaryDirectory() as sysroot:
            # create a dummy syspurpose file
            syspurpose_path = RHSM_SYSPURPOSE_FILE_PATH
            directory = os.path.split(syspurpose_path)[0]
            os.makedirs(util.join_paths(sysroot, directory))
            os.mknod(util.join_paths(sysroot, syspurpose_path))
            self.assertTrue(check_system_purpose_set(sysroot))

        # system purpose not set
        with tempfile.TemporaryDirectory() as sysroot:
            self.assertFalse(check_system_purpose_set(sysroot))
