import types
import weakref
import sys
import time
from functools import partial

from PyQt5 import QtWidgets
from PyQt5 import QtGui 
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, QTimer

## The following code is borrowed from here: 
# http://stackoverflow.com/questions/24689800/async-like-pattern-in-pyqt-or-cleaner-background-call-pattern
# It provides a child->parent thread-communication mechanism.
class ref(object):
    """
    A weak method implementation
    """
    def __init__(self, method):
        try:
            if method.im_self is not None:
                # bound method
                self._obj = weakref.ref(method.im_self)
            else:
                # unbound method
                self._obj = None
            self._func = method.im_func
            self._class = method.im_class
        except AttributeError:
            # not a method
            self._obj = None
            self._func = method
            self._class = None

    def __call__(self):
        """
        Return a new bound-method like the original, or the
        original function if refers just to a function or unbound
        method.
        Returns None if the original object doesn't exist
        """
        if self.is_dead():
            return None
        if self._obj is not None:
            # we have an instance: return a bound method
            return types.MethodType(self._func, self._obj(), self._class)
        else:
            # we don't have an instance: return just the function
            return self._func

    def is_dead(self):
        """
        Returns True if the referenced callable was a bound method and
        the instance no longer exists. Otherwise, return False.
        """
        return self._obj is not None and self._obj() is None

    def __eq__(self, other):
        try:
            return type(self) is type(other) and self() == other()
        except:
            return False

    def __ne__(self, other):
        return not self == other


class proxy(ref):
    """
    Exactly like ref, but calling it will cause the referent method to
    be called with the same arguments. If the referent's object no longer lives,
    ReferenceError is raised.

    If quiet is True, then a ReferenceError is not raise and the callback 
    silently fails if it is no longer valid. 
    """

    def __init__(self, method, quiet=False):
        super(proxy, self).__init__(method)
        self._quiet = quiet

    def __call__(self, *args, **kwargs):
        func = ref.__call__(self)
        if func is None:
            if self._quiet:
                return
            else:
                raise ReferenceError('object is dead')
        else:
            return func(*args, **kwargs)

    def __eq__(self, other):
        try:
            func1 = ref.__call__(self)
            func2 = ref.__call__(other)
            return type(self) == type(other) and func1 == func2
        except:
            return False


class CallbackEvent(QtCore.QEvent):
    """
    A custom QEvent that contains a callback reference

    Also provides class methods for conveniently executing 
    arbitrary callback, to be dispatched to the event loop.
    """
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, func, *args, **kwargs):
        super(CallbackEvent, self).__init__(self.EVENT_TYPE)
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def callback(self):
        """
        Convenience method to run the callable. 

        Equivalent to:  
            self.func(*self.args, **self.kwargs)
        """
        self.func(*self.args, **self.kwargs)

    @classmethod
    def post_to(cls, receiver, func, *args, **kwargs):
        """
        Post a callable to be delivered to a specific
        receiver as a CallbackEvent. 

        It is the responsibility of this receiver to 
        handle the event and choose to call the callback.
        """
        # We can create a weak proxy reference to the
        # callback so that if the object associated with
        # a bound method is deleted, it won't call a dead method
        if not isinstance(func, proxy):
            reference = proxy(func, quiet=True)
        else:
            reference = func
        event = cls(reference, *args, **kwargs)

        # post the event to the given receiver
        QtWidgets.QApplication.postEvent(receiver, event)

## End borrowed code

## Begin Coroutine-framework code

class AsyncTask(QtCore.QObject):
    """ Object used to manage asynchronous tasks.

    This object should wrap any function that you want
    to call asynchronously. It will launch the function
    in a new thread, and register a listener so that
    `on_finished` is called when the thread is complete.

    """
    def __init__(self, func, *args, **kwargs):
        super(AsyncTask, self).__init__()
        self.result = None  # Used for the result of the thread.
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.finished = False
        self.finished_cb_ran = False
        self.finished_callback = None
        self.objThread = RunThreadCallback(self, self.func, self.on_finished, 
                                           *self.args, **self.kwargs)
        self.objThread.start()

    def customEvent(self, event):
        event.callback()

    def on_finished(self, result):
        """ Called when the threaded operation is complete.

        Saves the result of the thread, and
        executes finished_callback with the result if one
        exists. Also closes/cleans up the thread.

        """
        self.finished = True
        self.result = result
        if self.finished_callback:
            self.finished_ran = True
            func = partial(self.finished_callback, result)
            QTimer.singleShot(0, func)
        self.objThread.quit()
        self.objThread.wait()


class RunThreadCallback(QtCore.QThread):
    """ Runs a function in a thread, and alerts the parent when done. 

    Uses a custom QEvent to alert the main thread of completion.

    """
    def __init__(self, parent, func, on_finish, *args, **kwargs):
        super(RunThreadCallback, self).__init__(parent)
        self.on_finished = on_finish
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as e:
            print("e is %s" % e)
            result = e
        finally:
            CallbackEvent.post_to(self.parent(), self.on_finished, result)


def coroutine(func):
    """ Coroutine decorator, meant for use with AsyncTask.

    This decorator must be used on any function that uses
    the `yield AsyncTask(...)` pattern. It shouldn't be used
    in any other case.

    The decorator will yield AsyncTask objects from the
    decorated generator function, and register itself to
    be called when the task is complete. It will also
    excplicitly call itself if the task is already
    complete when it yields it.

    """
    def wrapper(*args, **kwargs):
        def execute(gen, input=None):
            if isinstance(gen, types.GeneratorType):
                if not input:
                    obj = next(gen)
                else:
                    try:
                        obj = gen.send(input)
                    except StopIteration as e:
                        result = getattr(e, "value", None)
                        return result
                if isinstance(obj, AsyncTask):
                    # Tell the thread to call `execute` when its done
                    # using the current generator object.
                    func = partial(execute, gen)
                    obj.finished_callback = func
                    if obj.finished and not obj.finished_cb_ran:
                        obj.on_finished(obj.result)
                else:
                    raise Exception("Using yield is only supported with AsyncTasks.")
            else:
                print("result is %s" % result)
                return result
        result = func(*args, **kwargs)
        execute(result)
    return wrapper

## End coroutine-framework code


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.cmd_button = QtWidgets.QPushButton("Push", self)
        self.cmd_button.clicked.connect(self.send_evt)
        self.statusBar()
        self.show()

    def worker(self, inval):
        print("in worker, received '%s'" % inval)
        time.sleep(2)
        return "%s worked" % inval

    @coroutine
    def send_evt(self, arg):
        out = AsyncTask(self.worker, "test string")
        out2 = AsyncTask(self.worker, "another test string")
        QThread.sleep(3)
        print("kicked off async task, waiting for it to be done")
        val = yield out
        val2 = yield out2
        print("out is %s" % val)
        print("out2 is %s" % val2)
        out = yield AsyncTask(self.worker, "Some other string")
        print("out is %s" % out)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    m = MainWindow()
    sys.exit(app.exec_())