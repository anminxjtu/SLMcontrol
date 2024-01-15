import wx
# from log_sys import *         # 单独运行

from slm.log_sys import *       # 作为包儿导入
import numpy as np
import math
import time
import threading
import datetime
import sys
import matplotlib.pyplot as plt
from scipy.special import assoc_laguerre

PI = math.pi
PIXELPITCH = 8e-6
BEAMWAIST = 5e-4
WAVELENGTH = 810e-9
# BLAZE = 20*PIXELPITCH
# BLAZE =2*PI/15514*1e-3
BLAZE = 9.25*PIXELPITCH

EVT_NEW_IMAGE = wx.PyEventBinder(wx.NewEventType(), 0)

class ImageEvent(wx.PyCommandEvent):
    def __init__(self, eventType=EVT_NEW_IMAGE.evtType[0], id=0):
        wx.PyCommandEvent.__init__(self, eventType, id)
        self.img = None
        self.split = False      # Default: no splitting on SLM
        logger.info('----------Event init-----------')


class SLMframe(wx.Frame):

    def __init__(self,
               monitor):
        self.SetMonitor(monitor)
        super().__init__(None, 
                         -1, 
                         'SLM_monitor_%d' % monitor,
                         pos = (self._x0, self._y0), 
                         size = (self._resX, self._resY)
                         )
        self.Window = SLMwindow(self, 
                                res = (self._resX, self._resY))
        self.Window._x0 = self._x0
        self.Window._y0 = self._y0
        self.Window._resX = self._resX
        self.Bind(EVT_NEW_IMAGE, self.OnNewImage)
        # self.img = LGhologram(1, self._resX, self._resY).img
        # wx.StaticBitmap(self, -1, self.img, pos=(0, 0))
        # self.Show()
        # time.sleep(5)
        # self.img = LGhologram(2, self._resX, self._resY).img
        # wx.StaticBitmap(self.Window, -1, self.img, pos=(0, 0))
        # self.Refresh()

        logger.info('----------Frame: {} init finish!-----------'.format(monitor))
    def SetMonitor(self, monitor: int):
        if (monitor < 0 or monitor > wx.Display.GetCount()-1):
            raise ValueError('Invalid monitor (monitor %d).' % monitor)
        self._x0, self._y0, self._resX, self._resY = wx.Display(monitor).GetGeometry()
        logger.warning('Frame:{} -> x0: {} y0: {} resX: {} resY: {}'.format(monitor, self._x0, self._y0, self._resX, self._resY))

    def OnNewImage(self, event):
        logger.info('----------Frame ImageEvent handler-----------')
        self.Window.UpdateImage(event)

    def Quit(self):
        wx.CallAfter(self.Destroy)


class SLMwindow(wx.Window):

    def __init__(self,  *args, **kwargs):
        self.res = kwargs.pop('res')
        super().__init__(*args, **kwargs)
        
        # hide cursor
        cursor = wx.Cursor(wx.CURSOR_BLANK)
        self.SetCursor(cursor) 
        
        self.img = wx.Image(*self.res)
        self._Buffer = wx.Bitmap(*self.res)
        self.Bind(EVT_NEW_IMAGE, self.UpdateImage)
        # self.Bind(wx.EVT_PAINT,self.OnPaint)

        # print(self.res[1])
        # print(type(*self.res))
        # self.img = LGhologram(1, self.res[0], self.res[1]).img

        # wx.StaticBitmap(self, -1, self.img, pos=(0, 0))
        # wx.StaticBitmap(self, -1, self.img, pos=(0, 0))
        
    # def OnPaint(self, event):
    #     # self._Buffer = self.img.ConvertToBitmap()
    #     # dc = wx.BufferedPaintDC(self, self._Buffer)
    #     # time.sleep(1)
    #     wx.StaticBitmap(self, -1, self.img, pos=(0, 0))


    def UpdateImage(self, event):
        logger.info('Update image-----------')
        # self.img = event.img
        
        # dc = wx.BufferedPaintDC(self, self.img.ConvertToBitmap())
        # dc.DrawBitmap(self._Buffer,0,0)
        
        # assert(event.img == self.img)
        if event.split == True:
            wx.StaticBitmap(self, -1, event.img, pos=(961, 0))
        else:
            wx.StaticBitmap(self, -1, event.img, pos=(0, 0))
        logger.info('self._x0:{} self._y0:{}'.format(self._x0, self._y0))
        self.Refresh(eraseBackground=True, rect=None)


class LGhologram():
    def __init__(self,
                 l,
                 w,
                 h,
                 p = 0,
                 wBias = 0,
                 hBias = 0,
                 pixelPitch = PIXELPITCH,
                 beamWaist = BEAMWAIST,
                 waveLength = WAVELENGTH,
                 blaze = BLAZE
                ):
        self.ell = l
        self.p = p
        self.blaze = blaze
        self.omega0 = beamWaist
        self.x = np.linspace(0, w, w)*pixelPitch
        self.y = np.linspace(0, h, h)*pixelPitch
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.xCenter = int((w+wBias)/2)
        self.yCenter = int((h+hBias)/2)
        self.X = self.X - self.xCenter*pixelPitch
        self.Y = self.Y - self.yCenter*pixelPitch
        self.r = np.sqrt(self.X**2 + self.Y**2)
        self.theta = np.arctan2(self.Y,self.X) 

        # if self.ell == 0:
        #     M = 1        # need a extra minus sign
        #     F = -math.pi
        #     mod = (F+2*math.pi*self.X/self.blaze)%(2*math.pi)   
        #     self.phaseMatrix = np.angle(np.exp(1j*M*mod))
        # elif isinstance(self.ell,dict) == True:
        #     _amp = self.ell['Amp']
        #     _isempty = 0
        #     for i in range(len(_amp)):
        #         if _amp[i] == 0:
        #             _isempty += 1
        #     if _isempty == len(_amp):
        #         M = 1        # need a extra minus sign
        #         F = -math.pi
        #         mod = (F+2*math.pi*self.X/self.blaze)%(2*math.pi)   
        #         self.phaseMatrix = np.angle(np.exp(1j*M*mod))
        #     else:
        #         self.phaseMatrix = self.phaseHologram()

        # else:   
        #     self.phaseMatrix = self.phaseHologram()
        # print(self.phaseMatrix)

        self.phaseMatrix = self.phaseHologram()
        self.img = self.convertToBitmap(self.phaseMatrix)

    def LGMode(self,_ell:int ,_p:int = 0, _z:float = 0):
        """
        generate the LG mode.

        Parameters
        ----------
        ell: int

          p: int

          z: float
             [m]
        """
        _k = 2*PI/WAVELENGTH
        _zR = _k*self.omega0**2/2
        _omegaz = math.sqrt(2*(_z**2+_zR**2)/_k/_zR)
        constantParameter = math.sqrt(1*math.factorial(2*_p)/math.pi/math.factorial(_p+abs(_ell)))/_omegaz
        firstTerm = ((np.sqrt(2)*self.r/_omegaz)**abs(_ell))
        secondTerm = np.exp(-self.r**2/_omegaz**2)*np.exp(1j*_ell*self.theta)
        thirdTerm = assoc_laguerre(2*self.r**2/_omegaz**2, _p, abs(_ell))
        zTerm = np.exp(1j*_k*self.r**2*_z/2/(_z+_zR**2))*np.exp(-1j*(2*_p+abs(_ell)+1)*math.atan2(_z/_zR))

        amplitude =  constantParameter*firstTerm*secondTerm*thirdTerm*zTerm
        intensity = amplitude*amplitude.conjugate()
        # print(amplitude/math.sqrt(sum(sum(intensity))))
        return  amplitude/sum(sum(np.sqrt(intensity)))
    
    def phaseHologram(self, modulation_depth = 1):
        self.AMP = self.LGMode(self.ell, self.p)
        lgAbs = abs(self.AMP)
        lgAngle = np.angle(self.AMP)
        sincInverse = self.asinc(lgAbs)
        M = 1 - 1/math.pi * sincInverse         # need a extra minus sign
        F = lgAngle - math.pi * M
        mod = (F+2*math.pi*modulation_depth*self.X/self.blaze)%(2*math.pi*modulation_depth)
        #-------------------------------------
        T = np.exp(1j*M*mod)
        return np.angle(T)

    def convertToBitmap(self, inputData):
        h,w = inputData.shape[0], inputData.shape[1]
        maxD = np.max(inputData)
        minD = np.min(inputData)
        inputData = (inputData - minD)/(maxD - minD)*255
        bw_array = np.around(inputData).astype('uint8')
        bw_array.shape = h, w, 1
        color_array = np.concatenate((bw_array,bw_array,bw_array), axis=2)
        data = color_array.tobytes()
        return wx.ImageFromBuffer(w, h, dataBuffer=data)


    def asinc(self, y):
         return  2*y+3/10*y**3+321/2800*y**5+3197/56000*y**7+445617/13798400*y**9+\
            1766784699/89689600000*y**11+317184685563/25113088000000*y**13+\
            14328608561991/1707689984000000*y**15+6670995251837391/1165411287040000000*y**17+\
            910588298588385889/228420612259840000000*y**19+\
            1889106915501879285127263/669318078043783168000000000*y**21+\
            122684251268939994619239/60571771768668160000000000*y**23+\
            86578199631805319180104483967/58899990867852918784000000000000*y**25+\
            36790913563978761395277930686421/34161994703354692894720000000000000*y**27+\
            295479400033606079171291233070109663/371437974410411888261201920000000000000*y**29+\
            5429197579977012936689051219262425180781/9174517967937173640051687424000000000000000*y**31+\
            111912180845235829957717919886518013347855667/252655431286439247725093999083520000000000000000*y**33+\
            21623582556767547163123245489615552651038372109/64865414807824606864932296091238400000000000000000*y**35+\
            1686950689722579328034933293949678511289600201851/6691379632807169971329857912569856000000000000000000*y**37+\
            362964877894310955248925785551248746981943835416147/1895485357802467420969439750506151936000000000000000000*y**39+\
            241119375769652087142546687133690376324455849576103305306113/1651328495419246089263940926464174667092459520000000000000000000*y**41+\
            62733744440681157939079200023293588467527441653821853933262223/561451688442543670349739914997819386811436236800000000000000000000*y**43+\
            90541073261492600342265407374539407149059862146954660576097727343/1055529174271982100257511040195900447205500125184000000000000000000000*y**45+\
            126749063504538759034999649107808731423757688715140874157349767781/1919143953221785636831838254901637176737272954880000000000000000000000*y**47+\
            249693053510060031661928074632553530869877798468407353253082594529911/4897091793534510236175803834629896837864823539630080000000000000000000000*y**49
    
class Superhologram(LGhologram):
    """
    This class is used to generate holograms of superposition state based on LGhologram class.
    """
    def _init__(self,
                l,
                w,
                h,
                p = 0,
                wBais = 0,
                hBais = 0,
                pixelPitch = PIXELPITCH,
                beamWaist = BEAMWAIST,
                waveLength = WAVELENGTH,
                blaze = BLAZE):
        super(LGhologram, self).__init__(l,w,h,p,wBais,hBais)
        pass

    def phaseHologram(self, modulation_depth = 1):
        # logger.error('This is superposition state phaseHologram function')
        _amplitude = self.ell['Amp']
        _phase = self.ell['Pha']
        _topo = self.ell['Topo']
        _topoP = self.ell['P']
        modulation_depth = self.ell['MD']

        _alen = len(_amplitude)
        _plen = len(_phase)
        _topolen = len(_topo)
        _topoplen = len(_topoP)

        if _alen != _plen or _topolen != _topoplen:
            logger.error('Superposition state form error, please check!')
            return
        _intensity = 0
        for i in range(_alen):
            _intensity += _amplitude[i]**2
        _intensity = math.sqrt(_intensity)

        _acopy = []
        for i in range(_alen):
            _acopy.append(_amplitude[i]/_intensity)
        
        self.AMP = 0
        for i in range(_alen):
            if _acopy[i] == 0:
                continue
            self.AMP += np.exp(_phase[i]*1j)*_acopy[i]*self.LGMode(_topo[i],_topoP[i])
        
        lgAbs = abs(self.AMP)

        # plt.imshow(lgAbs)
        # plt.show()

        lgAngle = np.angle(self.AMP)
        sincInverse = self.asinc(lgAbs)
        M = 1 - 1/math.pi * sincInverse         # need a extra minus sign
        F = lgAngle - math.pi * M
        mod = (F+2*math.pi*modulation_depth*self.X/self.blaze)%(2*math.pi*modulation_depth)
        #-------------------------------------
        T = np.exp(1j*M*mod)
        return np.angle(T)


###############
# 此类实现有问题，原则上只能开启一个mainloop
###############
# class  SLMdisplay:
#     def __init__(self,
#                  monitor = 0
#                  ):
#         self.monitor = monitor
#         self.display_thread = threading.Thread(target=self.run)
#         # print(self.display_thread._name)
#         # self.display_thread.daemon = True
#         self.display_thread.start()
#         time.sleep(2)
#         print('----------------sleep over----------------')
        

#     def run(self):
#         self.app = wx.App()
#         self.frame = SLMframe(self.monitor)
#         self.frame.Show(True)
#         logger.info('----------Main app start!-----------')
#         self.app.MainLoop()

#     def refresh(self,new_ell):
#         self.frame.Window.img = LGhologram(new_ell, self.frame.Window.res[0], self.frame.Window.res[1]).img
#         # print(self.frame.Window.img)
#         event = ImageEvent()
#         # self.frame.Window.ProcessEvent(event)
#         wx.PostEvent(self.frame, event)             # 线程间通信，重要！！！！！
#         # event.img = img
#         # print(event.img)
        
#         # print(self.frame.Window.img)
#         # self.frame.Window.refreshWindow()

#         # self.frame.Refresh()

class  SLMdisplay:
    def __init__(self,
                 monitor_num = 1
                 ):
        self.monitor_num = monitor_num
        self.display_thread = threading.Thread(target=self.slmrun, name='SLMdisplay')
        # print(self.display_thread._name)
        # self.display_thread.daemon = True
        self.display_thread.start()
        time.sleep(2)
        logger.warning('----------------SLMdisplay initializes fishing!----------------')
        

    def slmrun(self):
        self.app = wx.App()
        self.frame = {}
        for i in range(1,self.monitor_num):
            logger.info('----------SLM_{} display!-----------'.format(i))
            # self.frame.append(SLMframe(i))
            self.frame[i] = SLMframe(i)
            self.frame[i].ShowFullScreen(True, wx.FULLSCREEN_ALL)
            

        logger.info('----------Main app start!-----------')
        self.app.MainLoop()

    def refresh(self,which_frame, wbais, hbais, new_ell):
        res = self.inputLexAnalysis(new_ell)
        if res == 1 or res == 2:    # input is a .jpg image
            _pic = wx.Image(new_ell, wx.BITMAP_TYPE_PNG).ConvertToBitmap()

        elif res == 3:       # input os a single state
            _pic = LGhologram(new_ell, self.frame[which_frame].Window.res[0], self.frame[which_frame].Window.res[1], wbais, hbais).img

        elif res == 4:  # input is a superposition 
            # inputStructure: {'Amp'  : [1,2,3,4],
            #                  'Pha'  : [0,PI,PI/2,-1], 
            #                  'Topo' : [1,2,3,4]
            #                 }

            _pic = Superhologram(new_ell,self.frame[which_frame].Window.res[0], self.frame[which_frame].Window.res[1], wbais, hbais).img

            # sys.exit(1)

        


        self.frame[which_frame].Window.img = _pic
        # print(self.frame.Window.img)
        event = ImageEvent()
        event.img = _pic
        # self.frame.Window.ProcessEvent(event)
        wx.PostEvent(self.frame[which_frame], event)             # 线程间通信，重要！！！！！
        # self.frame[which_frame].AddPendingEvent(event)
        
        # event.img = img
        # print(event.img)
        
        # print(self.frame.Window.img)
        # self.frame.Window.refreshWindow()

        # self.frame.Refresh()

    def inputLexAnalysis(self, input):
        if isinstance(input, str):
            if input[-4:] == '.jpg':
                return 1
            elif input[-4:] == '.png':
                return 2
            else:
                logger.error('----------input:{} not defined, please check!-----------'.format(input))
                return 

        if isinstance(input, int):
            return 3
        
        if isinstance(input, dict):     # inputStructure: {'Amp'  : [1,2,3,4],
                                        #                  'Pha'  : [0,PI,PI/2,-1]
                                        #                  'Topo' : [1,2,3,4]       
                                        #                 }
            return 4
        
        # isinstance(input, list)
        # isinstance(input, float)
        # pass

if __name__ == '__main__':
    # a = SLMdisplay(0)
    # b = SLMdisplay(0)
    # time.sleep(1)
    # start_time = datetime.datetime.now()
    # logger.info('----------Program start!-----------')
    # a.refresh(1)
    # time.sleep(5)
    # b.refresh(2)
    # logger.info('----------Main thread have finished!-----------')
    # end_time = datetime.datetime.now()
    # print(end_time - start_time)
    # # a.frame.Quit()
    # # SLMdisplay(0)
    SLM = SLMdisplay(1)
    time.sleep(1)
    start_time = datetime.datetime.now()
    a = {'Amp':[1,2,3,4],'Pha':[PI,-PI,PI/2,0],'Topo':[1,2,3,4]}
    b = {'Amp':[2],'Pha':[0],'Topo':[1]}
    # b = {'Amp':[1,1],'Pha':[0,0],'Topo':[-1,1]}
    print(type(a))
    print(isinstance(a, dict))
    
    WBAIS = 0
    HBAIS = 0
    
    SLM.refresh(0, WBAIS, HBAIS, b)
    # for i in range(20):
    #     SLM.refresh(0,'E:\\anmin\\slm\\try.png')
    #     time.sleep(0.01)
        # _time = datetime.datetime.now()
        # print(_time - start_time)
    
    
    end_time = datetime.datetime.now()
    print(end_time - start_time)



    # SLM.refresh(1,2)
    # SLM.refresh(2,3)

    # str1 = "1234.jpg"
    # print()
    # if str1[-4:]=="ajpg" or str1[-4:]==".jpg":
    #     print(1111)