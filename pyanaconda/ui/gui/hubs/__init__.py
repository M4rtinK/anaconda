# Base classes for Hubs.
#
# Copyright (C) 2011-2012  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions of
# the GNU General Public License v.2, or (at your option) any later version.
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY expressed or implied, including the implied warranties of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.  You should have received a copy of the
# GNU General Public License along with this program; if not, write to the
# Free Software Foundation, Inc., 31 Milk Street #960789 Boston, MA
# 02196 USA.  Any Red Hat trademarks that are incorporated in the
# source code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission of
# Red Hat, Inc.
#

from pyanaconda import lifecycle
from pyanaconda.anaconda_loggers import get_module_logger
from pyanaconda.core.i18n import C_, _
from pyanaconda.core.timer import Timer
from pyanaconda.flags import flags
from pyanaconda.ui import common
from pyanaconda.ui.gui import GUIObject
from pyanaconda.ui.gui.helpers import autoinstall_stopped
from pyanaconda.ui.gui.utils import escape_markup, gtk_call_once
from pyanaconda.ui.helpers import get_distribution_text

log = get_module_logger(__name__)


class Hub(GUIObject, common.Hub):
    """A Hub is an overview UI screen.  A Hub consists of one or more grids of
       configuration options that the user may choose from.  Each grid is
       provided by a SpokeCategory, and each option is provided by a Spoke.
       When the user dives down into a Spoke and is finished interacting with
       it, they are returned to the Hub.

       Some Spokes are required.  The user must interact with all required
       Spokes before they are allowed to proceed to the next stage of
       installation.

       From a layout perspective, a Hub is the entirety of the screen, though
       the screen itself can be roughly divided into thirds.  The top third is
       some basic navigation information (where you are, what you're
       installing).  The middle third is the grid of Spokes.  The bottom third
       is an action area providing additional buttons (quit, continue) or
       progress information (during package installation).

       Installation may consist of multiple chained Hubs, or Hubs with
       additional standalone screens either before or after them.

       .. inheritance-diagram:: Hub
          :parts: 3
    """

    _hubs_collection = []

    # Should we automatically go to next hub if processing is done and there are no
    # spokes on the hub ? The default value is False and Initial Setup will likely
    # override it to True in it's hub.
    continue_if_empty = False

    def __init__(self, data, storage, payload):
        """Create a new Hub instance.

           The arguments this base class accepts defines the API that Hubs
           have to work with.  A Hub does not get free reign over everything
           in the anaconda class, as that would be a big mess.  Instead, a
           Hub may count on the following:

           ksdata       -- An instance of a pykickstart Handler object.  The
                           Hub uses this to populate its UI with defaults
                           and to pass results back after it has run.
           storage      -- An instance of storage.Storage.  This is useful for
                           determining what storage devices are present and how
                           they are configured.
           payload      -- An instance of a payload.Payload subclass.  This
                           is useful for displaying and selecting packages to
                           install, and in carrying out the actual installation.
        """
        GUIObject.__init__(self, data)
        common.Hub.__init__(self, storage, payload)

        # enable the auto continue feature if we are in kickstart
        # mode, but if the user interacts with the hub, it will be
        # disabled again
        self._auto_continue = flags.automatedInstall
        self._click_continue = False

        self._hubs_collection.append(self)
        self.timeout = None

        self._incompleteSpokes = []
        self._inSpoke = False
        self._notReadySpokes = []
        self._spokes = {}

        # Used to store the last result of _updateContinue
        self._warningMsg = None

        self._checker = None
        # Flag to indicate the user can continue even if the checker indicates an error.
        # The checker itself is left alone so the error message doesn't accidentally get
        # cleaered.
        self._checker_ignore = False

        self._gridColumns = 3

    def _createBox(self):
        """Create and fill the list of categories and spokes."""
        import gi

        gi.require_version("Gtk", "3.0")
        gi.require_version("AnacondaWidgets", "3.4")

        from gi.repository import AnacondaWidgets, Gtk

        cats_and_spokes = self._collectCategoriesAndSpokes()
        categories = cats_and_spokes.keys()

        grid = Gtk.Grid(row_spacing=18, column_spacing=18, column_homogeneous=True,
                        margin_bottom=12, margin_left=12, margin_right=12,
                        halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER,
                        row_homogeneous=True)

        col = 0

        row_in_column = [-1] * self._gridColumns

        for category in common.sort_categories(categories):
            selectors = []
            for spokeClass in sorted(cats_and_spokes[category], key=lambda s: s.title):
                # Check if this spoke is to be shown in the supported environments
                if not any(spokeClass.should_run(environ, self.data) for environ in flags.environs):
                    continue

                # Create the new spoke and populate its UI with whatever data.
                # From here on, this Spoke will always exist.
                spoke = spokeClass(self.data, self.storage, self.payload)
                spoke.window.set_beta(self.window.get_beta())
                spoke.window.set_property("distribution", get_distribution_text())

                # If a spoke is not showable, it is unreachable in the UI.  We
                # might as well get rid of it.
                #
                # NOTE:  Any kind of spoke can be unshowable.
                if not spoke.showable:
                    del(spoke)
                    continue

                # This allows being able to jump between two spokes without
                # having to directly involve the hub.
                self._spokes[spokeClass.__name__] = spoke

                # If a spoke is indirect, it is reachable but not directly from
                # a hub.  This is for things like the custom partitioning spoke,
                # which you can only get to after going through the initial
                # storage configuration spoke.
                #
                # NOTE:  This only makes sense for NormalSpokes.  Other kinds
                # of spokes do not involve a hub.
                if spoke.indirect:
                    spoke.initialize()
                    continue

                spoke.selector = AnacondaWidgets.SpokeSelector(C_("GUI|Spoke", spoke.title),
                                                               spoke.icon)

                # Set all selectors to insensitive before initialize runs.  The call to
                # _updateCompleteness later will take care of setting it straight.
                spoke.selector.set_sensitive(False)
                spoke.initialize()

                if not spoke.ready:
                    self._notReadySpokes.append(spoke)

                # Set some default values on the associated selector that
                # affect its display on the hub.
                self._updateCompleteness(spoke, update_continue=False)
                spoke.selector.connect("button-press-event", self._on_spoke_clicked, spoke)
                spoke.selector.connect("key-release-event", self._on_spoke_clicked, spoke)
                selectors.append(spoke.selector)

            if not selectors:
                continue

            # category handling

            # excape unwanted markup
            cat_title = escape_markup(category.get_title())
            # generate pango markup
            cat_label = '<span size="larger" weight="bold">{}</span>'.format(cat_title)
            # setup the category label
            label = Gtk.Label(label=cat_label,
                              use_markup=True, halign=Gtk.Align.START, valign=Gtk.Align.END,
                              margin_bottom=6, wrap=True, xalign=0.0)

            grid.attach(label, col, row_in_column[col], 1, 1)
            row_in_column[col] += 1

            for selector in selectors:
                grid.attach(selector, col, row_in_column[col], 1, 1)
                row_in_column[col] += 1

            col = (col + 1) % self._gridColumns

        # initialization of all expected spokes has been started, so notify the controller
        hub_controller = lifecycle.get_controller_by_name(self.__class__.__name__)
        if hub_controller:
            hub_controller.all_modules_added()
        else:
            log.error("Initialization controller for hub %s expected but missing.", self.__class__.__name__)

        spokeArea = self.window.get_spoke_area()
        viewport = Gtk.Viewport()
        viewport.add(grid)
        spokeArea.add(viewport)

        self._updateContinue()

    def _updateCompleteness(self, spoke, update_continue=True):
        log.debug("AAA _updateCompleteness")
        log.debug("AAA _updateCompleteness - set sensitive")
        spoke.selector.set_sensitive(spoke.sensitive and spoke.ready)
        log.debug("AAA _updateCompleteness - set status")
        log.debug("AAA _updateCompleteness - set status spoke: %s, continue: %s" % (spoke, update_continue))
        spoke.selector.set_property("status", spoke.status)
        log.debug("AAA _updateCompleteness - set status - done")
        log.debug("AAA _updateCompleteness - set tooltip")
        spoke.selector.set_tooltip_markup(escape_markup(spoke.status))
        log.debug("AAA _updateCompleteness - set incomplete")
        spoke.selector.set_incomplete(not spoke.completed and spoke.mandatory)
        log.debug("AAA _updateCompleteness - handle completeness")
        self._handleCompleteness(spoke, update_continue)
        log.debug("AAA _updateCompleteness - done")

    def _handleCompleteness(self, spoke, update_continue=True):
        # Add the spoke to the incomplete list if it's now incomplete, and make
        # sure it's not on the list if it's now complete.  Then show the box if
        # it's needed and hide it if it's not.
        log.debug("AAA handle completeness - spoke %s, %s" % (spoke, update_continue))
        log.debug("AAA handle completeness - check if mandatory or completed")
        log.debug("AAA handle completeness - get mandatory")
        mandatory = spoke.mandatory
        log.debug(mandatory)
        log.debug("AAA handle completeness - get mandatory - done")
        log.debug("AAA handle completeness - get completed")
        completed = spoke.completed
        log.debug(completed)
        log.debug("AAA handle completeness - get completed - done")
        if mandatory or completed:
        #if not spoke.mandatory or spoke.completed:
            log.debug("AAA handle completeness - not mandatory or completed")
            if spoke in self._incompleteSpokes:
                log.debug("AAA handle completeness - not mandatory or completed - removing from incomplete spokes")
                self._incompleteSpokes.remove(spoke)
                log.debug("AAA handle completeness - not mandatory or completed - removing from incomplete spokes - done")
                log.debug("incomplete spokes: %s", self._incompleteSpokes)
        else:
            log.debug("AAA handle completeness - mandatory or complete")
            if spoke not in self._incompleteSpokes:
                log.debug("AAA handle completeness - mandatory or complete - not in incomplete spokes")
                self._incompleteSpokes.append(spoke)
                log.debug("AAA handle completeness - mandatory or complete - not in incomplete spokes - added")
                log.debug("incomplete spokes: %s", self._incompleteSpokes)

        if update_continue:
            log.debug("AAA handle completeness - update continue")
            self._updateContinue()
            log.debug("AAA handle completeness - update continue - done")
        log.debug("AAA handle completeness - done for %s, %s" % (spoke, update_continue))

    def _get_warning(self):
        """Get the warning message for the hub."""
        log.debug("AAA _get_warning()")
        warning = None
        if len(self._incompleteSpokes) == 0:
            log.debug("AAA _get_warning() - no warning")
            log.debug("AAA _get_warning() - no warning - self._checker")
            log.debug(self._checker)
            log.debug("AAA _get_warning() - no warning - self._checker - done")
            log.debug("AAA _get_warning() - no warning - self._checker.check() 1")
            log.debug(self._checker.check())
            log.debug("AAA _get_warning() - no warning - self._checker.check() - done 1")

            log.debug("AAA _get_warning() - no warning - self._checker.check() 2")
            log.debug(self._checker.check())
            log.debug("AAA _get_warning() - no warning - self._checker.check() - done 2")

            log.debug("AAA _get_warning() - no warning - self._checker.check() 3")
            log.debug(self._checker.check())
            log.debug("AAA _get_warning() - no warning - self._checker.check() - done 3")

            if self._checker and not self._checker.check():
                log.debug("AAA _get_warning() - no warning - get error message")
                warning = self._checker.error_message
                log.error(self._checker.error_message)
                log.debug("AAA _get_warning() - no warning - get error message - done")

                # If this is a kickstart, consider the user to be warned and
                # let them continue anyway, manually
                if flags.automatedInstall:
                    self._auto_continue = False
                    self._checker_ignore = True
        else:
            log.debug("AAA _get_warning() - some warning")
            warning = _("Please complete items marked with this icon before continuing to the next step.")

        log.debug("AAA _get_warning() - warning: %s" % warning)
        return warning

    def _updateContinue(self):
        # Check that this warning isn't already set to avoid spamming the
        # info bar with incomplete spoke messages when the hub starts
        log.debug("AAA _updateContinue")
        log.debug("AAA _updateContinue - get warning")
        warning = self._get_warning()
        #log.debug("AAA _updateContinue - get warning - SKIP")
        warning = ""
        log.debug("AAA _updateContinue - get warning - done")

        if warning != self._warningMsg:
            log.debug("AAA _updateContinue - warning missmatch")
            self.clear_info()
            self._warningMsg = warning

            if warning:
                log.debug("AAA _updateContinue - warning set new")
                self.set_warning(warning)

        log.debug("AAA _updateContinue - update continue button")
        self._updateContinueButton()
        log.debug("AAA _updateContinue - update continue button - done")

    @property
    def continuePossible(self):
        return len(self._incompleteSpokes) == 0 and len(self._notReadySpokes) == 0 and (getattr(self._checker, "success", True) or self._checker_ignore)

    def _updateContinueButton(self):
        self.window.set_may_continue(self.continuePossible)

    def _update_spokes(self):
        import queue

        from pyanaconda.ui.communication import hubQ

        q = hubQ.q

        if not self._spokes and self.window.get_may_continue() and self.continue_if_empty:
            # no spokes, move on
            log.debug("no spokes available on %s, continuing automatically", self)
            gtk_call_once(self.window.emit, "continue-clicked")

        # Grab all messages that may have appeared since last time this method ran.
        while True:
            try:
                (code, args) = q.get(False)
            except queue.Empty:
                break


            log.debug("AAA *** QUEUE MESSAGE:")
            log.debug(code)
            log.debug(args)
            # The first argument to all codes is the name of the spoke we are
            # acting on.  If no such spoke exists, throw the message away.
            spoke = self._spokes.get(args[0], None)
            if not spoke or spoke.__class__.__name__ not in self._spokes:
                q.task_done()
                continue

            if code == hubQ.HUB_CODE_NOT_READY:
                log.debug("AAA *** QUEUE - NOT READY")
                self._updateCompleteness(spoke)

                if spoke not in self._notReadySpokes:
                    self._notReadySpokes.append(spoke)

                self._updateContinueButton()
                log.debug("spoke is not ready: %s", spoke)
            elif code == hubQ.HUB_CODE_READY:
                log.debug("AAA *** QUEUE - READY")
                self._updateCompleteness(spoke)

                if spoke in self._notReadySpokes:
                    self._notReadySpokes.remove(spoke)

                self._updateContinueButton()
                log.debug("spoke is ready: %s", spoke)

                # If this is a real kickstart install (the kind with an input ks file)
                # and all spokes are now completed, we should skip ahead to the next
                # hub automatically.  Take into account the possibility the user is
                # viewing a spoke right now, though.
                if flags.automatedInstall:
                    spoke_title = spoke.title.replace("_", "")
                    # Users might find it helpful to know why a kickstart install
                    # went interactive.  Log that here.
                    if not spoke.completed and spoke.mandatory:
                        autoinstall_stopped("User interaction required on spoke %s" % spoke_title)
                    else:
                        log.debug("kickstart installation, spoke %s is ready", spoke_title)

                    if self.continuePossible:
                        if self._inSpoke:
                            self._auto_continue = False
                        elif self._auto_continue:
                            self._click_continue = True

            elif code == hubQ.HUB_CODE_MESSAGE:
                log.debug("AAA *** QUEUE - STATUS")
                spoke.selector.set_property("status", args[1])
                log.debug("setting %s status to: %s", spoke, args[1])

            log.debug("AAA *** QUEUE - TASK DONE")
            q.task_done()

        # queue is now empty, should continue be clicked?
        if self._auto_continue and self._click_continue and self.window.get_may_continue():
            # don't update spokes anymore
            self.timeout.cancel()

            # enqueue the emit to the Gtk message queue
            log.debug("automatically clicking continue button")
            gtk_call_once(self.window.emit, "continue-clicked")

        return True

    def refresh(self):
        GUIObject.refresh(self)
        self._createBox()

        for hub in Hub._hubs_collection:
            if hub.timeout is not None:
                log.debug("Disabling event loop for hub %s", hub.__class__.__name__)
                hub.timeout.cancel()
                hub.timeout = None

        log.debug("Starting event loop for hub %s", self.__class__.__name__)
        self.timeout = Timer()
        self.timeout.timeout_msec(100, self._update_spokes)

    ### SIGNAL HANDLERS

    def _on_spoke_clicked(self, selector, event, spoke):
        import gi

        gi.require_version("Gdk", "3.0")

        from gi.repository import Gdk

        # This handler only runs for these two kinds of events, and only for
        # activate-type keys (space, enter) in the latter event's case.
        if event and event.type not in [Gdk.EventType.BUTTON_PRESS, Gdk.EventType.KEY_RELEASE]:
            return

        if event and event.type == Gdk.EventType.KEY_RELEASE and \
           event.keyval not in [Gdk.KEY_space, Gdk.KEY_Return, Gdk.KEY_ISO_Enter, Gdk.KEY_KP_Enter, Gdk.KEY_KP_Space]:
            return

        if selector:
            selector.grab_focus()

        # The automated kickstart installation already continues. Nothing to do.
        if self._click_continue:
            return

        # On automated kickstart installs, our desired behavior is to display
        # the hub while background processes work, then skip to the progress
        # hub immediately after everything's done.
        # However if the user proves his intent to change the kickstarted
        # values by entering any of the spokes, we need to disable the
        # auto continue feature and wait for the user to explicitly state
        # that he is done configuring by pressing the continue button.
        self._auto_continue = False

        # Enter the spoke
        self._inSpoke = True
        spoke.refresh()
        self.main_window.enterSpoke(spoke)
        # the new spoke should be now visible, trigger the entered signal
        spoke.entered.emit(spoke)

    def spoke_done(self, spoke):
        log.debug("AAAAAAAAAA SPOKE DONE SPOKE DONE SPOKE DONE")
        log.debug("AAAAAAAAAA SPOKE DONE SPOKE DONE SPOKE DONE")
        log.debug("AAAAAAAAAA SPOKE DONE SPOKE DONE SPOKE DONE")
        log.debug("AAAAAAAAAA SPOKE DONE SPOKE DONE SPOKE DONE")
        log.debug("AAAAAAAAAA SPOKE DONE SPOKE DONE SPOKE DONE")
        # Ignore if not in a spoke
        if not self._inSpoke:
            log.debug("AAAAAAAAAA SPOKE DONE - not in spoke")
            return

        if spoke.changed and (not spoke.skipTo or (spoke.skipTo and spoke.applyOnSkip)):
            log.debug("AAAAAAAAAA SPOKE DONE - changed")
            spoke.apply()
            log.debug("AAAAAAAAAA SPOKE DONE - changed - apply")
            spoke.execute()
            log.debug("AAAAAAAAAA SPOKE DONE - changed - execute")

        spoke.exited.emit(spoke)
        log.debug("AAAAAAAAAA SPOKE DONE - exited emit")

        self._inSpoke = False

        # Now update the selector with the current status and completeness.
        log.debug("AAAAAAAAAA SPOKE DONE - updating completeness")
        for sp in self._spokes.values():
            log.debug("AAAAAAAAAA SPOKE DONE - updating completeness - processing spoke %s" % sp)
            if not sp.indirect:
                log.debug("AAAAAAAAAA SPOKE DONE - updating completeness - updating spoke %s" % sp)
                self._updateCompleteness(sp, update_continue=False)
                log.debug("AAAAAAAAAA SPOKE DONE - updating completeness - updating spoke %s - DONE" % sp)
        log.debug("AAAAAAAAAA SPOKE DONE - updating completeness - done")


        log.debug("AAAAAAAAAA SPOKE DONE - update continue")
        self._updateContinue()
        log.debug("AAAAAAAAAA SPOKE DONE - update continue - done")

        # And then if that spoke wants us to jump straight to another one,
        # handle that now.
        if spoke.skipTo and spoke.skipTo in self._spokes:
            log.debug("AAAAAAAAAA SPOKE DONE - skip to spoke")
            dest = spoke.skipTo

            # Clear out the skipTo setting so we don't cycle endlessly.
            spoke.skipTo = None

            self._on_spoke_clicked(self._spokes[dest].selector, None, self._spokes[dest])
        # Otherwise, switch back to the hub (that's us!)
        else:
            log.debug("AAAAAAAAAA SPOKE DONE - return to hub")
            self.main_window.returnToHub()
