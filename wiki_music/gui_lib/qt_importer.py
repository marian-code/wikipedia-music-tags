"""Module for importing all Qt classes used by GUI.

Note
----
With the help of QtPy all major Qt bindings are supported: PyQt5, PyQt4,
Pyside2 and PySide.
"""

import logging
from typing import TYPE_CHECKING

log = logging.getLogger(__name__)

try:
    from qtpy.QtWidgets import (QMainWindow, QFileDialog, QApplication, QStyle,
                                QTableWidgetItem, QMessageBox, QProgressDialog,
                                QAbstractItemView, QInputDialog, QLabel,
                                QVBoxLayout, QTableWidget, QWidget, QDialog,
                                QStatusBar, QSystemTrayIcon, QSizePolicy,
                                QRubberBand, QStyleFactory, QSizeGrip,
                                QStyledItemDelegate, QProgressBar, QTableView,
                                QPushButton, QAction)
    from qtpy.QtGui import (QStandardItemModel, QStandardItem, QImage, QColor,
                            QPixmap, QIcon, QResizeEvent, QPalette)
    from qtpy.QtCore import (Qt, QSortFilterProxyModel, QTimer, QObject,
                             QBuffer, QSize, QRect, Property, Slot, Signal,
                             QByteArray, QIODevice, QPoint, QEvent, QVariant)
    from qtpy import uic

    if TYPE_CHECKING:
        from qtpy.QtGui import QDropEvent, QEnterEvent, QMoveEvent
        from qtpy.QtWidgets import QStyleOptionViewItem
        from qtpy.QtCore import QModelIndex
except ImportError as e:
    log.critical(f"None of the Qt backends is available: {e}")
    raise ImportError(f"None of the Qt backends is available: {e}")
else:
    log.debug("Qt imports done")
