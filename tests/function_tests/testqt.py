import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

def window():
   app = QApplication(sys.argv)
   w = QWidget()
   b = QPushButton(w)
   b.setText("Show message!")

   b.move(50,50)
   b.clicked.connect(showdialog)
   w.setWindowTitle("PyQt Dialog demo")
   w.show()
   sys.exit(app.exec_())
	
def showdialog():
   #showdialog1()
   msg = QMessageBox()
   msg.setIcon(QMessageBox.Information)

   msg.setText("This is a message box")
   msg.setInformativeText("This is additional information")
   msg.setWindowTitle("MessageBox demo")
   msg.setDetailedText("The details are as follows:")
   msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
   msg.buttonClicked.connect(msgbtn)
	
   retval = msg.exec_()
   print("value of pressed message box button:", retval)

def showdialog1():
   """
   msg = QMessageBox()
   msg.setInformativeText("This is additional information")
   msg.setDetailedText("The details are as follows:")
   msg.buttonClicked.connect(msgbtn)
   """
	
   retval = QMessageBox(QMessageBox.Information, "MessageBox demo", "This is a message box", QMessageBox.Ok | QMessageBox.Cancel).exec_()
   print("value of pressed message box button:", retval)
	
def msgbtn(i):
   print("Button pressed is:",i.text())
	
if __name__ == '__main__': 
   window()