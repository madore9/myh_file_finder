import sys
import types


def _install_pyqt5_stubs():
    class _Signal:
        def __init__(self):
            self._callbacks = []

        def connect(self, callback):
            self._callbacks.append(callback)

        def emit(self, *args, **kwargs):
            for cb in list(self._callbacks):
                cb(*args, **kwargs)

    class _SignalDescriptor:
        def __set_name__(self, owner, name):
            self._name = name

        def __get__(self, instance, owner):
            if instance is None:
                return self
            signal = instance.__dict__.get(self._name)
            if signal is None:
                signal = _Signal()
                instance.__dict__[self._name] = signal
            return signal

    def pyqtSignal(*_args, **_kwargs):
        return _SignalDescriptor()

    class _QThread:
        def __init__(self, *_args, **_kwargs):
            pass

        def start(self):
            self.run()

        def run(self):
            pass

    class _Dummy:
        def __init__(self, *_args, **_kwargs):
            pass

    qtcore = types.ModuleType("PyQt5.QtCore")
    qtcore.QThread = _QThread
    qtcore.pyqtSignal = pyqtSignal
    qtcore.QTimer = _Dummy
    qtcore.QSize = _Dummy
    qtcore.Qt = _Dummy

    qtgui = types.ModuleType("PyQt5.QtGui")
    qtgui.QFont = _Dummy
    qtgui.QColor = _Dummy
    qtgui.QPalette = _Dummy

    class _QPixmap(_Dummy):
        def loadFromData(self, *_args, **_kwargs):
            return True

    class _QIcon(_Dummy):
        pass

    qtgui.QPixmap = _QPixmap
    qtgui.QIcon = _QIcon

    qtwidgets = types.ModuleType("PyQt5.QtWidgets")
    for name in [
        "QApplication",
        "QMainWindow",
        "QWidget",
        "QVBoxLayout",
        "QHBoxLayout",
        "QTableWidget",
        "QTableWidgetItem",
        "QPushButton",
        "QLabel",
        "QLineEdit",
        "QComboBox",
        "QCheckBox",
        "QProgressBar",
        "QFileDialog",
        "QMessageBox",
        "QHeaderView",
        "QAbstractItemView",
        "QGroupBox",
        "QSplitter",
        "QFrame",
        "QStyle",
        "QToolButton",
        "QMenu",
        "QAction",
        "QListWidget",
        "QDialog",
        "QPlainTextEdit",
        "QDialogButtonBox",
    ]:
        setattr(qtwidgets, name, _Dummy)

    pyqt5 = types.ModuleType("PyQt5")
    pyqt5.QtCore = qtcore
    pyqt5.QtGui = qtgui
    pyqt5.QtWidgets = qtwidgets

    sys.modules.setdefault("PyQt5", pyqt5)
    sys.modules.setdefault("PyQt5.QtCore", qtcore)
    sys.modules.setdefault("PyQt5.QtGui", qtgui)
    sys.modules.setdefault("PyQt5.QtWidgets", qtwidgets)


try:
    import PyQt5  # noqa: F401
except Exception:
    _install_pyqt5_stubs()
