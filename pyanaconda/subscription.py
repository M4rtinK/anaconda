#
# Subscription related helper functions.
#
# Copyright (C) 2020  Red Hat, Inc.  All rights reserved.
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

from pyanaconda.modules.common.constants.namespaces import SUBSCRIPTION_NAMESPACE
from pyanaconda.modules.common.constants.services import BOSS


def check_subscription_module_available():
    """Check if the Subscription module appears to be running.

    :return: True if Subscription module is running, False otherwise
    :rtype: bool
    """
    boss_proxy = BOSS.get_proxy()
    subscription_module_name = ".".join(SUBSCRIPTION_NAMESPACE)
    return subscription_module_name in boss_proxy.GetModules()
