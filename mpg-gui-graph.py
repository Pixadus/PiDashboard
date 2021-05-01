from ctypes import alignment
import sys
import obd
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg

class Dashboard(QWidget):
   def __init__(self, parent = None):
      super(Dashboard, self).__init__(parent)

      ##########################
      # -- Global Variables -- #
      ##########################

      # TODO setup csv logging
      csv_logging = "none" # Possible values: none (no logging), average (total average for trip), detailed (detailed for trip)
      csv_file = "obd_log.csv"

      # Refresh rate (in seconds) for OBD queries and graph updates
      refresh_rate = 0.5 

      # Graph x-axis range (in seconds)
      mpg_x_range = 60 
      speed_x_range = 60
      rpm_x_range = 60
      tmp_x_range = 60
      voltage_x_range = 60
      load_x_range = 60

      # Average value sample set size
      self.avg_val_sample_size = 2500
      
      #########################
      # -- Window Geometry -- #
      #########################

      self.title = 'OBDash'
      self.index = 0
      self.left = 10
      self.top = 10
      self.width = 800
      self.height = 480
      self.setWindowTitle(self.title)
      self.setGeometry(self.left, self.top, self.width, self.height)
      self.setStyleSheet("background-color: #232323")
      self.layout = QStackedLayout()
      self.setLayout(self.layout)

      # NOTE Layout order is: Home[0], Dashboard[1], Speed[2], RPM[3], MPG[4], Temp[5], Voltage[6], Load[7]

      ################################
      # -- Global Setup -- #
      ################################

      # OBD connection
      # print("Connecting to OBD Reciever")
      # while True:
      #    self.connection = obd.Async()
      #    if self.connection.is_connected():
      #       print("Connection successful. Starting command watch loop...")
      #       self.connection.watch(obd.commands.SPEED)
      #       self.connection.watch(obd.commands.RPM)
      #       self.connection.watch(obd.commands.INTAKE_PRESSURE)
      #       self.connection.watch(obd.commands.INTAKE_TEMP)
      #       self.connection.watch(obd.commands.COOLANT_TEMP)
      #       self.connection.watch(obd.commands.ENGINE_LOAD)
      #       self.connection.watch(obd.commands.ELM_VOLTAGE)
      #       self.connection.start()
      #       break
      #    else:
      #       print("Unable to connect to OBD reciever. Retrying in 3 seconds...")
      #       time.sleep(3)
            
            
      # Update loop
      self.timer = QTimer()
      #self.timer.timeout.connect(self.UpdateValues)
      self.timer.start(int(refresh_rate*1000))

      ###################
      # -- Dashboard -- #
      ###################

      dash_layout = QGridLayout()
      dash_widget = QWidget()
      dash_widget.setLayout(dash_layout)
      dash_layout.setRowMinimumHeight(1,110)
      self.layout.addWidget(dash_widget)

      # --- Video Widget --- #

      # Video Status Label
      self.dash_v_label = QLabel("Video Status")
      self.dash_v_label.setFont(QFont('Fira Sans', 18))
      self.dash_v_label.setAlignment(Qt.AlignCenter)
      self.dash_v_label.setStyleSheet("color: #FFFFFF")
      dash_layout.addWidget(self.dash_v_label,1,1)

      # Video Placeholder
      self.dash_placeholder = QLabel()
      placeholder = QPixmap('media/blank.png')
      self.dash_placeholder.setPixmap(placeholder)
      self.dash_placeholder.setAlignment(Qt.AlignCenter)
      dash_layout.addWidget(self.dash_placeholder,2,1)

      # --- Row 1 --- #
      # # Speed Label
      # self.dash_speed = QLabel("Speed (mph)")
      # self.dash_speed.setFont(QFont('Fira Sans Light', 18))
      # self.dash_speed.setAlignment(Qt.AlignCenter)
      # self.dash_speed.setStyleSheet("color: #A5A5A5")
      # self.dash_speed.mousePressEvent = self.switchToSpeed
      # dash_layout.addWidget(self.dash_speed,1,1)

      # # Speed Value
      # self.dash_speed_val = QLabel("0.0")
      # self.dash_speed_val.setFont(QFont('Open Sans Bold', 28))
      # self.dash_speed_val.setAlignment(Qt.AlignCenter)
      # self.dash_speed_val.setStyleSheet("color: #009D65")
      # self.dash_speed_val.mousePressEvent = self.switchToSpeed
      # dash_layout.addWidget(self.dash_speed_val,2,1)

      # # RPM Label
      # self.dash_rpm = QLabel("RPM")
      # self.dash_rpm.setFont(QFont('Fira Sans Light', 18))
      # self.dash_rpm.setAlignment(Qt.AlignCenter)
      # self.dash_rpm.setStyleSheet("color: #A5A5A5")
      # self.dash_rpm.mousePressEvent = self.switchToRPM
      # dash_layout.addWidget(self.dash_rpm,1,2)

      # # RPM Value
      # self.dash_rpm_val = QLabel("0.0")
      # self.dash_rpm_val.setFont(QFont('Open Sans Bold', 28))
      # self.dash_rpm_val.setAlignment(Qt.AlignCenter)
      # self.dash_rpm_val.setStyleSheet("color: #009D65")
      # self.dash_rpm_val.mousePressEvent = self.switchToRPM
      # dash_layout.addWidget(self.dash_rpm_val,2,2)

      # # MPG Label
      # self.dash_mpg = QLabel("MPG")
      # self.dash_mpg.setFont(QFont('Fira Sans Light', 18))
      # self.dash_mpg.setAlignment(Qt.AlignCenter)
      # self.dash_mpg.setStyleSheet("color: #A5A5A5")
      # self.dash_mpg.mousePressEvent = self.switchToMPG
      # dash_layout.addWidget(self.dash_mpg,1,3)

      # # MPG Value
      # self.dash_mpg_val = QLabel("0.0")
      # self.dash_mpg_val.setFont(QFont('Open Sans Bold', 28))
      # self.dash_mpg_val.setAlignment(Qt.AlignCenter)
      # self.dash_mpg_val.setStyleSheet("color: #009D65")
      # self.dash_mpg_val.mousePressEvent = self.switchToMPG
      # dash_layout.addWidget(self.dash_mpg_val,2,3)

      # # Middle stretch
      # dash_layout.setRowStretch(3,1)

      # # --- Row 2 --- #

      # dash_layout.setRowMinimumHeight(5,110)
      # # Temperature Label
      # self.dash_tmp = QLabel("Temperature (C)")
      # self.dash_tmp.setFont(QFont('Fira Sans Light', 18))
      # self.dash_tmp.setAlignment(Qt.AlignCenter)
      # self.dash_tmp.setStyleSheet("color: #A5A5A5")
      # self.dash_tmp.mousePressEvent = self.switchToTmp
      # dash_layout.addWidget(self.dash_tmp,4,1)

      # # Temperature Value
      # self.dash_tmp_val = QLabel("0.0")
      # self.dash_tmp_val.setFont(QFont('Open Sans Bold', 28))
      # self.dash_tmp_val.setAlignment(Qt.AlignCenter)
      # self.dash_tmp_val.setStyleSheet("color: #009D65")
      # self.dash_tmp_val.mousePressEvent = self.switchToTmp
      # dash_layout.addWidget(self.dash_tmp_val,5,1)

      # # Voltage Label
      # self.dash_voltage = QLabel("Voltage (V)")
      # self.dash_voltage.setFont(QFont('Fira Sans Light', 18))
      # self.dash_voltage.setAlignment(Qt.AlignCenter)
      # self.dash_voltage.setStyleSheet("color: #A5A5A5")
      # self.dash_voltage.mousePressEvent = self.switchToVoltage
      # dash_layout.addWidget(self.dash_voltage,4,2)

      # # Voltage Value
      # self.dash_voltage_val = QLabel("0.0")
      # self.dash_voltage_val.setFont(QFont('Open Sans Bold', 28))
      # self.dash_voltage_val.setAlignment(Qt.AlignCenter)
      # self.dash_voltage_val.setStyleSheet("color: #009D65")
      # self.dash_voltage_val.mousePressEvent = self.switchToVoltage
      # dash_layout.addWidget(self.dash_voltage_val,5,2)

      # # Load Label
      # self.dash_load = QLabel("Load (%)")
      # self.dash_load.setFont(QFont('Fira Sans Light', 18))
      # self.dash_load.setAlignment(Qt.AlignCenter)
      # self.dash_load.setStyleSheet("color: #A5A5A5")
      # self.dash_load.mousePressEvent = self.switchToLoad
      # dash_layout.addWidget(self.dash_load,4,3)

      # # Load Value
      # self.dash_load_val = QLabel("0.0")
      # self.dash_load_val.setFont(QFont('Open Sans Bold', 28))
      # self.dash_load_val.setAlignment(Qt.AlignCenter)
      # self.dash_load_val.setStyleSheet("color: #009D65")
      # self.dash_load_val.mousePressEvent = self.switchToLoad
      # dash_layout.addWidget(self.dash_load_val,5,3)

      ####################### 
      # -- Speed Details -- #
      #######################

      # speed_layout = QGridLayout()
      # speed_widget = QWidget()
      # speed_widget.setLayout(speed_layout)
      # self.layout.addWidget(speed_widget)
      # speed_widget.mouseDoubleClickEvent = self.switchToDash

      # # Labels for Instant and Average
      # self.speed_li = QLabel("Current Speed (mph)")
      # self.speed_li.setFont(QFont('Fira Sans Light', 24))
      # self.speed_li.setAlignment(Qt.AlignCenter)
      # self.speed_li.setStyleSheet("color: #A5A5A5")
      # speed_layout.addWidget(self.speed_li,1,1)
      
      # self.speed_la = QLabel("Average Speed (mph)")
      # self.speed_la.setFont(QFont('Fira Sans Light', 24))
      # self.speed_la.setAlignment(Qt.AlignCenter)
      # self.speed_la.setStyleSheet("color: #A5A5A5")
      # speed_layout.addWidget(self.speed_la,1,2)

      # # Instant and Average Values
      # self.speed_lmi = QLabel("0.0")
      # self.speed_lmi.setFont(QFont('Open Sans Bold', 36))
      # self.speed_lmi.setAlignment(Qt.AlignCenter)
      # self.speed_lmi.setStyleSheet("color: #009D65")
      # speed_layout.addWidget(self.speed_lmi,2,1)
      
      # self.speed_lma = QLabel("0.0")
      # self.speed_lma.setFont(QFont('Open Sans Bold', 36))
      # self.speed_lma.setAlignment(Qt.AlignCenter)
      # self.speed_lma.setStyleSheet("color: #009D65")
      # speed_layout.addWidget(self.speed_lma,2,2)
      # self.speed_avg_list = [0]

      # # Speed Graph
      # self.speed_graph = pg.PlotWidget(self, background="#232323")
      # self.speed_x_time = [0]
      # self.speed_y_speed = [0.0]
      # self.speed_run_time = speed_x_range/refresh_rate
      # self.speed_gp = self.speed_graph.plot(self.speed_x_time,self.speed_y_speed)
      # speed_layout.addWidget(self.speed_graph,4,1,1,2)

      # ####################### 
      # # -- RPM Details -- #
      # #######################

      # rpm_layout = QGridLayout()
      # rpm_widget = QWidget()
      # rpm_widget.setLayout(rpm_layout)
      # self.layout.addWidget(rpm_widget)
      # rpm_widget.mouseDoubleClickEvent = self.switchToDash

      # # Labels for Instant and Average
      # self.rpm_li = QLabel("Current RPM")
      # self.rpm_li.setFont(QFont('Fira Sans Light', 24))
      # self.rpm_li.setAlignment(Qt.AlignCenter)
      # self.rpm_li.setStyleSheet("color: #A5A5A5")
      # rpm_layout.addWidget(self.rpm_li,1,1)
      
      # self.rpm_la = QLabel("Average RPM")
      # self.rpm_la.setFont(QFont('Fira Sans Light', 24))
      # self.rpm_la.setAlignment(Qt.AlignCenter)
      # self.rpm_la.setStyleSheet("color: #A5A5A5")
      # rpm_layout.addWidget(self.rpm_la,1,2)

      # # Instant and Average Values
      # self.rpm_lmi = QLabel("0.0")
      # self.rpm_lmi.setFont(QFont('Open Sans Bold', 36))
      # self.rpm_lmi.setAlignment(Qt.AlignCenter)
      # self.rpm_lmi.setStyleSheet("color: #009D65")
      # rpm_layout.addWidget(self.rpm_lmi,2,1)
      
      # self.rpm_lma = QLabel("0.0")
      # self.rpm_lma.setFont(QFont('Open Sans Bold', 36))
      # self.rpm_lma.setAlignment(Qt.AlignCenter)
      # self.rpm_lma.setStyleSheet("color: #009D65")
      # rpm_layout.addWidget(self.rpm_lma,2,2)
      # self.rpm_avg_list = [0]

      # # Graph
      # self.rpm_graph = pg.PlotWidget(self, background="#232323")
      # self.rpm_x_time = [0]
      # self.rpm_y_rpm = [0.0]
      # self.rpm_run_time = rpm_x_range/refresh_rate
      # self.rpm_gp = self.rpm_graph.plot(self.rpm_x_time,self.rpm_y_rpm)
      # rpm_layout.addWidget(self.rpm_graph,4,1,1,2)

      # #####################
      # # -- MPG Details -- #
      # #####################

      # mpg_layout = QGridLayout()
      # mpg_widget = QWidget()
      # mpg_widget.setLayout(mpg_layout)
      # self.layout.addWidget(mpg_widget)
      # mpg_widget.mouseDoubleClickEvent = self.switchToDash

      # # Labels for Instant and Average
      # self.mpg_li = QLabel("Instant MPG")
      # self.mpg_li.setFont(QFont('Fira Sans Light', 24))
      # self.mpg_li.setAlignment(Qt.AlignCenter)
      # self.mpg_li.setStyleSheet("color: #A5A5A5")
      # mpg_layout.addWidget(self.mpg_li,1,1)
      
      # self.mpg_la = QLabel("Average MPG")
      # self.mpg_la.setFont(QFont('Fira Sans Light', 24))
      # self.mpg_la.setAlignment(Qt.AlignCenter)
      # self.mpg_la.setStyleSheet("color: #A5A5A5")
      # mpg_layout.addWidget(self.mpg_la,1,2)

      # # MPG Instant and Average Value Texts
      # self.mpg_lmi = QLabel("0.0")
      # self.mpg_lmi.setFont(QFont('Open Sans Bold', 36))
      # self.mpg_lmi.setAlignment(Qt.AlignCenter)
      # self.mpg_lmi.setStyleSheet("color: #009D65")
      # mpg_layout.addWidget(self.mpg_lmi,2,1)
      
      # self.mpg_lma = QLabel("0.0")
      # self.mpg_lma.setFont(QFont('Open Sans Bold', 36))
      # self.mpg_lma.setAlignment(Qt.AlignCenter)
      # self.mpg_lma.setStyleSheet("color: #009D65")
      # mpg_layout.addWidget(self.mpg_lma,2,2)
      # self.mpg_avg_list = [0]

      # # MPG Graph
      # self.mpg_graph = pg.PlotWidget(self, background="#232323")
      # self.mpg_x_time = [0]
      # self.mpg_y_mpg = [0.0]
      # self.mpg_run_time = mpg_x_range/refresh_rate
      # self.mpg_gp = self.mpg_graph.plot(self.mpg_x_time,self.mpg_y_mpg)
      # mpg_layout.addWidget(self.mpg_graph,4,1,1,2)

      # #############################
      # # -- Temperature Details -- #
      # #############################

      # tmp_layout = QGridLayout()
      # tmp_widget = QWidget()
      # tmp_widget.setLayout(tmp_layout)
      # self.layout.addWidget(tmp_widget)
      # tmp_widget.mouseDoubleClickEvent = self.switchToDash

      # # Labels for Instant and Average
      # self.tmp_li = QLabel("Current Temperature (C)")
      # self.tmp_li.setFont(QFont('Fira Sans Light', 24))
      # self.tmp_li.setAlignment(Qt.AlignCenter)
      # self.tmp_li.setStyleSheet("color: #A5A5A5")
      # tmp_layout.addWidget(self.tmp_li,1,1)
      
      # self.tmp_la = QLabel("Average Temperature (C)")
      # self.tmp_la.setFont(QFont('Fira Sans Light', 24))
      # self.tmp_la.setAlignment(Qt.AlignCenter)
      # self.tmp_la.setStyleSheet("color: #A5A5A5")
      # tmp_layout.addWidget(self.tmp_la,1,2)

      # # Instant and Average Values
      # self.tmp_lmi = QLabel("0.0")
      # self.tmp_lmi.setFont(QFont('Open Sans Bold', 36))
      # self.tmp_lmi.setAlignment(Qt.AlignCenter)
      # self.tmp_lmi.setStyleSheet("color: #009D65")
      # tmp_layout.addWidget(self.tmp_lmi,2,1)
      
      # self.tmp_lma = QLabel("0.0")
      # self.tmp_lma.setFont(QFont('Open Sans Bold', 36))
      # self.tmp_lma.setAlignment(Qt.AlignCenter)
      # self.tmp_lma.setStyleSheet("color: #009D65")
      # tmp_layout.addWidget(self.tmp_lma,2,2)
      # self.tmp_avg_list = [0]

      # # Graph
      # self.tmp_graph = pg.PlotWidget(self, background="#232323")
      # self.tmp_x_time = [0]
      # self.tmp_y_tmp = [0.0]
      # self.tmp_run_time = tmp_x_range/refresh_rate
      # self.tmp_gp = self.tmp_graph.plot(self.tmp_x_time,self.tmp_y_tmp)
      # tmp_layout.addWidget(self.tmp_graph,4,1,1,2)
      
      # #########################
      # # -- Voltage Details -- #
      # #########################

      # voltage_layout = QGridLayout()
      # voltage_widget = QWidget()
      # voltage_widget.setLayout(voltage_layout)
      # self.layout.addWidget(voltage_widget)
      # voltage_widget.mouseDoubleClickEvent = self.switchToDash

      # # Labels for Instant and Average
      # self.voltage_li = QLabel("Current Voltage (V)")
      # self.voltage_li.setFont(QFont('Fira Sans Light', 24))
      # self.voltage_li.setAlignment(Qt.AlignCenter)
      # self.voltage_li.setStyleSheet("color: #A5A5A5")
      # voltage_layout.addWidget(self.voltage_li,1,1)
      
      # self.voltage_la = QLabel("Average Voltage (V)")
      # self.voltage_la.setFont(QFont('Fira Sans Light', 24))
      # self.voltage_la.setAlignment(Qt.AlignCenter)
      # self.voltage_la.setStyleSheet("color: #A5A5A5")
      # voltage_layout.addWidget(self.voltage_la,1,2)

      # # Instant and Average Values
      # self.voltage_lmi = QLabel("0.0")
      # self.voltage_lmi.setFont(QFont('Open Sans Bold', 36))
      # self.voltage_lmi.setAlignment(Qt.AlignCenter)
      # self.voltage_lmi.setStyleSheet("color: #009D65")
      # voltage_layout.addWidget(self.voltage_lmi,2,1)
      
      # self.voltage_lma = QLabel("0.0")
      # self.voltage_lma.setFont(QFont('Open Sans Bold', 36))
      # self.voltage_lma.setAlignment(Qt.AlignCenter)
      # self.voltage_lma.setStyleSheet("color: #009D65")
      # voltage_layout.addWidget(self.voltage_lma,2,2)
      # self.voltage_avg_list = [0]

      # # Graph
      # self.voltage_graph = pg.PlotWidget(self, background="#232323")
      # self.voltage_x_time = [0]
      # self.voltage_y_voltage = [0.0]
      # self.voltage_run_time = voltage_x_range/refresh_rate
      # self.voltage_gp = self.voltage_graph.plot(self.voltage_x_time,self.voltage_y_voltage)
      # voltage_layout.addWidget(self.voltage_graph,4,1,1,2)

      # ######################
      # # -- Load Details -- #
      # ######################

      # load_layout = QGridLayout()
      # load_widget = QWidget()
      # load_widget.setLayout(load_layout)
      # self.layout.addWidget(load_widget)
      # load_widget.mouseDoubleClickEvent = self.switchToDash

      # # Labels for Instant and Average
      # self.load_li = QLabel("Current Load (%)")
      # self.load_li.setFont(QFont('Fira Sans Light', 24))
      # self.load_li.setAlignment(Qt.AlignCenter)
      # self.load_li.setStyleSheet("color: #A5A5A5")
      # load_layout.addWidget(self.load_li,1,1)
      
      # self.load_la = QLabel("Average Load (%)")
      # self.load_la.setFont(QFont('Fira Sans Light', 24))
      # self.load_la.setAlignment(Qt.AlignCenter)
      # self.load_la.setStyleSheet("color: #A5A5A5")
      # load_layout.addWidget(self.load_la,1,2)

      # # Instant and Average Values
      # self.load_lmi = QLabel("0.0")
      # self.load_lmi.setFont(QFont('Open Sans Bold', 36))
      # self.load_lmi.setAlignment(Qt.AlignCenter)
      # self.load_lmi.setStyleSheet("color: #009D65")
      # load_layout.addWidget(self.load_lmi,2,1)
      
      # self.load_lma = QLabel("0.0")
      # self.load_lma.setFont(QFont('Open Sans Bold', 36))
      # self.load_lma.setAlignment(Qt.AlignCenter)
      # self.load_lma.setStyleSheet("color: #009D65")
      # load_layout.addWidget(self.load_lma,2,2)
      # self.load_avg_list = [0]

      # # Graph
      # self.load_graph = pg.PlotWidget(self, background="#232323")
      # self.load_x_time = [0]
      # self.load_y_load = [0.0]
      # self.load_run_time = load_x_range/refresh_rate
      # self.load_gp = self.load_graph.plot(self.load_x_time,self.load_y_load)
      # load_layout.addWidget(self.load_graph,4,1,1,2)

   ##########################
   # -- Helper Functions -- #
   ##########################

   # ------ EVENTS ------- #
   def exitWindow(self,exit):
      self.close()

   def switchToHome(self,event):
      # Event to transition back to home menu.
      self.layout.setCurrentIndex(0)

   def switchToDash(self, event):
      # Event to transition back to the dashboard
      # TODO if in details menu, go back to dashboard. If in dashboard, return home
      self.layout.setCurrentIndex(1)

   def switchToSpeed(self, event):
      self.layout.setCurrentIndex(2)

   def switchToRPM(self, event):
      self.layout.setCurrentIndex(3)

   def switchToMPG(self, event):
      self.layout.setCurrentIndex(4)

   def switchToTmp(self, event):
      self.layout.setCurrentIndex(5)
   
   def switchToVoltage(self, event):
      self.layout.setCurrentIndex(6)

   def switchToLoad(self, event):
      self.layout.setCurrentIndex(7)

   # ------ Update Functions ------ #

   def UpdateValues(self):
      # TODO break this up into sub-functions in another file.
      # == Update Current Values == #
      SPEED = self.connection.query(obd.commands.SPEED).value.magnitude
      RPM = self.connection.query(obd.commands.RPM).value.magnitude
      MAP = self.connection.query(obd.commands.INTAKE_PRESSURE).value.magnitude
      TMP = self.connection.query(obd.commands.INTAKE_TEMP).value.magnitude+273.15
      CLT_TMP = self.connection.query(obd.commands.COOLANT_TEMP).value.magnitude
      VOLTAGE = self.connection.query(obd.commands.ELM_VOLTAGE).value.magnitude
      LOAD = self.connection.query(obd.commands.ENGINE_LOAD).value.magnitude

      # == Speed Graph == #
      # Calculate average value. Make sure data is less than the average value sample size.
      MPH_SPEED = SPEED*0.62137
      if len(self.speed_avg_list) < self.avg_val_sample_size:
         self.speed_avg_list.append(MPH_SPEED)
      else:
         self.speed_avg_list.pop(0)
         self.speed_avg_list.append(MPH_SPEED)
      avg = 0
      for x in range(len(self.speed_avg_list)):
         avg += self.speed_avg_list[x]
      speed_mavg = avg/len(self.speed_avg_list)

      # Update the graph
      if len(self.speed_x_time) <= self.speed_run_time:
         self.speed_x_time.append(len(self.speed_x_time))
         self.speed_y_speed.append(MPH_SPEED)
      else:
         self.speed_y_speed.pop(0)
         self.speed_y_speed.append(MPH_SPEED)

      # == RPM Graph == #
      # Calculate average value. Make sure data is less than the average value sample size.
      if len(self.rpm_avg_list) < self.avg_val_sample_size:
         self.rpm_avg_list.append(RPM)
      else:
         self.rpm_avg_list.pop(0)
         self.rpm_avg_list.append(RPM)
      avg = 0
      for x in range(len(self.rpm_avg_list)):
         avg += self.rpm_avg_list[x]
      rpm_mavg = avg/len(self.rpm_avg_list)

      # Update the graph
      if len(self.rpm_x_time) <= self.rpm_run_time:
         self.rpm_x_time.append(len(self.rpm_x_time))
         self.rpm_y_rpm.append(RPM)
      else:
         self.rpm_y_rpm.pop(0)
         self.rpm_y_rpm.append(RPM)

      # == MPG Calculations & Graph == #
      R = 8.314  # Specific gas constant
      MM = 28.97 # Molecular mass of air
      DISP = 3.964 # Engine displacement in L
      VE = 0.75 # Volumetric efficency, play around with this value
      IMAP = (RPM*MAP)/TMP
      MAF = (IMAP/120)*VE*DISP*(MM/R)
      MPG = (710.7*SPEED)/(MAF*100)

      # Update average value. Make sure data is less than the average value sample size - update over time. 
      if len(self.mpg_avg_list) < self.avg_val_sample_size:
         self.mpg_avg_list.append(MPG)
      else:
         self.mpg_avg_list.pop(0)
         self.mpg_avg_list.append(MPG)
      avg = 0
      for x in range(len(self.mpg_avg_list)):
         avg += self.mpg_avg_list[x]
      mpg_mavg = avg/len(self.mpg_avg_list)

      # Calculate graph changes
      if len(self.mpg_x_time) <= self.mpg_run_time:
         self.mpg_x_time.append(len(self.mpg_x_time))
         self.mpg_y_mpg.append(MPG)
      else:
         self.mpg_y_mpg.pop(0)
         self.mpg_y_mpg.append(MPG)

      # == Temperature Graph == #
      # Calculate average value. Make sure data is less than the average value sample size.
      if len(self.tmp_avg_list) < self.avg_val_sample_size:
         self.tmp_avg_list.append(CLT_TMP)
      else:
         self.tmp_avg_list.pop(0)
         self.tmp_avg_list.append(CLT_TMP)
      avg = 0
      for x in range(len(self.tmp_avg_list)):
         avg += self.tmp_avg_list[x]
      tmp_mavg = avg/len(self.tmp_avg_list)

      # Update the graph
      if len(self.tmp_x_time) <= self.tmp_run_time:
         self.tmp_x_time.append(len(self.tmp_x_time))
         self.tmp_y_tmp.append(CLT_TMP)
      else:
         self.tmp_y_tmp.pop(0)
         self.tmp_y_tmp.append(CLT_TMP)

      # == Voltage Graph == #
      # Calculate average value. Make sure data is less than the average value sample size.
      if len(self.voltage_avg_list) < self.avg_val_sample_size:
         self.voltage_avg_list.append(VOLTAGE)
      else:
         self.voltage_avg_list.pop(0)
         self.voltage_avg_list.append(VOLTAGE)
      avg = 0
      for x in range(len(self.voltage_avg_list)):
         avg += self.voltage_avg_list[x]
      voltage_mavg = avg/len(self.voltage_avg_list)

      # Update the graph
      if len(self.voltage_x_time) <= self.voltage_run_time:
         self.voltage_x_time.append(len(self.voltage_x_time))
         self.voltage_y_voltage.append(VOLTAGE)
      else:
         self.voltage_y_voltage.pop(0)
         self.voltage_y_voltage.append(VOLTAGE)

      # == Load Graph == #
      # Calculate average value. Make sure data is less than the average value sample size.
      if len(self.load_avg_list) < self.avg_val_sample_size:
         self.load_avg_list.append(LOAD)
      else:
         self.load_avg_list.pop(0)
         self.load_avg_list.append(LOAD)
      avg = 0
      for x in range(len(self.load_avg_list)):
         avg += self.load_avg_list[x]
      load_mavg = avg/len(self.load_avg_list)

      # Update the graph
      if len(self.load_x_time) <= self.load_run_time:
         self.load_x_time.append(len(self.load_x_time))
         self.load_y_load.append(LOAD)
      else:
         self.load_y_load.pop(0)
         self.load_y_load.append(LOAD)

      # == Set Dash Values == #
      self.dash_rpm_val.setText(str(round(RPM,2)))
      self.dash_speed_val.setText(str(round(MPH_SPEED,2)))
      self.dash_mpg_val.setText(str(round(MPG,2)))
      self.dash_tmp_val.setText(str(round(CLT_TMP,2)))
      self.dash_voltage_val.setText(str(round(VOLTAGE,2)))
      self.dash_load_val.setText(str(round(LOAD,2)))

      # == Set Detailed Values == #
      self.speed_lmi.setText(str(round(MPH_SPEED,2)))
      self.speed_lma.setText(str(round(speed_mavg,2)))
      self.rpm_lmi.setText(str(round(RPM,2)))
      self.rpm_lma.setText(str(round(rpm_mavg,2)))
      self.mpg_lmi.setText(str(round(MPG,2)))
      self.mpg_lma.setText(str(round(mpg_mavg,2)))
      self.tmp_lmi.setText(str(round(CLT_TMP,2)))
      self.tmp_lma.setText(str(round(tmp_mavg,2)))
      self.voltage_lmi.setText(str(round(VOLTAGE,2)))
      self.voltage_lma.setText(str(round(voltage_mavg,2)))
      self.load_lmi.setText(str(round(LOAD,2)))
      self.load_lma.setText(str(round(load_mavg,2)))

      # == Update Graphs == #
      self.speed_gp.setData(self.speed_x_time,self.speed_y_speed)
      self.rpm_gp.setData(self.rpm_x_time, self.rpm_y_rpm)
      self.mpg_gp.setData(self.mpg_x_time,self.mpg_y_mpg)
      self.tmp_gp.setData(self.tmp_x_time,self.tmp_y_tmp)
      self.voltage_gp.setData(self.tmp_x_time,self.voltage_y_voltage)
      self.load_gp.setData(self.load_x_time,self.load_y_load)

def main():
   app = QApplication(sys.argv)
   dash = Dashboard()
   dash.showFullScreen()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()
