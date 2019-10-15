""" Module for importing all Qt classes used by GUI.

Note
----
With the help of QtPy all major Qt bindings are supported: PyQt5, PyQt4,
Pyside2 and PySide.
"""

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
