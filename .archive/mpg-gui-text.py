import sys
import obd
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class OBDGui(QWidget):
   def __init__(self, parent = None):
      super(OBDGui, self).__init__(parent)

      # Set window geometry
      self.title = 'OBD GUI'
      self.left = 10
      self.top = 10
      self.width = 450
      self.height = 200
      self.setWindowTitle(self.title)
      self.setGeometry(self.left, self.top, self.width, self.height)
      layout = QVBoxLayout()

      # MPG Slider
      self.s = QProgressBar()
      self.s.setRange(0,50)
      self.s.setValue(0)
      self.s.setTextVisible(False)
      self.s.setAlignment(Qt.AlignRight)
      layout.addWidget(self.s)

      # MPG Value Text
      self.l = QLabel("0.0 MPGs")
      self.l.setFont(QFont('Fira Sans Semi-Light', 16))
      self.l.setAlignment(Qt.AlignCenter)
      layout.addWidget(self.l)

      # Update timer
      print("Connecting to OBD Reciever")
      self.connection = obd.Async()
      print("Connection successful. Starting command watch loop...")
      self.connection.watch(obd.commands.SPEED)
      self.connection.watch(obd.commands.RPM)
      self.connection.watch(obd.commands.INTAKE_PRESSURE)
      self.connection.watch(obd.commands.INTAKE_TEMP)
      self.connection.start()
      self.timer = QTimer()
      self.timer.timeout.connect(self.getmpg)
      self.timer.start(500)

      # Open the CSV Log File
      self.mf = open("mpg.csv", "w+")
      self.mf.write("MPG,RPM,SPEED,IMAP,TMP,MAP\n")

      # Arrange all widets
      self.setLayout(layout)


   def getmpg(self):
      SPEED = self.connection.query(obd.commands.SPEED).value.magnitude
      # MAF Calculation
      RPM = self.connection.query(obd.commands.RPM).value.magnitude
      MAP = self.connection.query(obd.commands.INTAKE_PRESSURE).value.magnitude
      TMP = self.connection.query(obd.commands.INTAKE_TEMP).value.magnitude+273.15
      R = 8.314  # Specific gas constant
      MM = 28.97 # Molecular mass of air
      DISP = 3.964 # Engine displacement in L
      VE = 0.75 # Volumetric efficency, play around with this value
      IMAP = (RPM*MAP)/TMP
      MAF = (IMAP/120)*VE*DISP*(MM/R)
      MPG = (710.7*SPEED)/(MAF*100)
      self.mf.write("{},{},{},{},{},{}\n".format(MPG,RPM,SPEED,IMAP,TMP,MAP))
      self.l.setText(str(MPG)+" MPGs")
def main():
   app = QApplication(sys.argv)
   ex = OBDGui()
   ex.show()
   sys.exit(app.exec_())
   
	
if __name__ == '__main__':
   main()