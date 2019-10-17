"""Module for importing all Qt classes used by GUI.

Note
----
With the help of QtPy all major Qt bindings are supported: PyQt5, PyQt4,
Pyside2 and PySide.
"""

import logging

log = logging.getLogger(__name__)

# This exception is recurring quite often so here are imports to debug it
# normally these are hiddnen because they are caught in qtpy
"""
try:
    from PyQt5.QtCore import PYQT_VERSION_STR as PYQT_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PyQt5.QtCore import QT_VERSION_STR as QT_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PySide2 import __version__ as PYSIDE_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PySide2.QtCore import __version__ as QT_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PyQt4.Qt import PYQT_VERSION_STR as PYQT_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PyQt4.Qt import QT_VERSION_STR as QT_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PySide import __version__ as PYSIDE_VERSION
except ImportError as e:
    log.exception(e)
try:
    from PySide.QtCore import __version__ as QT_VERSION
except ImportError as e:
    log.exception(e)
"""

try:
    from qtpy.QtWidgets import (QMainWindow, QFileDialog, QApplication,
                                QTableWidgetItem, QMessageBox, QHBoxLayout,
                                QAbstractItemView, QInputDialog, QLabel,
                                QVBoxLayout, QTableWidget, QWidget, QDialog,
                                QStatusBar, QSystemTrayIcon, QSizePolicy,
                                QRubberBand, QStyleFactory, QSizeGrip,
                                QProgressBar, QProgressDialog)
    from qtpy.QtGui import (QStandardItemModel, QStandardItem, QImage,
                            QPixmap, QIcon, QPainter, QResizeEvent)
    from qtpy.QtCore import (Qt, QSortFilterProxyModel, QTimer, QObject,
                             QBuffer, QSize, QRect, Property, Slot, Signal,
                             QByteArray, QIODevice, QPoint, QEvent,
                             QModelIndex, QVariant)
    from qtpy import uic
except ImportError as e:
    log.critical(f"None of the Qt backends is available: {e}")
    raise ImportError(f"None of the Qt backends is available: {e}")
else:
    log.debug("Qt imports done")
