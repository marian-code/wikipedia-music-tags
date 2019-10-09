from wiki_music.utilities.loggers import log_gui

from distutils.version import LooseVersion
import os
import platform
import sys
import warnings

# Version of QtPy
from ._version import __version__


class PythonQtError(RuntimeError):
    """Error raise if no bindings could be selected."""
    pass


class PythonQtWarning(Warning):
    """Warning if some features are not implemented in a binding."""
    pass

# Qt API environment variable name
QT_API = 'QT_API'

# Names of the expected PyQt5 api
PYQT5_API = ['pyqt5']

# Names of the expected PyQt4 api
PYQT4_API = [
    'pyqt',  # name used in IPython.qt
    'pyqt4'  # pyqode.qt original name
]

# Names of the expected PySide api
PYSIDE_API = ['pyside']

# Names of the expected PySide2 api
PYSIDE2_API = ['pyside2']

# Detecting if a binding was specified by the user
binding_specified = QT_API in os.environ

# Setting a default value for QT_API
os.environ.setdefault(QT_API, 'pyqt5')

API = os.environ[QT_API].lower()
initial_api = API
assert API in (PYQT5_API + PYQT4_API + PYSIDE_API + PYSIDE2_API)

is_old_pyqt = is_pyqt46 = False
PYQT5 = True
PYQT4 = PYSIDE = PYSIDE2 = False

print("API:", API)
print('FORCE_QT_API:', os.environ.get('FORCE_QT_API'))

# When `FORCE_QT_API` is set, we disregard
# any previously imported python bindings.
if os.environ.get('FORCE_QT_API') is not None:
    if 'PyQt5' in sys.modules:
        API = initial_api if initial_api in PYQT5_API else 'pyqt5'
    elif 'PySide2' in sys.modules:
        API = initial_api if initial_api in PYSIDE2_API else 'pyside2'
    elif 'PyQt4' in sys.modules:
        API = initial_api if initial_api in PYQT4_API else 'pyqt4'
    elif 'PySide' in sys.modules:
        API = initial_api if initial_api in PYSIDE_API else 'pyside'

if API in PYQT5_API:
    print("ahoj pyqt5 1")
    try:
        from PyQt5.QtCore import PYQT_VERSION_STR as PYQT_VERSION  # analysis:ignore
        print("ahoj pyqt5 2")
        from PyQt5.QtCore import QT_VERSION_STR as QT_VERSION  # analysis:ignore
        print("ahoj pyqt5 3")
        PYSIDE_VERSION = None

        if sys.platform == 'darwin':
            macos_version = LooseVersion(platform.mac_ver()[0])
            if macos_version < LooseVersion('10.10'):
                if LooseVersion(QT_VERSION) >= LooseVersion('5.9'):
                    raise PythonQtError("Qt 5.9 or higher only works in "
                                        "macOS 10.10 or higher. Your "
                                        "program will fail in this "
                                        "system.")
            elif macos_version < LooseVersion('10.11'):
                if LooseVersion(QT_VERSION) >= LooseVersion('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version
    except ImportError as e:
        API = os.environ['QT_API'] = 'pyside2'

if API in PYSIDE2_API:
    print("ahoj pyside2 1")
    try:
        from PySide2 import __version__ as PYSIDE_VERSION  # analysis:ignore
        print("ahoj pyside2 2")
        from PySide2.QtCore import __version__ as QT_VERSION  # analysis:ignore
        print("ahoj pyside2 3")

        PYQT_VERSION = None
        PYQT5 = False
        PYSIDE2 = True

        if sys.platform == 'darwin':
            macos_version = LooseVersion(platform.mac_ver()[0])
            if macos_version < LooseVersion('10.11'):
                if LooseVersion(QT_VERSION) >= LooseVersion('5.11'):
                    raise PythonQtError("Qt 5.11 or higher only works in "
                                        "macOS 10.11 or higher. Your "
                                        "program will fail in this "
                                        "system.")

            del macos_version
    except ImportError:
        API = os.environ['QT_API'] = 'pyqt'

if API in PYQT4_API:
    print("ahoj pyqt4 1")
    try:
        import sip
        print("ahoj pyqt4 2")

        try:
            sip.setapi('QString', 2)
            sip.setapi('QVariant', 2)
            sip.setapi('QDate', 2)
            sip.setapi('QDateTime', 2)
            sip.setapi('QTextStream', 2)
            sip.setapi('QTime', 2)
            sip.setapi('QUrl', 2)
        except (AttributeError, ValueError):
            # PyQt < v4.6
            pass
        from PyQt4.Qt import PYQT_VERSION_STR as PYQT_VERSION  # analysis:ignore
        print("ahoj pyqt4 3")
        from PyQt4.Qt import QT_VERSION_STR as QT_VERSION  # analysis:ignore
        print("ahoj pyqt4 4")
        PYSIDE_VERSION = None
        PYQT5 = False
        PYQT4 = True
    except ImportError:
        API = os.environ['QT_API'] = 'pyside'
    else:
        is_old_pyqt = PYQT_VERSION.startswith(('4.4', '4.5', '4.6', '4.7'))
        is_pyqt46 = PYQT_VERSION.startswith('4.6')

if API in PYSIDE_API:
    print("ahoj pyside 1")
    try:
        from PySide import __version__ as PYSIDE_VERSION  # analysis:ignore
        print("ahoj pyside 2")
        from PySide.QtCore import __version__ as QT_VERSION  # analysis:ignore
        print("ahoj pyside 3")
        PYQT_VERSION = None
        PYQT5 = PYSIDE2 = False
        PYSIDE = True
    except ImportError:
        raise PythonQtError('No Qt bindings could be found')

# If a correct API name is passed to QT_API and it could not be found,
# switches to another and informs through the warning
if API != initial_api and binding_specified:
    warnings.warn('Selected binding "{}" could not be found, '
                  'using "{}"'.format(initial_api, API), RuntimeWarning)

API_NAME = {'pyqt5': 'PyQt5', 'pyqt': 'PyQt4', 'pyqt4': 'PyQt4',
            'pyside': 'PySide', 'pyside2':'PySide2'}[API]

if PYQT4:
    import sip
    try:
        API_NAME += (" (API v{0})".format(sip.getapi('QString')))
    except AttributeError:
        pass

# original code
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
                             QModelIndex)
except ImportError as e:
    log_gui.critical("None of the Qt backends is available! Aborting")
    raise ImportError("None of the Qt backends is available! Aborting")
else:
    log_gui.debug("Qt imports done")
