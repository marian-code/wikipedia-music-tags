from PyQt5 import QtGui, QtCore, QtWidgets

class Window(QtWidgets.QWidget):
    def __init__(self, rows, columns):
        QtWidgets.QWidget.__init__(self)
        self.table = QtWidgets.QTableWidget(self)
        self.table.setRowCount(rows)
        self.table.setColumnCount(columns)
        for column in range(columns):
            for row in range(rows):
                item = QtWidgets.QTableWidgetItem('Text%d' % row)
                self.table.setItem(row, column, item)
        self.edit = QtWidgets.QLineEdit(self)
        self.button = QtWidgets.QPushButton('Search', self)
        self.button.clicked.connect(self.handleButton)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.table)
        layout.addWidget(self.edit)
        layout.addWidget(self.button)

    def handleButton(self):
        items = self.table.findItems(
            self.edit.text(), QtCore.Qt.MatchContains)
        if items:
            results = '\n'.join(
                'row %d column %d' % (item.row() + 1, item.column() + 1)
                for item in items)
        else:
            results = 'Found Nothing'
        QtWidgets.QMessageBox.information(self, 'Search Results', results)

if __name__ == '__main__':

    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = Window(6, 3)
    window.resize(350, 300)
    window.show()
    sys.exit(app.exec_())