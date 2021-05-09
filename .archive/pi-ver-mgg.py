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
        refresh_rate = 1

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

        self.title = 'Endurance'
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
        vp_widget.setStyleSheet("background-color: #232323")
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
        es_widget.setStyleSheet("background-color: #232323")
        dash_layout.addWidget(es_widget,1,2)

        # ES Label
        es_label = QLabel("Engine Status")
        es_label.setFont(QFont('Fira Sans', 18))
        es_label.setAlignment(Qt.AlignCenter)
        es_label.setStyleSheet("color: #FFFFFF")
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
        os.system('sudo shutdown now')


def main():
   app = QApplication(sys.argv)
   dash = Dashboard()
   dash.showFullScreen()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()
