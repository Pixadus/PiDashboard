from ctypes import alignment
import sys, obd, os, cv2, time, threading
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import queue as Queue
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
        self.refresh_rate = 0.5

        # Graph x-axis range (in seconds)
        mpg_x_range = 60 
        speed_x_range = 60
        rpm_x_range = 60
        tmp_x_range = 60
        voltage_x_range = 60
        load_x_range = 60

        # Average value sample set size
        self.avg_val_sample_size = 2500

        self.queue = Queue.Queue()
        # Image capture options
        self.IMG_SIZE    = 1920,1080         # 640,480 or 1280,720 or 1920,1080
        self.CAP_API     = cv2.CAP_ANY       # or cv2.CAP_DSHOW, etc...
        self.EXPOSURE    = 0                 # Non-zero for fixed exposure
        self.CAPTURING   = True              # System will start capturing as soon as engine starts
        self.DISP_SCALE  = 5                 # Scaling factor for display image

        # Image save options
        self.sec_per_shot = 5
        self.path = datetime.now().strftime("%m-%d-%y-%H:%M:%S")
        self.number = 0
        os.mkdir(self.path)

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
        #self.timer.timeout.connect(self.UpdateValues)
        self.timer.timeout.connect(lambda: self.show_image(self.queue, self.vp_image, self.DISP_SCALE))        
        self.timer.start(int(self.refresh_rate*1000))
        self.capture_thread = threading.Thread(target=self.grab_images, args=(0, self.queue, self.CAPTURING))
        self.capture_thread.start()         # Thread to grab images

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
        self.vp_image = ImageWidget()
        vp_layout.addWidget(self.vp_image, alignment=Qt.AlignCenter)

        # Button row widget
        vp_br_widget = QWidget()
        vp_br_layout = QHBoxLayout()
        vp_br_widget.setLayout(vp_br_layout)
        vp_br_play = QPushButton("Start")
        vp_br_play.clicked.connect(self.startCapture)
        vp_br_stop = QPushButton("Stop")
        vp_br_stop.clicked.connect(self.stopCapture)
        vp_br_layout.addWidget(vp_br_play)
        vp_br_layout.addWidget(vp_br_stop)
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

        # VLT Row
        vltr_widget = QWidget()
        vltr_layout = QHBoxLayout()
        vltr_widget.setLayout(vltr_layout)
        vlt_button = QPushButton("VLT")
        vlt_value = QLabel()
        vltr_layout.addWidget(vlt_button)
        vltr_layout.addWidget(vlt_value)
        es_layout.addWidget(vltr_widget)

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
        self.bot_date = QLabel("Test")
        self.bot_date.setFont(QFont('Fira Sans Light', 16))
        self.bot_date.setAlignment(Qt.AlignVCenter)
        self.bot_date.setStyleSheet("color: #009D65")
        now = datetime.now()
        self.bot_date.setText(now.strftime("%H:%M:%S - %B %d, %Y"))
        bot_layout.addWidget(self.bot_date)

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
        self.CAPTURING=False
        self.close()
    def powerOff(self):
        self.capture_thread._stop()
        os.system('systemctl poweroff')
    def startCapture(self):
        self.CAPTURING=True
        self.capture_thread = threading.Thread(target=self.grab_images, args=(0, self.queue, self.CAPTURING))
        self.capture_thread.start()         # Thread to grab images
    def stopCapture(self):
        self.CAPTURING=False

    # Grab images from the camera (separate thread)
    def grab_images(self, cam_num, queue, capturing):
        cap = cv2.VideoCapture(cam_num-1 + self.CAP_API)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.IMG_SIZE[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.IMG_SIZE[1])
        if self.EXPOSURE:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0)
            cap.set(cv2.CAP_PROP_EXPOSURE, self.EXPOSURE)
        else:
            cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
        while True:
            if self.CAPTURING:
                if cap.grab():
                    retval, image = cap.retrieve(0)
                    if image is not None and queue.qsize() < 2:
                        queue.put(image)
                    else:
                        time.sleep(self.refresh_rate / 1000.0)
                else:
                    print("Error: can't grab camera image")
                    break
            else:
                break
        cap.release()       


    # Fetch camera image from queue, and display it
    def show_image(self, imageq, display, scale):
        if not imageq.empty():
            image = imageq.get()
            if image is not None and len(image) > 0:
                img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                self.save_image(img)
                self.display_image(img, display, scale)

    # Saves the image
    def save_image(self, img):
        if self.number % self.sec_per_shot*2 == 0:
            cv2.imwrite(self.path+"/IMG-"+str(int(self.number/(self.sec_per_shot*2)))+'.png', img)
        self.number+=1

    # Display an image, reduce size if required
    def display_image(self, img, display, scale=1):
        disp_size = img.shape[1]//scale, img.shape[0]//scale
        disp_bpl = disp_size[0] * 3
        if scale > 1:
            img = cv2.resize(img, disp_size, 
                             interpolation=cv2.INTER_CUBIC)
        qimg = QImage(img.data, disp_size[0], disp_size[1], disp_bpl, QImage.Format_RGB888)
        display.setImage(qimg)
        
    def UpdateValues(self):
        now = datetime.now()
        self.bot_date.setText(now.strftime("%H:%M:%S - %B %d, %Y"))
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
            self.rpm_value.setText(str(round(RPM,2)))
            self.spd_value.setText(str(round(MPH_SPEED,2)))
            self.mpg_value.setText(str(round(MPG,2)))
            self.tmp_value.setText(str(round(CLT_TMP,2)))
            self.vlt_value.setText(str(round(VOLTAGE,2)))
            self.lod_value.setText(str(round(LOAD,2)))

            # == Set Detailed Values == #
            # self.speed_lmi.setText(str(round(MPH_SPEED,2)))
            # self.speed_lma.setText(str(round(speed_mavg,2)))
            # self.rpm_lmi.setText(str(round(RPM,2)))
            # self.rpm_lma.setText(str(round(rpm_mavg,2)))
            # self.mpg_lmi.setText(str(round(MPG,2)))
            # self.mpg_lma.setText(str(round(mpg_mavg,2)))
            # self.tmp_lmi.setText(str(round(CLT_TMP,2)))
            # self.tmp_lma.setText(str(round(tmp_mavg,2)))
            # self.voltage_lmi.setText(str(round(VOLTAGE,2)))
            # self.voltage_lma.setText(str(round(voltage_mavg,2)))
            # self.load_lmi.setText(str(round(LOAD,2)))
            # self.load_lma.setText(str(round(load_mavg,2)))

            # # == Update Graphs == #
            # self.speed_gp.setData(self.speed_x_time,self.speed_y_speed)
            # self.rpm_gp.setData(self.rpm_x_time, self.rpm_y_rpm)
            # self.mpg_gp.setData(self.mpg_x_time,self.mpg_y_mpg)
            # self.tmp_gp.setData(self.tmp_x_time,self.tmp_y_tmp)
            # self.voltage_gp.setData(self.tmp_x_time,self.voltage_y_voltage)
            # self.load_gp.setData(self.load_x_time,self.load_y_load)
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
                # Try reestablishing connection
                self.connection = obd.Async()
    
#############################
# -- Image Custom Widget -- #
#############################
class ImageWidget(QWidget):
    def __init__(self, parent=None):
        super(ImageWidget, self).__init__(parent)
        self.image = None

    def setImage(self, image):
        self.image = image
        self.setMinimumSize(image.size())
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        if self.image:
            qp.drawImage(QPoint(0, 0), self.image)
        qp.end()



def main():
   app = QApplication(sys.argv)
   app.setStyle('Fusion')
   dash = Dashboard()
   dash.showFullScreen()
   sys.exit(app.exec_())
	
if __name__ == '__main__':
   main()
