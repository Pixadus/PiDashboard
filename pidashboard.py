from ctypes import alignment
import sys
import obd
import os
import time
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
#import pyqtgraph as pg

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

        # Color options
        ER_BTN_TXT = "rgb(0,0,0)"
        ER_BTN_BCK = "rgb(100,100,100)"
        ER_VAL_TXT = "#009D65"

        # OBD Connection
        self.connection = obd.Async()
        
        #########################
        # -- Window Geometry -- #
        #########################

        self.title = 'PiDashboard'
        self.index = 0
        self.left = 10
        self.top = 10
        self.width = 800
        self.height = 480
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setStyleSheet("""
        background-color: #383838;
        color: rgb(230,230,230);
        font: "Fira Sans Light";
        """)
        self.layout = QStackedLayout()
        self.setLayout(self.layout)

        # --- Timer --- #
        self.timer = QTimer()
        self.timer.timeout.connect(self.UpdateValues)
        self.timer.start(int(refresh_rate*1000))

        ###################
        # -- Dashboard -- #
        ###################

        dash_widget = QWidget()
        dash_layout = QGridLayout()
        dash_layout.rowStretch(2)
        dash_widget.setLayout(dash_layout)
        self.layout.addWidget(dash_widget)

        ##############################
        # -- Video Preview Widget -- #
        ##############################

        vp_widget = QWidget()
        vp_layout = QVBoxLayout()
        vp_widget.setLayout(vp_layout)
        vp_widget.setStyleSheet("background-color: #232323;")
        dash_layout.addWidget(vp_widget,1,1)

        # VP Label
        vp_top_label = QLabel("Video Status")
        vp_top_label.setFont(QFont('Fira Sans', 18))
        vp_top_label.setAlignment(Qt.AlignCenter)
        vp_top_label.setStyleSheet("color: #FFFFFF")
        vp_layout.addWidget(vp_top_label)

        # Placeholder image
        vp_placeholder = QLabel()
        vp_placeholder.setPixmap(QPixmap('media/blank.png'))
        vp_placeholder.setAlignment(Qt.AlignCenter)
        vp_layout.addWidget(vp_placeholder)

        # Button row widget
        vp_br_widget = QWidget()
        vp_br_layout = QHBoxLayout()
        vp_br_widget.setLayout(vp_br_layout)
        vp_br_play = QPushButton("Play")
        vp_br_stop = QPushButton("Stop")
        vp_br_exp = QPushButton("Expand")
        vp_br_layout.addWidget(vp_br_play)
        vp_br_layout.addWidget(vp_br_stop)
        vp_br_layout.addWidget(vp_br_exp)
        vp_layout.addWidget(vp_br_widget)

        # Storage indicator bar (can we do a text indicator, like 1.24/2.00?)
        vp_str_bar = QProgressBar()
        vp_str_bar.setRange(0,2000)
        vp_str_bar.setValue(0)
        vp_layout.addWidget(vp_str_bar)

        ######################
        # -- Engine Stats -- #
        ######################

        es_widget = QWidget()
        es_layout = QVBoxLayout()
        es_widget.setLayout(es_layout)
        es_widget.setStyleSheet("background-color: #232323;")
        dash_layout.addWidget(es_widget,1,2)

        # ES Label
        es_label = QLabel("Engine Status")
        es_label.setFont(QFont('Fira Sans', 18))
        es_label.setAlignment(Qt.AlignCenter)
        es_label.setStyleSheet("color: #FFFFFF; padding-left: 4em; padding-right: 4em;")
        es_layout.addWidget(es_label)

        # MPG Row
        mpgr_widget = QWidget()
        mpgr_layout = QHBoxLayout()
        mpgr_widget.setLayout(mpgr_layout)
        mpg_button = QPushButton("MPG")
        mpg_value = QLabel()
        mpgr_layout.addWidget(mpg_button)
        mpgr_layout.addWidget(mpg_value)
        es_layout.addWidget(mpgr_widget)

        # SPD Row
        spdr_widget = QWidget()
        spdr_layout = QHBoxLayout()
        spdr_widget.setLayout(spdr_layout)
        spd_button = QPushButton("SPD")
        spd_value = QLabel()
        spdr_layout.addWidget(spd_button)
        spdr_layout.addWidget(spd_value)
        es_layout.addWidget(spdr_widget)

        # RPM Row
        rpmr_widget = QWidget()
        rpmr_layout = QHBoxLayout()
        rpmr_widget.setLayout(rpmr_layout)
        rpm_button = QPushButton("RPM")
        rpm_value = QLabel()
        rpmr_layout.addWidget(rpm_button)
        rpmr_layout.addWidget(rpm_value)
        es_layout.addWidget(rpmr_widget)

        # TMP Row
        tmpr_widget = QWidget()
        tmpr_layout = QHBoxLayout()
        tmpr_widget.setLayout(tmpr_layout)
        tmp_button = QPushButton("TMP")
        tmp_value = QLabel()
        tmpr_layout.addWidget(tmp_button)
        tmpr_layout.addWidget(tmp_value)
        es_layout.addWidget(tmpr_widget)

        # LOAD Row
        lodr_widget = QWidget()
        lodr_layout = QHBoxLayout()
        lodr_widget.setLayout(lodr_layout)
        lod_button = QPushButton("LOAD")
        lod_value = QLabel()
        lodr_layout.addWidget(lod_button)
        lodr_layout.addWidget(lod_value)
        es_layout.addWidget(lodr_widget)

        ####################
        # -- Bottom Row -- #
        ####################

        bot_widget = QWidget()
        bot_layout = QHBoxLayout()
        bot_widget.setLayout(bot_layout)
        bot_widget.setStyleSheet("background-color: #232323")
        dash_layout.addWidget(bot_widget,2,1,1,2)

        # Left spacing
        bot_layout.addSpacerItem(QSpacerItem(80,10))

        # Date / time label
        bot_date = QLabel("Test")
        bot_date.setFont(QFont('Fira Sans Light', 16))
        bot_date.setAlignment(Qt.AlignVCenter)
        bot_date.setStyleSheet("color: #009D65")
        bot_layout.addWidget(bot_date)

        # Center spacing
        bot_layout.addSpacerItem(QSpacerItem(200,10))

        # Power button
        bot_pwr = QPushButton("Power Off")
        bot_pwr.clicked.connect(self.powerOff)
        bot_hot = QPushButton("Exit")
        bot_hot.clicked.connect(self.exitWindow)
        bot_hot.isCheckable()
        bot_hot.isChecked()
        bot_layout.addWidget(bot_pwr)
        bot_layout.addWidget(bot_hot)

    ##########################
    # -- Helper Functions -- #
    ##########################

    # ------ EVENTS ------- #
    def exitWindow(self):
        self.close()
    def powerOff(self):
        os.system('systemctl poweroff')

    def UpdateValues(self):
        if self.connection.is_connected():
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
        else:
            if self.connection.is_connected():
                self.connection.watch(obd.commands.SPEED)
                self.connection.watch(obd.commands.RPM)
                self.connection.watch(obd.commands.INTAKE_PRESSURE)
                self.connection.watch(obd.commands.INTAKE_TEMP)
                self.connection.watch(obd.commands.COOLANT_TEMP)
                self.connection.watch(obd.commands.ENGINE_LOAD)
                self.connection.watch(obd.commands.ELM_VOLTAGE)
                self.connection.start()
            else:
                # Wait 3 seconds, check if OBD connection is reestablished
                time.sleep(3)


def main():
   app = QApplication(sys.argv)
   app.setStyle('Fusion')
   dash = Dashboard()
   dash.showFullScreen()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()
