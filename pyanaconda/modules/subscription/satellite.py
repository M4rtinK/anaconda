#
# Satellite support purpose library.
#
# Copyright (C) 2024 Red Hat, Inc.
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
import tempfile

from requests import RequestException

from pyanaconda.core import constants, util

from pyanaconda.core.payload import ProxyString, ProxyStringError
from pyanaconda.core.configuration.anaconda import conf
from pyanaconda.core.path import make_directories

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)

# the well-known path of the Satellite instance URL where
# the provisioning script should be located
PROVISIONING_SCRIPT_SUB_PATH = "/pub/katello-rhsm-consumer"

FIXED_SCRIPT = """#!/bin/bash

set -e

KATELLO_SERVER=dhcp123.anaconda.englab.brq.redhat.com
PORT=443

KATELLO_SERVER_CA_CERT=katello-server-ca.pem
KATELLO_DEFAULT_CA_CERT=katello-default-ca.pem

CERT_DIR=/etc/rhsm/ca
PREFIX=/rhsm
CFG=/etc/rhsm/rhsm.conf
CFG_BACKUP=$CFG.kat-backup
CA_TRUST_ANCHORS=/etc/pki/ca-trust/source/anchors

read -r -d '' KATELLO_DEFAULT_CA_DATA << EOM || true
-----BEGIN CERTIFICATE-----
MIIHGTCCBQGgAwIBAgIUTjwg8+HqbUvks6I9qZoZdtQEb/gwDQYJKoZIhvcNAQEL
BQAwgZExCzAJBgNVBAYTAlVTMRcwFQYDVQQIDA5Ob3J0aCBDYXJvbGluYTEQMA4G
A1UEBwwHUmFsZWlnaDEQMA4GA1UECgwHS2F0ZWxsbzEUMBIGA1UECwwLU29tZU9y
Z1VuaXQxLzAtBgNVBAMMJmRoY3AxMjMuYW5hY29uZGEuZW5nbGFiLmJycS5yZWRo
YXQuY29tMB4XDTI0MDgxMzE2MjkzOVoXDTM4MDExNzE2MjkzOVowgZExCzAJBgNV
BAYTAlVTMRcwFQYDVQQIDA5Ob3J0aCBDYXJvbGluYTEQMA4GA1UEBwwHUmFsZWln
aDEQMA4GA1UECgwHS2F0ZWxsbzEUMBIGA1UECwwLU29tZU9yZ1VuaXQxLzAtBgNV
BAMMJmRoY3AxMjMuYW5hY29uZGEuZW5nbGFiLmJycS5yZWRoYXQuY29tMIICIjAN
BgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAsxSo2qKB1DFHQJgLCghcwIWBB/6I
9MgKMGNZcx3ff3tF0BlAO+JY5WlywIuR47aoI8AjfdVPXxqRZsB7KGj9Ouyq6Hbp
Mc5cenGYBnK9m7IKM6MVouP4VmBD1oktVx42iVfWD9uMRCXVGQuOyjkdBhQpVuAi
+NPVoGDDtycJZv9u0LCsm80igb5f9dfMzyK0gqdE5THCkaM3yCrKh0W0TkxeGWrJ
uZXDw6ormLsSQu6QfOSiZapVguWmQ+MXoo4M7bwQehpqdb4tD0TZRMNcHiWp+TQ6
FFsdKid78L/y11WtUmFpVTMq/QQZ9D95QSy+lCHWlFPuuE4bq9/7Vx3vt09VeMkt
59ZFhQMHa2uLWDmqV1ByBN7XlFZQFgZM6p6h5V3PL4f0HQLe2xkchRNKaEYIjrHR
qzYDQNfNxr1oiTpbrqwRYBE3h0wj9fMzQ5sUVgbKphF9aJUS5mwy76gbgvZbI/n5
SKHKE1KonQhH4h2mBV8JAYB+k0kUDpiNaL2c6PnahOPKpi1umZT+Igpw/hHsx898
KI1O7M2k4n5UrmPEtqh/EZdspAE/YHjIpP1QGooGkrXX3yP7OqwUwf20sw34Parx
yPlCTPdpZAMlQowvnqNre+9w8DgXd8ZysWveB7SGzXp50hOZ0AgsTbHspGr5Ur7U
g5TXfYWWNdK22CkCAwEAAaOCAWUwggFhMAwGA1UdEwQFMAMBAf8wCwYDVR0PBAQD
AgGmMB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjARBglghkgBhvhCAQEE
BAMCAkQwNQYJYIZIAYb4QgENBCgWJkthdGVsbG8gU1NMIFRvb2wgR2VuZXJhdGVk
IENlcnRpZmljYXRlMB0GA1UdDgQWBBSSvVOZ7TDH+fqdozSAVJW3G0tfZDCBuwYD
VR0jBIGzMIGwoYGXpIGUMIGRMQswCQYDVQQGEwJVUzEXMBUGA1UECAwOTm9ydGgg
Q2Fyb2xpbmExEDAOBgNVBAcMB1JhbGVpZ2gxEDAOBgNVBAoMB0thdGVsbG8xFDAS
BgNVBAsMC1NvbWVPcmdVbml0MS8wLQYDVQQDDCZkaGNwMTIzLmFuYWNvbmRhLmVu
Z2xhYi5icnEucmVkaGF0LmNvbYIUTjwg8+HqbUvks6I9qZoZdtQEb/gwDQYJKoZI
hvcNAQELBQADggIBAG/dLM6icFdLRyw6EFnPstM2wFmxVxF3LyabaXG54syBZa7I
lQObDStF8ZroViuLBjgXzC8PRC5bdurKAbvS2UGHb5UUM5mtE2DGBXDsV0caWsiJ
SCDMGzKvlhHuMpUyq6rrD3JMzGkLLMROGKUWlzayB83Oj0m7x1krycY7K+Z5kK+J
Thd4dwlLBjBWw4/1m24CmORoY3zVqFNTJFAVvzZpUr4OCTkyf+SFbxg3vdFGsQAv
I6r0HxSX2Bcds5WZP5k5rmMg7XwAuPJ3ZqLg5imiNtF39uVEeEESljKqOYXv9egI
BFhwxfpLXmmlJlPFmbsj87956J47IV7LISLlCx1YXJ4AIQhSjp1g7rNk9vwvbaaP
Mb/xYKL4YFEW8HdXye558RIrf23Mx858F/WKQHfB3TxmL0j3qheUPEsc+H3q23k3
R4n3/ZtclTSI6xGWuj+vT8VNuAv5rseiVDaoZAeiwyvWfLk1+dDxfzSdIyjA6zUd
MxlUUU6HB1kjaGyZM8CwOkk2RcDiiyEgfpmM4G7QcRko2UjuVmfB3fAujODR9abA
Y8fUHPPetgSIQd0Mp1x7iowaYDmSYr9HBzceLI6AlYirlyhppUHkKT4BYlZHd9EZ
86T35+xXiz5eaq0NnHLIAFOuQ23qitKW2lTT9YNwLTzi53PunXsdcqTjD+zT
-----END CERTIFICATE-----

EOM

read -r -d '' KATELLO_SERVER_CA_DATA << EOM || true
-----BEGIN CERTIFICATE-----
MIIHGTCCBQGgAwIBAgIUTjwg8+HqbUvks6I9qZoZdtQEb/gwDQYJKoZIhvcNAQEL
BQAwgZExCzAJBgNVBAYTAlVTMRcwFQYDVQQIDA5Ob3J0aCBDYXJvbGluYTEQMA4G
A1UEBwwHUmFsZWlnaDEQMA4GA1UECgwHS2F0ZWxsbzEUMBIGA1UECwwLU29tZU9y
Z1VuaXQxLzAtBgNVBAMMJmRoY3AxMjMuYW5hY29uZGEuZW5nbGFiLmJycS5yZWRo
YXQuY29tMB4XDTI0MDgxMzE2MjkzOVoXDTM4MDExNzE2MjkzOVowgZExCzAJBgNV
BAYTAlVTMRcwFQYDVQQIDA5Ob3J0aCBDYXJvbGluYTEQMA4GA1UEBwwHUmFsZWln
aDEQMA4GA1UECgwHS2F0ZWxsbzEUMBIGA1UECwwLU29tZU9yZ1VuaXQxLzAtBgNV
BAMMJmRoY3AxMjMuYW5hY29uZGEuZW5nbGFiLmJycS5yZWRoYXQuY29tMIICIjAN
BgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAsxSo2qKB1DFHQJgLCghcwIWBB/6I
9MgKMGNZcx3ff3tF0BlAO+JY5WlywIuR47aoI8AjfdVPXxqRZsB7KGj9Ouyq6Hbp
Mc5cenGYBnK9m7IKM6MVouP4VmBD1oktVx42iVfWD9uMRCXVGQuOyjkdBhQpVuAi
+NPVoGDDtycJZv9u0LCsm80igb5f9dfMzyK0gqdE5THCkaM3yCrKh0W0TkxeGWrJ
uZXDw6ormLsSQu6QfOSiZapVguWmQ+MXoo4M7bwQehpqdb4tD0TZRMNcHiWp+TQ6
FFsdKid78L/y11WtUmFpVTMq/QQZ9D95QSy+lCHWlFPuuE4bq9/7Vx3vt09VeMkt
59ZFhQMHa2uLWDmqV1ByBN7XlFZQFgZM6p6h5V3PL4f0HQLe2xkchRNKaEYIjrHR
qzYDQNfNxr1oiTpbrqwRYBE3h0wj9fMzQ5sUVgbKphF9aJUS5mwy76gbgvZbI/n5
SKHKE1KonQhH4h2mBV8JAYB+k0kUDpiNaL2c6PnahOPKpi1umZT+Igpw/hHsx898
KI1O7M2k4n5UrmPEtqh/EZdspAE/YHjIpP1QGooGkrXX3yP7OqwUwf20sw34Parx
yPlCTPdpZAMlQowvnqNre+9w8DgXd8ZysWveB7SGzXp50hOZ0AgsTbHspGr5Ur7U
g5TXfYWWNdK22CkCAwEAAaOCAWUwggFhMAwGA1UdEwQFMAMBAf8wCwYDVR0PBAQD
AgGmMB0GA1UdJQQWMBQGCCsGAQUFBwMBBggrBgEFBQcDAjARBglghkgBhvhCAQEE
BAMCAkQwNQYJYIZIAYb4QgENBCgWJkthdGVsbG8gU1NMIFRvb2wgR2VuZXJhdGVk
IENlcnRpZmljYXRlMB0GA1UdDgQWBBSSvVOZ7TDH+fqdozSAVJW3G0tfZDCBuwYD
VR0jBIGzMIGwoYGXpIGUMIGRMQswCQYDVQQGEwJVUzEXMBUGA1UECAwOTm9ydGgg
Q2Fyb2xpbmExEDAOBgNVBAcMB1JhbGVpZ2gxEDAOBgNVBAoMB0thdGVsbG8xFDAS
BgNVBAsMC1NvbWVPcmdVbml0MS8wLQYDVQQDDCZkaGNwMTIzLmFuYWNvbmRhLmVu
Z2xhYi5icnEucmVkaGF0LmNvbYIUTjwg8+HqbUvks6I9qZoZdtQEb/gwDQYJKoZI
hvcNAQELBQADggIBAG/dLM6icFdLRyw6EFnPstM2wFmxVxF3LyabaXG54syBZa7I
lQObDStF8ZroViuLBjgXzC8PRC5bdurKAbvS2UGHb5UUM5mtE2DGBXDsV0caWsiJ
SCDMGzKvlhHuMpUyq6rrD3JMzGkLLMROGKUWlzayB83Oj0m7x1krycY7K+Z5kK+J
Thd4dwlLBjBWw4/1m24CmORoY3zVqFNTJFAVvzZpUr4OCTkyf+SFbxg3vdFGsQAv
I6r0HxSX2Bcds5WZP5k5rmMg7XwAuPJ3ZqLg5imiNtF39uVEeEESljKqOYXv9egI
BFhwxfpLXmmlJlPFmbsj87956J47IV7LISLlCx1YXJ4AIQhSjp1g7rNk9vwvbaaP
Mb/xYKL4YFEW8HdXye558RIrf23Mx858F/WKQHfB3TxmL0j3qheUPEsc+H3q23k3
R4n3/ZtclTSI6xGWuj+vT8VNuAv5rseiVDaoZAeiwyvWfLk1+dDxfzSdIyjA6zUd
MxlUUU6HB1kjaGyZM8CwOkk2RcDiiyEgfpmM4G7QcRko2UjuVmfB3fAujODR9abA
Y8fUHPPetgSIQd0Mp1x7iowaYDmSYr9HBzceLI6AlYirlyhppUHkKT4BYlZHd9EZ
86T35+xXiz5eaq0NnHLIAFOuQ23qitKW2lTT9YNwLTzi53PunXsdcqTjD+zT
-----END CERTIFICATE-----

EOM

is_debian()
{
  if [ -r "/etc/os-release" ]
  then
    ID="$(sed -n -e "s/^ID\s*=\s*\(.*\)/\1/p" /etc/os-release)"
    ID_LIKE="$(sed -n -e "s/^ID_LIKE\s*=\s*\(.*\)/\1/p" /etc/os-release)"

    if [ "$ID" = "debian" ] ||       # Debian
       [ "$ID_LIKE" = "debian" ] ||  # e.g Ubuntu
       [ "$ID_LIKE" = "ubuntu" ]     # e.g. Linux Mint
    then
      return 0
    fi
  fi
  return 1
}

# exit on non-RHEL systems or when rhsm.conf is not found
test -f $CFG || exit
type -P subscription-manager >/dev/null || type -P subscription-manager-cli >/dev/null || exit

# backup configuration during the first run
test -f $CFG_BACKUP || cp $CFG $CFG_BACKUP

# create the cert
echo "$KATELLO_SERVER_CA_DATA" > $CERT_DIR/$KATELLO_SERVER_CA_CERT
chmod 644 $CERT_DIR/$KATELLO_SERVER_CA_CERT

echo "$KATELLO_DEFAULT_CA_DATA" > $CERT_DIR/$KATELLO_DEFAULT_CA_CERT
chmod 644 $CERT_DIR/$KATELLO_DEFAULT_CA_CERT

if is_debian
then
  # Debian setup
  BASEURL=https://$KATELLO_SERVER/pulp/deb

  subscription-manager config \
    --server.hostname="$KATELLO_SERVER" \
    --server.prefix="$PREFIX" \
    --server.port="$PORT" \
    --rhsm.repo_ca_cert="%(ca_cert_dir)s$KATELLO_SERVER_CA_CERT" \
    --rhsm.baseurl="$BASEURL"
else
  # rhel setup
  BASEURL=https://$KATELLO_SERVER/pulp/content/

  subscription-manager config \
    --server.hostname="$KATELLO_SERVER" \
    --server.prefix="$PREFIX" \
    --server.port="$PORT" \
    --rhsm.repo_ca_cert="%(ca_cert_dir)s$KATELLO_SERVER_CA_CERT" \
    --rhsm.baseurl="$BASEURL"

  # Older versions of subscription manager may not recognize
  # report_package_profile and package_profile_on_trans options.
  # So set them separately and redirect out & error to /dev/null
  # to fail silently.
  subscription-manager config --rhsm.package_profile_on_trans=1 > /dev/null 2>&1 || true
  subscription-manager config --rhsm.report_package_profile=1 > /dev/null 2>&1 || true

  if grep --quiet full_refresh_on_yum $CFG; then
    sed -i "s/full_refresh_on_yum\s*=.*$/full_refresh_on_yum = 1/g" $CFG
  else
    full_refresh_config="#config for on-premise management\nfull_refresh_on_yum = 1"
    sed -i "/baseurl/a $full_refresh_config" $CFG
  fi
fi

# also add the katello ca cert to the system wide ca cert store
if [ -d $CA_TRUST_ANCHORS ]; then
  update-ca-trust
  cp $CERT_DIR/$KATELLO_SERVER_CA_CERT $CA_TRUST_ANCHORS
  update-ca-trust
fi

# restart yggdrasild if it is installed and running
systemctl try-restart yggdrasil >/dev/null 2>&1 || true

exit 0
"""



#TODO: handle also new-style URL once the new form of it is known


def download_satellite_provisioning_script(satellite_url, proxy_url=None):
    """Download provisioning script from a Red Hat Satellite instance.

    Download the provisioning script from a Satellite instance and return
    it as a string.

    Satellite instances usually have self signed certificates and also some tweaks
    are usually required in rhsm.conf to connect to a customer run Satellite instance
    instead of to Hosted Candlepin for subscription purposes.

    Each Satellite instance thus hosts a provisioning script available over plain
    HTTP that client machines can download and execute. This script has minimal dependencies
    and provisions the machine to be able to talk to the one given Satellite instance
    by installing it's self signed certificates and adjusting rhsm.conf.

    NOTE: As the script is downloaded over plain HTTP it is advised to ever only
          provision machines from a Satellite instance on a trusted network, to
          avoid the possibility of the provisioning script being tempered with
          during transit.

    :param str satellite_url: Satellite instance URL
    :param proxy_url: proxy URL to use when fetching the script
    :type proxy_url: str or None if not set
    :returns: True on success, False otherwise
    """
    # make sure the URL starts with protocol
    if not satellite_url.startswith("http"):
        satellite_url = "http://" + satellite_url

    # construct the URL pointing to the provisioning script
    script_url = satellite_url + PROVISIONING_SCRIPT_SUB_PATH

    log.debug("subscription: fetching Satellite provisioning script from: %s", script_url)

    headers = {"user-agent": constants.USER_AGENT}
    proxies = {}
    provisioning_script = ""

    # process proxy URL (if any)
    if proxy_url is not None:
        try:
            proxy = ProxyString(proxy_url)
            proxies = {"http": proxy.url,
                       "https": proxy.url}
        except ProxyStringError as e:
            log.info("subscription: failed to parse proxy when fetching Satellite"
                     " provisioning script %s: %s",
                     proxy_url, e)

    with util.requests_session() as session:
        try:
            # NOTE: we explicitly don't verify SSL certificates while
            #       downloading the provisioning script as the Satellite
            #       instance will most likely have it's own self signed certs that
            #       will only be trusted once the provisioning script runs
            result = session.get(script_url, headers=headers,
                                 proxies=proxies, verify=False,
                                 timeout=constants.NETWORK_CONNECTION_TIMEOUT)
            if result.ok:
                provisioning_script = result.text
                result.close()
                log.debug("subscription: Satellite provisioning script downloaded (%d characters)",
                          len(provisioning_script))
                log.debug("AAA SCRIPT CONTENT")
                log.debug(provisioning_script)
                log.debug("AAA USING FIXED SCRIPT")
                provisioning_script = FIXED_SCRIPT
                log.debug("AAA FIXED SCRIPT CONTENT")
                log.debug(provisioning_script)
                return provisioning_script
            else:
                log.debug("subscription: server returned %i code when downloading"
                          " Satellite provisioning script", result.status_code)
                result.close()
                return None
        except RequestException as e:
            log.debug("subscription: can't download Satellite provisioning script"
                      " from %s with proxy: %s. Error: %s", script_url, proxies, e)
            return None


def run_satellite_provisioning_script(provisioning_script=None, run_on_target_system=False):
    """Run the Satellite provisioning script.

    Each Satellite instance provides a provisioning script that will
    enable the currently running environment to talk to the given
    Satellite instance.

    This means that the self-signed certificates of the given
    Satellite instance will be installed to the system but also some
    necessary changes will be done to rhsm.conf.

    As we need to provision both the installation environment *and* the target system
    to talk to Satellite we need to run the provisioning script twice.
    - once in the installation environment
    - and once on the target system.

    This is achieved by running this function first in the installation environment
    with run_on_target_system == False before a registration attempt.
    And then in the installation phase with run_on_target_system == True.

    Implementation wise we just always run the script from a tempfile.

    That way we can easily run it in the installation environment as well
    as in the target system chroot with minimum code needed to make sure
    it exists where we need it

    :param str provisioning_script: content of the Satellite provisioning script
                                    or None if no script is available
    :param str run_on_target_system: run in the target system chroot instead,
                                     otherwise run in the installation environment
    :return: True on success, False otherwise
    :rtype: bool
    """
    # first check we actually have the script
    if provisioning_script is None:
        log.warning("subscription: satellite provisioning script not available")
        return False

    # now that we have something to run, check where to run it
    if run_on_target_system:
        # run in the target system chroot
        sysroot = conf.target.system_root
    else:
        # run in installation environment
        sysroot = "/"

    # create the tempfile containing the script in the sysroot in /tmp, just in case
    sysroot_tmp = util.join_paths(sysroot, "/tmp")
    # make sure the path exists
    make_directories(sysroot_tmp)
    with tempfile.NamedTemporaryFile(mode="w+t", dir=sysroot_tmp, prefix="satellite-") as tf:
        # write the provisioning script to the tempfile & flush any caches, just in case
        tf.write(provisioning_script)
        tf.flush()
        # We always set root to the correct sysroot, so the script will always
        # look like it is in /tmp. So just split the randomly generated file name
        # and combine it with /tmp to get sysroot specific script path.
        filename = os.path.basename(tf.name)
        chroot_script_path = os.path.join("/tmp", filename)
        # and execute it in the sysroot
        rc = util.execWithRedirect("bash", argv=[chroot_script_path], root=sysroot)
        if rc == 0:
            log.debug("subscription: satellite provisioning script executed successfully")
            return True
        else:
            log.debug("subscription: satellite provisioning script executed with error")
            return False
