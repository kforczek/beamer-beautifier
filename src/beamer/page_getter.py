from typing import Callable
from threading import Lock

from PyQt5 import QtCore


class PageGetter(QtCore.QObject):
    local_version_available = QtCore.pyqtSignal(object)
    background_version_available = QtCore.pyqtSignal(object)
    global_version_available = QtCore.pyqtSignal(object)

    def __init__(self, local_version_slot: Callable, background_version_slot: Callable, global_version_slot: Callable):
        """
        :param local_version_slot: The function that gets called when a new local version becomes available.
        :param background_version_slot: The function that gets called when a new background version becomes available.
        :param global_version_slot: The function that gets called when a new global version becomes available.
        """
        super().__init__()
        self.local_version_available.connect(local_version_slot)
        self.background_version_available.connect(background_version_slot)
        self.global_version_available.connect(global_version_slot)

        self._is_canceled = False
        self._checker_lock = Lock()

    def cancel(self):
        """
        Cancels the task. No more slot functions will be called.
        """
        with self._checker_lock:
            self._is_canceled = True

    def add_local_version(self, version):
        with self._checker_lock:
            if self._is_canceled:
                return

        self.local_version_available.emit(version)

    def add_background_version(self, version):
        with self._checker_lock:
            if self._is_canceled:
                return

        self.background_version_available.emit(version)

    def add_global_version(self, version):
        with self._checker_lock:
            if self._is_canceled:
                return

        self.global_version_available.emit(version)
