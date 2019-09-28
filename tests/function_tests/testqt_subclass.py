import random, sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QApplication,
                             QTableWidgetItem, QTableView)
from PyQt5.QtCore import Qt, QVariant, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem
import os


class NumberSortModel(QSortFilterProxyModel):

    def lessThan(self, left_index, right_index):

        left_var = left_index.data(Qt.EditRole)
        right_var = right_index.data(Qt.EditRole)

        try:
            return float(left_var) < float(right_var)
        except (ValueError, TypeError):
            pass
        return left_var < right_var

        try:
            return left_var < right_var
        except TypeError:  # in case of NoneType
            return True

class NewStandardItem(QStandardItem):

    def data(self, role):
        if role != 0:
            return super(NewStandardItem, self).data(role)
        else:
            filtered = super(NewStandardItem, self).data(role)
            filtered = str(os.path.split(filtered)[1])
            return filtered

    """
    def setData(self, value, role):
        if role != 0:
            super(NewStandardItem, self).setData(value, role)
        else:
            value_old = self.realData(role)
            if value_old is not None:
                value = str(os.path.join(os.path.split(value_old)[0], value))

            super(NewStandardItem, self).setData(value, role)
    """

    def realData(self, role):
        return super(NewStandardItem, self).data(role)

    def text(self):
        text_text = super(NewStandardItem, self).text()
        text_data = self.realData(Qt.DisplayRole)

        if len(text_data) > len(text_text):
            return text_data
        else:
            return text_text

if __name__ == "__main__":

    #print(QStandardItem.__dict__)

    import inspect
    from pprint import pprint
    #pprint(inspect.getmembers(QStandardItem, lambda a:not(inspect.isroutine(a))))

    app = QApplication(sys.argv)
    model = QStandardItemModel(5, 5)
    random.seed()
    for i in range(5):
        for j in range(5):
            item = QStandardItem()
            item.setData(QVariant("C:\drivers\daco.mp3"), Qt.DisplayRole)
            item_new = NewStandardItem()
            item_new.setData(QVariant("C:\drivers/daco.mp3"), Qt.DisplayRole)
            print(item.data(Qt.DisplayRole), item_new.data(Qt.DisplayRole),
                  item_new.realData(Qt.DisplayRole))

            model.setItem(i, j, item_new)
    
    proxy = NumberSortModel()
    proxy.setSourceModel(model)
    
    view = QTableView()
    view.setModel(proxy)
    view.setSortingEnabled(True)
    view.show()

    def detail():
        print(type(model.item(0, 0)))
        print(model.item(0, 0).data(Qt.EditRole), model.item(0, 0).text())

    view.clicked.connect(detail)

    sys.exit(app.exec_())