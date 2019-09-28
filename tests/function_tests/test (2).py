import random, sys
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QApplication,
                             QTableWidgetItem, QTableView)
from PyQt5.QtCore import Qt, QVariant, QSortFilterProxyModel
from PyQt5.QtGui import QStandardItemModel, QStandardItem

class NumberSortModel(QSortFilterProxyModel):

    def lessThan(self, left_index, right_index):

        left_var = left_index.data(Qt.EditRole)
        right_var = right_index.data(Qt.EditRole)

        try:
            return float(left_var) < float(right_var)
        except (ValueError, TypeError):
            pass
        return left_var < right_var


if __name__ == "__main__":

    app = QApplication(sys.argv)
    model = QStandardItemModel(5, 5)
    random.seed()
    for i in range(5):
        for j in range(5):
            item = QStandardItem()
            item.setData(QVariant(str(random.randint(-500, 500)/100.0)), Qt.DisplayRole)
            model.setItem(i, j, item)
    
    proxy = NumberSortModel()
    proxy.setSourceModel(model)
    
    view = QTableView()
    view.setModel(proxy)
    view.setSortingEnabled(True)
    view.show()
    sys.exit(app.exec_())