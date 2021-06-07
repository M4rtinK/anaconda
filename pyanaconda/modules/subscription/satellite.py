#
# Satellite support purpose library.
#
# Copyright (C) 2020 Red Hat, Inc.
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

from requests import RequestException

from pyanaconda.core import constants, util

# FIXME: move this to core ? use different user agent
#        without product version information ?
from pyanaconda.payload.dnf.utils import USER_AGENT

# maybe move this as well ?
from pyanaconda.core.payload import ProxyString, ProxyStringError

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)

# the well-known path of the Satellite instance URL where
# the provisioning script should be located
PROVISIONING_SCRIPT_SUB_PATH = "/pub/katello-rhsm-consumer"
# where to store the downloaded provisioning script
PROVISIONING_SCRIPT_DOWNLOAD_PATH = "/tmp/katello-rhsm-consumer"


def download_satellite_provisioning_script(satellite_url, proxy_url=None):
    """Download provisioning script from a Red Hat Satellite instance.

    Download the provisioning script from a Satellite instance and store it
    to a local file.

    Satellite instances usually have self signed certificates and also some tweaks
    are usually required in rhsm.conf to connect to a customer run Satellite instance
    instead of to Hosted Candlepin for subscription purposes.

    Each Satellite instance thus hosts a provisioning script available over plain
    HTTP that client machines ca fetch and execute. This script has minimal dependencies
    and provisions the machine to be able to talk to the one given Satellite instance
    by installing it's self signed certificates and adjusting rhsm.conf.

    NOTE: As the script is downloaded over plain HTTP is is adviced to ever only
          provision machines from a Satellite instance on a trusted network, to
          avoid the possibility of the provisioning script being tempered with
          during transit.


    :param str satellite_url: Satellite instance URL
    :param proxy_url: proxy URL to use when fetchign the script
    :type proxy_url: str or None if not set
    :returns: True on success, False otherwise
    """

    # construct the URL pointing to the provisioning script
    # FIXME: do this more clenly ? include the protocol in the URL ?
    script_url = "https://" + satellite_url + PROVISIONING_SCRIPT_SUB_PATH

    log.debug("subscription: fetching Satellite provisioning script from: %s", script_url)

    headers = {"user-agent": USER_AGENT}
    proxies = {}
    provisioning_script = ""

    if proxy_url is not None:
        try:
            proxy = ProxyString(self._proxy_url)
            proxies = {"http": proxy.url,
                       "https": proxy.url}
        except ProxyStringError as e:
            log.info("subscription: failed to parse proxy when fetching Satellite"
                     " provisioning script %s: %s",
                     proxy_url, e)

    session = util.requests_session()

    try:
        # NOTE: we explicitely don't verify SSL certificates while
        #       downloading the provisioning script as the Satellite
        #       instance will have it's own self signed certs that
        #       will only be trusted once the provisioning script runs
        result = session.get(script_url, headers=headers,
                             proxies=proxies, verify=False,
                             timeout=constants.NETWORK_CONNECTION_TIMEOUT)
        if result.ok:
            provisioning_script = result.text
            result.close()
        else:
            log.debug("subscription: server returned %i code when downloading"
                      " Satellite provisioning script", result.status_code)
            result.close()
    except RequestException as e:
        log.debug("subscription: can't download Satellite provisioning script"
                  " from %s with proxy: %s. Error: %s", script_url, proxies, e)

    if provisioning_script:
        log.debug("subscription: writing Satellite provisioning script to file: %s",
                  PROVISIONING_SCRIPT_DOWNLOAD_PATH)
        with open(PROVISIONING_SCRIPT_DOWNLOAD_PATH, "wt") as f:
            f.write(provisioning_script)
        # successfully downloaded and writen out the Satellite provisioning script
        return True
    else:
        # failed to download the Satellite provisioning script
        return False


def run_satellite_provisioning_script(sysroot):
    """Run the Satellite provisioning script.

    Each Satellite instance provides a provisioning script that will
    enable the currently running environment to talk to the given
    Satellite instance.

    This mainly menas that the self-signed certificates of the given
    Satellite instance will be installed to the system but also some
    necessary changes to rhsm.conf.

    Also as we need to provision both the installation *and* target system
    to talk to Satellite we need to run the provisioning script twice,
    once in the installation environment and once on the target system.

    This is achieved by running this function repeatedly with the root
    parameter set accordingly.

    :param str sysroot: system root where to run the provisioning script
    :return: True on success, False otherwise
    :rtype: bool
    """

    # FIXME: do we need to copy the script to the chroot to execute ?
    if os.path.exists(PROVISIONING_SCRIPT_DOWNLOAD_PATH):
        log.debug("subscription: executing Satellite provisioning script.")
        rc = util.execWithRedirect("bash", argv=[PROVISIONING_SCRIPT_DOWNLOAD_PATH], root=sysroot)
        if rc == 0:
            log.debug("subscription: satellite provisioning script executed successfully")
            return True
        else:
            log.debug("subscription: satellite provisioning script executed with error")
            return False
        return True
    else:
        log.warning("subscriotion: satellite provisioning script not found in: %s",
                    PROVISIONING_SCRIPT_DOWNLOAD_PATH)
        return False
