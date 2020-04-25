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
import glob
import shutil

from dasbus.typing import get_variant, Str

from pyanaconda.core import util

from pyanaconda.modules.common.task import Task
from pyanaconda.modules.common.errors.installation import InsightsConnectError, \
    InsightsClientMissingError, SubscriptionTokenTransferError

from pyanaconda.modules.subscription import system_purpose

from pyanaconda.anaconda_loggers import get_module_logger
log = get_module_logger(__name__)


class ConnectToInsightsTask(Task):
    """Connect the target system to Red Hat Insights."""

    INSIGHTS_TOOL_PATH = "/usr/bin/insights-client"

    def __init__(self, sysroot, subscription_attached, connect_to_insights):
        """Create a new task.

        :param str sysroot: target system root path
        :param bool subscription_attached: if True then the system has been subscribed,
                                           False otherwise
        :param bool connect_to_insights: if True then connect the system to Insights,
                                         if False do nothing
        """
        super().__init__()
        self._sysroot = sysroot
        self._subscription_attached = subscription_attached
        self._connect_to_insights = connect_to_insights

    @property
    def name(self):
        return "Connect the target system to Red Hat Insights"

    def run(self):
        """Connect the target system to Red Hat Insights."""
        # check if we should connect to Red Hat Insights
        if not self._connect_to_insights:
            log.debug("insights-connect-task: Insights not requested, skipping")
            return
        elif not self._subscription_attached:
            log.debug("insights-connect-task: "
                      "Insights requested but target system is not subscribed, skipping")
            return

        insights_path = util.join_paths(self._sysroot, self.INSIGHTS_TOOL_PATH)
        # check the insights client utility is available
        if not os.path.isfile(insights_path):
            raise InsightsClientMissingError(
                "The insight-client tool ({}) is not available.".format(self.INSIGHTS_TOOL_PATH)
            )

        # tell the insights client to connect to insights
        log.debug("insights-connect-task: connecting to insights")
        rc = util.execWithRedirect(self.INSIGHTS_TOOL_PATH, ["--register"], root=self._sysroot)
        if rc:
            raise InsightsConnectError("Connecting to Red Hat Insights failed.")


class SystemPurposeConfigurationTask(Task):
    """Installation task for setting system purpose."""

    def __init__(self, sysroot, system_purpose_data):
        """Create a new system purpose configuration task.

        :param str sysroot: a path to the root of the installed system
        :param system_purpose_data: system purpose data DBus structure
        :type system_purpose_data: DBusData instance
        """
        super().__init__()
        self._sysroot = sysroot
        self._system_purpose_data = system_purpose_data

    @property
    def name(self):
        return "Set system purpose"

    def run(self):
        # apply System Purpose data
        return system_purpose.give_the_system_purpose(
            sysroot=self._sysroot,
            role=self._system_purpose_data.role,
            sla=self._system_purpose_data.sla,
            usage=self._system_purpose_data.usage,
            addons=self._system_purpose_data.addons
        )


class RestoreRHSMLogLevelTask(Task):
    """Restore RHSM log level back to INFO."""

    def __init__(self, rhsm_config_proxy):
        """Create a new task.
        :param rhsm_config_proxy: DBus proxy for the RHSM Config object
        """
        super().__init__()
        self._rhsm_config_proxy = rhsm_config_proxy

    @property
    def name(self):
        return "Restoring subscription manager log level"

    def run(self):
        """Set RHSM log level back to INFO.

        We previously set the RHSM log level to DEBUG, which is also
        reflected in rhsm.conf. This would mean RHSM would continue to
        log in debug mode also on the system once rhsm.conf has been
        copied over to the target system.

        So set the log level back to INFO before we copy the config file.
        """
        log.debug("subscription: setting RHSM log level back to INFO")
        self._rhsm_config_proxy.Set("logging.default_log_level",
                                    get_variant(Str, "INFO"), "")


class TransferSubscriptionTokensTask(Task):
    """Transfer subscription tokens to the target system."""

    RHSM_REPO_FILE_PATH = "/etc/yum.repos.d/redhat.repo"
    RHSM_CONFIG_FILE_PATH = "/etc/rhsm/rhsm.conf"
    RHSM_SYSPURPOSE_FILE_PATH = "/etc/rhsm/syspurpose/syspurpose.json"
    RHSM_ENTITLEMENT_KEYS_PATH = "/etc/pki/entitlement"
    RHSM_CONSUMER_KEY_PATH = "/etc/pki/consumer/key.pem"
    RHSM_CONSUMER_CERT_PATH = "/etc/pki/consumer/cert.pem"

    TARGET_REPO_FOLDER_PATH = "/etc/yum.repos.d"

    def __init__(self, sysroot, transfer_subscription_tokens):
        """Create a new task.

        :param str sysroot: target system root path
        :param bool transfer_subscription_tokens: if True attempt to transfer subscription
                                                  tokens to target system (we always transfer
                                                  system purpose data unconditionally)
        """
        super().__init__()
        self._sysroot = sysroot
        self._transfer_subscription_tokens = transfer_subscription_tokens

    @property
    def name(self):
        return "Transfer subscription tokens to target system"

    def _copy_pem_files(self, input_folder, output_folder, not_empty=True):
        """Copy all pem files from input_folder to output_folder.
        Files with the pem extension are generally encryption keys and certificates.
        If output_folder does not exist, it & any parts of its path will
        be created.
        :param str input_folder: input folder for the pem files
        :param str output_folder: output folder where to copy the pem files
        :return: False if the input directory does not exists or is empty,
                True after all pem files have be successfully copied
        :rtype: bool
        """
        # check the input folder exists
        if not os.path.isdir(input_folder):
            return False
        # optionally check the input folder is not empty
        if not_empty and not os.listdir(input_folder):
            return False
        # create the output folder path if it does not exist
        if not os.path.isdir(output_folder):
            util.mkdirChain(output_folder)
        # transfer all the pem files in the input folder
        for pem_file_path in glob.glob(os.path.join(input_folder, "*.pem")):
            shutil.copy(pem_file_path, output_folder)
        # if we got this far the pem copy operation was a success
        return True

    def _copy_file_to_path(self, file_path, target_file_path):
        if not os.path.isfile(file_path):
            return False
        if not os.path.isdir(os.path.dirname(target_file_path)):
            util.mkdirChain(os.path.dirname(target_file_path))
        shutil.copy(file_path, target_file_path)
        return True

    def _transfer_system_purpose(self):
        # transfer the system purpose file if present
        # - this might be needed even if the system has not been subscribed
        #   during the installation and is therefore always attempted
        # - this means the syspurpose tool has been called in the installation
        #   environment & we need to transfer the results to the target system
        if os.path.exists(self.RHSM_SYSPURPOSE_FILE_PATH):
            log.debug("subscription: transferring syspurpose file")
            target_syspurpose_file_path = self._sysroot + self.RHSM_SYSPURPOSE_FILE_PATH
            self._copy_file_to_path(self.RHSM_SYSPURPOSE_FILE_PATH, target_syspurpose_file_path)

    def _transfer_rhsm_config_file(self):
        """Transfer the RHSM config file."""

        log.debug("subscription: transferring RHSM config file")
        target_rhsm_config_path = self._sysroot + self.RHSM_CONFIG_FILE_PATH
        if not self._copy_file_to_path(self.RHSM_CONFIG_FILE_PATH, target_rhsm_config_path):
            msg = "RHSM config file ({}) is missing.".format(self.RHSM_CONFIG_FILE_PATH)
            raise SubscriptionTokenTransferError(msg)

    def _transfer_consumer_key(self):
        """Transfer the consumer key."""
        log.debug("subscription: transferring consumer key")
        target_consumer_key_path = self._sysroot + self.RHSM_CONSUMER_KEY_PATH
        if not self._copy_file_to_path(self.RHSM_CONSUMER_KEY_PATH, target_consumer_key_path):
            msg = "RHSM consumer key ({}) is missing.".format(self.RHSM_CONSUMER_KEY_PATH)
            raise SubscriptionTokenTransferError(msg)

    def _transfer_consumer_cert(self):
        """Transfer the consumer cert."""
        log.debug("subscription: transferring consumer certificate")
        target_consumer_key_path = self._sysroot + self.RHSM_CONSUMER_CERT_PATH
        if not self._copy_file_to_path(self.RHSM_CONSUMER_CERT_PATH, target_consumer_key_path):
            msg = "RHSM consumer certificate ({}) is missing.".format(self.RHSM_CONSUMER_CERT_PATH)
            raise SubscriptionTokenTransferError(msg)

    def _transfer_entitlement_keys(self):
        """Transfer the entitlement keys."""
        log.debug("subscription: transferring entitlement keys")
        target_entitlement_keys_path = self._sysroot + self.RHSM_ENTITLEMENT_KEYS_PATH
        if not self._copy_pem_files(self.RHSM_ENTITLEMENT_KEYS_PATH, target_entitlement_keys_path):
            msg = "RHSM entitlement keys (from {}) are missing.".format(
                self.RHSM_ENTITLEMENT_KEYS_PATH)
            raise SubscriptionTokenTransferError(msg)

    def _transfer_repo_file(self):
        """Transfer the repo file."""
        log.debug("subscription: transferring repo file")
        target_repo_file_path = self._sysroot + self.RHSM_REPO_FILE_PATH
        if not self._copy_file_to_path(self.RHSM_REPO_FILE_PATH, target_repo_file_path):
            msg = "RHSM generated repo file ({}) is missing".format(self.RHSM_REPO_FILE_PATH)
            raise SubscriptionTokenTransferError(msg)

    def run(self):
        """Transfer the subscription tokens to the target system.

        Otherwise the target system would have to be registered and subscribed again
        due to missing subscription tokens.
        """
        self._transfer_system_purpose()

        # the other subscription tokens are only relevant if the system has been subscribed
        if not self._transfer_subscription_tokens:
            log.debug("subscription: transfer of subscription tokens not requested")
            return

        self._transfer_rhsm_config_file()
        self._transfer_consumer_key()
        self._transfer_consumer_cert()
        self._transfer_entitlement_keys()
        self._transfer_repo_file()
