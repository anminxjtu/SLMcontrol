# import slm
from slm import slm_control as slmPy
from snAPI.Main import *
# import matplotlib
# matplotlib.use('TkAgg',force=True)
# from matplotlib import pyplot as plt
# print("Switched to:",matplotlib.get_backend())
# import else
from log_sys import *
import time
import threading
import math
import wx
import sys

class myPico():
    def __init__(self,slm):
        self.TH260 = snAPI(libType=LibType.TH260)
        self.TH260.getDevice()
        
        # # alternatively read data from file
        self.TH260.setLogLevel(LogLevel.DataFile, True)
        self.TH260.initDevice(MeasMode.T2)
        self.TH260.device.setSyncTrigMode(syncTrigMode = TrigMode.CFD)
        self.TH260.device.setSyncDiv(syncDiv = 1)
        self.TH260.device.setSyncCFD(syncDiscrLvl = -50, syncZeroXLvL = -10)       # [mV]
        self.TH260.device.setSyncChannelOffset(syncChannelOffset = -1000)             # [ps] This sets a virtual delay time to the sync pulse. This is equivalent to changing the cable length on the sync input. The current resolution is the device's base resolution.
        # self.TH260.device.setSyncDeadTime(syncDeadTime = 24000)                             # [ps] TH206P only [24000, 44000, 66000, 88000, 112000, 135000, 160000 or 180000]
        self.TH260.device.setStopOverflow(stopCount = 4294967295)
        self.TH260.device.setInputCFD(channel = -1, discrLvl = -50, zeroXLvl = -10) # [ps]
        self.TH260.device.setInputChannelOffset(channel = -1, chanOffs = 0)
        self.TH260.device.setInputChannelEnable(channel = -1, chanEna = 1)
        self.TH260.device.setInputDeadTime(channel = -1, deadTime = 24000)               # [ps] TH206P only [24000, 44000, 66000, 88000, 112000, 135000, 160000 or 180000]
        
        # ----------create channels----------
        # second method
        self.cc_channel = self.TH260.manipulators.coincidence(chans = [0,1], windowTime = 3000, mode = CoincidenceMode.CountAll, keepChannels = True)

        # third method
        self.herald_channel = self.TH260.manipulators.herald(herald = 0, gateChans = [1], delayTime = 0, gateTime = 10000, keepChannels = True)
        self.TH260.manipulators.getConfig()


        # # enable this to get info about loading config
        self.TH260.setLogLevel(logLevel=LogLevel.Config, onOff=True)
        self.TH260.loadIniConfig("snAPI\TH260P.ini")

        # print complete device config structure
        self.TH260.logPrint("----------------------------------------------")
        self.TH260.logPrint(json.dumps(self.TH260.deviceConfig, indent=2))
        
        # device serial number (name)
        self.TH260.logPrint("----------------------------------------------")
        self.TH260.logPrint("Serial Number:", self.TH260.deviceConfig["ID"])
        
        # trigger/ discriminator level of all channels 
        self.TH260.logPrint("----------------------------------------------")
        for channel in self.TH260.deviceConfig["ChansCfg"]:
            if channel["TrigMode"] == "Edge":
                self.TH260.logPrint("Chan", channel["Index"], "- TrigLvl:", channel["TrigLvl"])
            elif channel["TrigMode"] == "CFD":
                self.TH260.logPrint("Chan", channel["Index"], "- DiscrLvl :", channel["DiscrLvl"])

        # print enable state channel 2 (this is the second channel - the first one has index 0)
        self.TH260.logPrint("----------------------------------------------")
        self.TH260.logPrint("Chan 1:", "enabled" if self.TH260.deviceConfig["ChansCfg"][0]["ChanEna"] else "disabled")

        # reads measurement description that contains special information about the measurement
        self.TH260.logPrint("----------------------------------------------")
        self.TH260.getMeasDescription()
        self.TH260.logPrint(json.dumps(self.TH260.measDescription, indent=2))
        self.TH260.logPrint("----------------------------------------------")
        # self.TH260.logPrint(json.dumps(, indent=2))
        print(self.TH260.getNumAllChannels())
        time.sleep(1)
        # self.TH260.closeDevice()
        # sys.exit()

        self.mea_flag = 0

        # self.setParameter()
        # logger.warning('----------TH260P initializes fishing!-----------')
        self.slm = slm

        self.GUI()
        logger.warning('----------GUI initializes fishing!-----------')


    def setParameter(self):
        pass

    def runMea(self):
        self.mea_flag = 1
        self.mea_thread = threading.Thread(target=self.run, name = 'Mea')

        self.mea_thread.start()

        # self.mea_thread.join() # Blocking the main thread

        expData = [1,2,3]
        
        pass

    def run(self):
        # assert(self.mea_flag)
        self.TH260.histogram.setRefChannel(channel = 0)
        # self.TH260.histogram.setBinWidth(binWidth = 1000)

        self.TH260.timeTrace.setNumBins(2)
        self.TH260.timeTrace.setHistorySize(1)
        self.TH260.timeTrace.measure(acqTime = 0, waitFinished = False, savePTU = False)    # acqTime: int (default: 1s) 0: means the measurement will run until :meth:`stopMeasure`

        while True:
            finished = self.TH260.timeTrace.isFinished()
            if self.mea_flag == 1 and self.window.uiclose_flag == 0:
                # TODO: some runing code and data saving
                ### ----------------first method---------------------------
                cntRs = self.TH260.getCountRates()
                syncrate = cntRs[0]
                chan1rate = cntRs[1]
                logger.error('sync:{} chal1:{}'.format(syncrate, chan1rate))
                # self.poData2GUI([syncrate, chan1rate, 123])

                ### ----------------second method---------------------------
                # self.TH260.histogram.measure(acqTime = 1000, waitFinished = True, savePTU = False)
                # data, bins = self.TH260.histogram.getData()
                # logger.warning('data:{} bins:{}'.format(data, bins))
                # logger.error('data_size:{} bins_size:{}'.format(data.shape, bins.shape))
                # logger.error('sync:{} chanl1:{} cc:{} herald:{}'.format(sum(data[0]), sum(data[1]), sum(data[2]), sum(data[3])))

               

                # ----------- Timetrace get data-------------------
                counts, times = self.TH260.timeTrace.getData() 
                syncrate = counts[0][-1]
                chan1rate = counts[1][-1]
                ccrate = counts[self.cc_channel][-1]
                hrate = counts[self.herald_channel][-1]
                logger.error('times:{} sync:{} chal1:{} cc:{} herald:{}'.format(times, counts[0], counts[1], counts[self.cc_channel], hrate))
                # print(type(syncrate))
                # print(type(chan1rate))
                # print(type(ccrate))
                self.poData2GUI([syncrate, chan1rate, ccrate, hrate[-1]])
                # -------------------------------------------------
                time.sleep(0.3)

                # # second method
                # self.TH260.manipulators.coincidence(chans = [0,1], windowTime = 2000, mode = CoincidenceMode.CountAll, keepChannels = True)

                # # third method
                # self.TH260.manipulators.herald(herald = 0, gateChans = [1], delayTime = 0, gateTime = 2000, keepChannels = True)


            if self.window.uiclose_flag == 1 or finished == True:
            # if self.window.uiclose_flag == 1:
                self.TH260.timeTrace.stopMeasure()
                time.sleep(2)
                self.TH260.closeDevice()
                break
            
        sys.exit()



        # self.mea_flag = 0

    def dataSav(self, data_path):
        pass

    def GUI(self):      # 将 SLM 传入 GUI 便于操控
        self.gui_thread = threading.Thread(target=self.disguiWindows, name = 'GUIdisplay')
        self.gui_thread.start()
        pass


    def disguiWindows(self):
        app = QApplication(sys.argv)
        self.window = Ui(self.slm)  # 将slm传入UI，便于交互
        self.window.show()
        # app.exec_()
        sys.exit(app.exec_())

    def poData2GUI(self, data):
        self.window.countDispaly(data)



    def quitMea(self):
        # TODO: delete the device
        pass

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QGraphicsPixmapItem, QGraphicsScene
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from PyQt5 import uic

class Ui(QMainWindow):
    def __init__(self,slm):
        lock.acquire()

        super(Ui,self).__init__()
        self.slm = slm
        self.uiclose_flag = 0

        self.ui = uic.loadUi("OAM_v1.ui", self)

        self.ui.chal1_dis.setDigitCount(7)
        self.ui.chal2_dis.setDigitCount(7)
        self.ui.cc_dis.setDigitCount(7)
        self.ui.herald_dis.setDigitCount(7)

        self.ui.spinBox_OAM1.setRange(-20,20)
        self.ui.spinBox_OAM2.setRange(-20,20)
        self.ui.spinBox_OAM3.setRange(-20,20)

        self.ui.spinBox_OAM1_2.setRange(-20,20)
        self.ui.spinBox_OAM2_2.setRange(-20,20)
        self.ui.spinBox_OAM3_2.setRange(-20,20)

        self.ui.spinBox_OAM1_3.setRange(-20,20)
        self.ui.spinBox_OAM2_3.setRange(-20,20)
        self.ui.spinBox_OAM3_3.setRange(-20,20)
        
        self.ui.spinBox_AMP1.setRange(-20,20)
        self.ui.spinBox_AMP2.setRange(-20,20)
        self.ui.spinBox_AMP3.setRange(-20,20)

        self.ui.spinBox_AMP1_2.setRange(-20,20)
        self.ui.spinBox_AMP2_2.setRange(-20,20)
        self.ui.spinBox_AMP3_2.setRange(-20,20)

        self.ui.spinBox_AMP1_3.setRange(-20,20)
        self.ui.spinBox_AMP2_3.setRange(-20,20)
        self.ui.spinBox_AMP3_3.setRange(-20,20)

        self.ui.spinBox_xbias1.setRange(-960,960)
        self.ui.spinBox_ybias1.setRange(-960,960)

        self.ui.spinBox_xbias1_2.setRange(-960,960)
        self.ui.spinBox_ybias1_2.setRange(-960,960)

        self.ui.spinBox_xbias1_3.setRange(-960,960)
        self.ui.spinBox_ybias1_3.setRange(-960,960)

        self.ui.spinBox_xbias1_2.setValue(175)
        self.ui.spinBox_ybias1_2.setValue(-40)
        self.ui.spinBox_xbias1_3.setValue(-5)
        self.ui.spinBox_ybias1_3.setValue(-500)
        
        # self.ui.doubleSpinBox_PHA1.setRange(-3.14,3.14,0.05)

        self.ui.pushButton_refresh1.clicked.connect(
            lambda value: self.refresh_0()
        )

        self.ui.pushButton_refresh1_2.clicked.connect(
            lambda value: self.refresh_1()
        )

        self.ui.pushButton_refresh1_3.clicked.connect(
            lambda value: self.refresh_2()
        )

        self.ui.pushButton_close.clicked.connect(
            lambda value: self.close()
        )

        lock.release()

    def close(self):
         self.uiclose_flag = 1
         time.sleep(1)
         sys.exit(0)


    def countDispaly(self,data):
        self.ui.chal1_dis.display(data[0])
        self.ui.chal2_dis.display(data[1])
        self.ui.cc_dis.display(data[2])
        self.ui.herald_dis.display(data[3])

        

    def refresh_0(self):
        _which_frame = 1
        lock.acquire()
        acquired_amp = []
        acquired_amp.append(int(self.ui.spinBox_AMP1.value()))
        acquired_amp.append(int(self.ui.spinBox_AMP2.value()))
        acquired_amp.append(int(self.ui.spinBox_AMP3.value()))

        acquired_pha = []
        acquired_pha.append(float(self.ui.doubleSpinBox_PHA1.value()))
        acquired_pha.append(float(self.ui.doubleSpinBox_PHA2.value()))
        acquired_pha.append(float(self.ui.doubleSpinBox_PHA3.value()))

        acquired_oam = []
        acquired_oam.append(int(self.ui.spinBox_OAM1.value()))
        acquired_oam.append(int(self.ui.spinBox_OAM2.value()))
        acquired_oam.append(int(self.ui.spinBox_OAM3.value()))

        new_ell = {}
        new_ell['Amp'] = acquired_amp
        new_ell['Pha'] = acquired_pha
        new_ell['Topo'] = acquired_oam

        wbais = self.ui.spinBox_xbias1.value()
        hbais = self.ui.spinBox_ybias1.value()

        def postfun(new_ell,which_frame):
            _pic = slmPy.Superhologram(new_ell, 1920, 1080, wbais, hbais).img
            # TODO: POST the pic to the thread: wx
            event = slmPy.ImageEvent()
            event.img = _pic
            wx.PostEvent(self.slm.frame[which_frame], event)    # 怎么把球传出去
            # time.sleep(0.2)
            _pic.SaveFile('slm'+str(which_frame-1)+'.png', wx.BITMAP_TYPE_PNG)

        
        

        GUI2SLMdisplay_thread = threading.Thread(target = postfun, name = 'GUIinput_2SLMdisplay', args= (new_ell,_which_frame,))
        GUI2SLMdisplay_thread.start()
        logger.warning('GUIinput is posted to SLMdisplay')
        GUI2SLMdisplay_thread.join()
        TH260P.window.holoDisplay(_which_frame-1)
        lock.release()

    def refresh_1(self, new_ell = {}, direct_call = False):
        _which_frame = 2
        lock.acquire()
        if direct_call == False:
            acquired_amp = []
            acquired_amp.append(int(self.ui.spinBox_AMP1_2.value()))
            acquired_amp.append(int(self.ui.spinBox_AMP2_2.value()))
            acquired_amp.append(int(self.ui.spinBox_AMP3_2.value()))

            acquired_pha = []
            acquired_pha.append(float(self.ui.doubleSpinBox_PHA1_2.value()))
            acquired_pha.append(float(self.ui.doubleSpinBox_PHA2_2.value()))
            acquired_pha.append(float(self.ui.doubleSpinBox_PHA3_2.value()))

            acquired_oam = []
            acquired_oam.append(int(self.ui.spinBox_OAM1_2.value()))
            acquired_oam.append(int(self.ui.spinBox_OAM2_2.value()))
            acquired_oam.append(int(self.ui.spinBox_OAM3_2.value()))

            new_ell = {}
            new_ell['Amp'] = acquired_amp
            new_ell['Pha'] = acquired_pha
            new_ell['Topo'] = acquired_oam

        wbais = self.ui.spinBox_xbias1_2.value()
        hbais = self.ui.spinBox_ybias1_2.value()

        def postfun(new_ell, which_frame):
            _pic = slmPy.Superhologram(new_ell, int(1920/2), 1080, wbais, hbais).img     # Here splitting because of 1920/2
            # TODO: POST the pic to the thread: wx
            event = slmPy.ImageEvent()
            event.img = _pic
            wx.PostEvent(self.slm.frame[which_frame], event)    # 怎么把球传出去
            # time.sleep(0.2)
            _pic.SaveFile('slm'+str(which_frame-1)+'.png', wx.BITMAP_TYPE_PNG)

        
        

        GUI2SLMdisplay_thread = threading.Thread(target = postfun, name = 'GUIinput_2SLMdisplay', args= (new_ell,_which_frame,))
        GUI2SLMdisplay_thread.start()
        logger.warning('GUIinput is posted to SLMdisplay')
        GUI2SLMdisplay_thread.join()
        TH260P.window.holoDisplay(_which_frame-1)
        lock.release()   


    def refresh_2(self, new_ell = {}, direct_call = False):
        _which_frame = 2
        lock.acquire()
        if direct_call == False:
            acquired_amp = []
            acquired_amp.append(int(self.ui.spinBox_AMP1_3.value()))
            acquired_amp.append(int(self.ui.spinBox_AMP2_3.value()))
            acquired_amp.append(int(self.ui.spinBox_AMP3_3.value()))

            acquired_pha = []
            acquired_pha.append(float(self.ui.doubleSpinBox_PHA1_3.value()))
            acquired_pha.append(float(self.ui.doubleSpinBox_PHA2_3.value()))
            acquired_pha.append(float(self.ui.doubleSpinBox_PHA3_3.value()))

            acquired_oam = []
            acquired_oam.append(int(self.ui.spinBox_OAM1_3.value()))
            acquired_oam.append(int(self.ui.spinBox_OAM2_3.value()))
            acquired_oam.append(int(self.ui.spinBox_OAM3_3.value()))

            new_ell = {}
            new_ell['Amp'] = acquired_amp
            new_ell['Pha'] = acquired_pha
            new_ell['Topo'] = acquired_oam

        wbais = self.ui.spinBox_xbias1_3.value()
        hbais = self.ui.spinBox_ybias1_3.value()

        def postfun(new_ell, which_frame):
            _pic = slmPy.Superhologram(new_ell, int(1920/2), 1080, wbais, hbais).img     # Here splitting because of 1920/2
            # TODO: POST the pic to the thread: wx
            event = slmPy.ImageEvent()
            event.img = _pic
            event.split = True
            wx.PostEvent(self.slm.frame[which_frame], event)    # 怎么把球传出去
            # time.sleep(0.1)
            _pic.SaveFile('slm'+str(which_frame)+'.png', wx.BITMAP_TYPE_PNG)

        
        

        GUI2SLMdisplay_thread = threading.Thread(target = postfun, name = 'GUIinput_2SLMdisplay', args= (new_ell,_which_frame,))
        GUI2SLMdisplay_thread.start()
        logger.warning('GUIinput is posted to SLMdisplay')
        GUI2SLMdisplay_thread.join()
        TH260P.window.holoDisplay(_which_frame)
        lock.release()   
        
        
        # self.slm.frame[0].Window.img.SaveFile('slm0.png', wx.BITMAP_TYPE_PNG)
        # TH260P.window.holoDisplay(0)


    def holoDisplay(self,frame):
        holopng = 'slm'+ str(frame) +'.png'
        # _pic = QImage(holopng)
        # _pix = QPixmap.fromImage(_pic)
        # item = QGraphicsPixmapItem(_pix)
        # scene = QGraphicsScene()
        # scene.addItem(item)
        # self.ui.graphicsView.setScene(scene)
        # self.ui.cc_dis.display(111111)

        _pic = QPixmap(holopng)
        if   frame == 0:
                self.ui.SLM0.setPixmap(_pic)
                self.ui.SLM0.setScaledContents(True)
        elif frame == 1:
                self.ui.SLM1.setPixmap(_pic)
                self.ui.SLM1.setScaledContents(True)
        elif frame == 2:
                self.ui.SLM2.setPixmap(_pic)
                self.ui.SLM2.setScaledContents(True)
        return 


            



PI = math.pi

if __name__ == '__main__':
    # lock = threading.Lock()


    # SLM = slmPy.SLMdisplay(3)

    # TH260P = myPico(SLM)

    # time.sleep(3)
    # logger.warning('----------1111111111!-----------')
    # b = {'Amp':[1],'Pha':[0],'Topo':[0]}
    # c = {'Amp':[1],'Pha':[0],'Topo':[1]}
    # d = {'Amp':[1],'Pha':[0],'Topo':[-1]}

    # WBAIS = 0
    # HBAIS = 0
    # SLM.refresh(1, WBAIS, HBAIS, b)
    # SLM.frame[1].Window.img.SaveFile('slm0.png', wx.BITMAP_TYPE_PNG)
    # TH260P.window.holoDisplay(0)

    # TH260P.window.refresh_1(b, direct_call = True)
    # TH260P.window.refresh_2(c, direct_call = True)
    # time.sleep(2)
    # TH260P.runMea()

    

    lock = threading.Lock()
    SLM = slmPy.SLMdisplay(3)
    TH260P = myPico(SLM)
    b = {'Amp':[1],'Pha':[0],'Topo':[0]}
    c = {'Amp':[1],'Pha':[0],'Topo':[1]}
    d = {'Amp':[1],'Pha':[0],'Topo':[-1]}

    WBAIS = 0
    HBAIS = 0
    SLM.refresh(1, WBAIS, HBAIS, b)
    SLM.frame[1].Window.img.SaveFile('slm0.png', wx.BITMAP_TYPE_PNG)
    TH260P.window.holoDisplay(0)

    TOPO = [-2,-1,0,1,2]
    BASIS_NUM = len(TOPO)
    MEA_BAS = []
    for i in range(0,BASIS_NUM-1):
        for j in range(i+1,BASIS_NUM):
            AMP = [0,0,0,0,0]
            PHA = [0,0,0,0,0]
            # TODO: please optimize the calculation of LG, remove the redundant calculation
            for k in range(0,6):
                if k == 0:
                    AMP[i] = 1
                elif k == 1:
                    AMP[j] = 1
                elif k == 2:
                    AMP[i] = 1
                    AMP[j] = 1
                elif k == 3:
                    AMP[i] = 1
                    AMP[j] = 1
                    PHA[j] = PI
                elif k == 4:
                    AMP[i] = 1
                    AMP[j] = 1
                    PHA[j] = PI/2
                elif k == 5:
                    AMP[i] = 1
                    AMP[j] = 1
                    PHA[j] = -PI/2
                MEA_BAS.append({'Amp':AMP,'Pha':PHA,'Topo':TOPO})
                AMP = [0,0,0,0,0]
                PHA = [0,0,0,0,0]
    MEA_BAS_NUM =len(MEA_BAS)
    with open('.\\mea_base.txt','w', encoding = 'utf-8') as f:
        for i in range(0,MEA_BAS_NUM):
            f.write(json.dumps(MEA_BAS[i]))
            f.write('\n')

    import os
    import datetime
    current_path = os.path.abspath('.')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d' '-%H-%M-%S')

    data_path = current_path + '\\' + current_time
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    MEA_COUNT = 0

    time1 = datetime.datetime.now()
    for i in range(0,MEA_BAS_NUM):
        sync = MEA_BAS[i]
        TH260P.window.refresh_1(sync, direct_call = True)
        for j in range(0,MEA_BAS_NUM):
            cha1 = MEA_BAS[j]
            TH260P.window.refresh_2(cha1, direct_call = True)
            time.sleep(0.1)
            #------------------------------------------
            COLLECT_TIME = int(5.5*1000)       # int:[ms]  how many times to collect data
            COLLECT_INTERVAL = 1               # [s]   interval between two collect
            COLLECT_T = COLLECT_TIME * COLLECT_INTERVAL
            TH260P.TH260.timeTrace.setNumBins(10)
            TH260P.TH260.timeTrace.setHistorySize(5)    # []
            TH260P.TH260.timeTrace.measure(acqTime = COLLECT_T, waitFinished = True, savePTU = False)      # acqTime: [ms]
            
            # set the save 
            assert(TH260P.TH260.timeTrace.isFinished())
            counts, times = TH260P.TH260.timeTrace.getData(normalized = False) 
            # TH260P.TH260.timeTrace.stopMeasure()
            syncrate = counts[0][-1]
            chan1rate = counts[1][-1]
            ccrate = counts[TH260P.cc_channel][-1]
            hrate = counts[TH260P.herald_channel][-1]
            TH260P.poData2GUI(([syncrate, chan1rate, ccrate, hrate[-1]]))
            # TODO: save the data
            with open(data_path + '\\' + 'sync_' + str(i) + 'chal1_' + str(j) + '.txt','w', encoding = 'utf-8') as f:
                f.write(json.dumps([i,MEA_BAS[i],j,MEA_BAS[j]]))
                f.write('\n')
                f.write(json.dumps(times.tolist()))
                f.write('\n')
                f.write(json.dumps(counts[0].tolist()))
                f.write('\n')
                f.write(json.dumps(counts[1].tolist()))
                f.write('\n')
                f.write(json.dumps(counts[TH260P.cc_channel].tolist()))
                f.write('\n')
                f.write(json.dumps(counts[TH260P.herald_channel].tolist()))
                MEA_COUNT += 1
                time2 = datetime.datetime.now()
                time_elapsed = time2-time1
                percentange = MEA_COUNT/MEA_BAS_NUM**2
                expect_finishtime = time1 + time_elapsed/percentange
                logger.error('MEA_COUNT:{} PERCENTAGE:{} TIME_ELAPSED:{} '.format(MEA_COUNT, percentange, time_elapsed))
                logger.error('Expected finish time:{}'.format(expect_finishtime))
                TH260P.window.expected_finishedtime.setText('Expect finishing at: {}'.format(expect_finishtime))
                if TH260P.window.uiclose_flag == 1:
                    TH260P.TH260.closeDevice()
                    time.sleep(1)
                    sys.exit(0)





    # TH260P.poData2GUI([1,2,3])
    # time.sleep(1)
    # TH260P.poData2GUI([4,5,6])
    # time.sleep(1)
    # TH260P.poData2GUI([7,8,9])
    # time.sleep(1)
    


    # a = {'Amp':[1,2,3,4],'Pha':[PI,-PI,PI/2,0],'Topo':[1,2,3,4]}
    # b = {'Amp':[1],'Pha':[0],'Topo':[0]}
    # b = {'Amp':[1,1],'Pha':[0,0],'Topo':[-1,1]}

    WBAIS = 0
    HBAIS = 0
    
    # SLM.refresh(1, WBAIS, HBAIS, b)
    # SLM.frame[1].Window.img.SaveFile('slm1.png', wx.BITMAP_TYPE_PNG)
    # TH260P.window.holoDisplay(1)

    # SLM.refresh(2, WBAIS, HBAIS, b)
    # SLM.frame[2].Window.img.SaveFile('slm2.png', wx.BITMAP_TYPE_PNG)
    # TH260P.window.holoDisplay(2)

    # time.sleep(2)


    # SLM.refresh(1,0)
    # SLM.refresh(2,1)

    # for i in range(0,100):
    #     SLM.refresh(0,1)
    #     SLM.refresh(0,1)
    #     SLM.refresh(0,1)
    #     time.sleep(1)
    #     TH260P.runMea()


        
    


    # SLM.refresh(0,1)
    # logger.info('----------000000000-----------')
