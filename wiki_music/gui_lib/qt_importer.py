""" Module for importing all Qt classes used by GUI.

Note
----
With the help of QtPy all major Qt bindings are supported: PyQt5, PyQt4,
Pyside2 and PySide.
"""

# debug readthedocs build

try:
    from PyQt5.QtCore import PYQT_VERSION_STR
except ImportError as e:
    print(e)
try:
    from PyQt5.QtCore import QT_VERSION_STR
except ImportError as e:
    print(e)
try:
    from PySide2 import __version__
except ImportError as e:
    print(e)
try:
    from PySide2.QtCore import __version__
except ImportError as e:
    print(e)
# end of reradthedocs debug

import logging

log = logging.getLogger(__name__)

try:
    from qtpy.QtWidgets import (QMainWindow, QFileDialog, QApplication,
                                QTableWidgetItem, QMessageBox, QHBoxLayout,
                                QAbstractItemView, QInputDialog, QLabel,
                                QVBoxLayout, QTableWidget, QWidget, QDialog,
                                QStatusBar, QSystemTrayIcon, QSizePolicy,
                                QRubberBand, QStyleFactory, QSizeGrip)
    from qtpy.QtGui import (QStandardItemModel, QStandardItem, QImage,
                            QPixmap, QIcon, QPainter, QResizeEvent)
    from qtpy.QtCore import (Qt, QSortFilterProxyModel, QTimer, QObject,
                             QBuffer, QSize, QRect, Property, Slot, Signal,
                             QByteArray, QIODevice, QPoint, QEvent,
                             QModelIndex, QVariant)
    from qtpy import uic
except ImportError as e:
    log.critical("None of the Qt backends is available! Aborting")
    raise ImportError("None of the Qt backends is available! Aborting")
else:
    log.debug("Qt imports done")
