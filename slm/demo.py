#!/usr/bin/python

import wx
from log_sys import *
import numpy as np
import matplotlib.pyplot as plt
import math
import time
import threading
w = 1920
h = 1080

app = wx.App()
frame = wx.Frame(None, -1, 'SLM_1')     # SetDimensions(x, y, width, height, sizeFlags=wx.SIZE_AUTO)
frame.SetDimensions(0,0,w,h)
logger.info('show the first frame!')

# TODO: compute the phase hologram
phase_hologram = np.random.randint(0,256,(308,920,1))

xCenter = int(w/2)
yCenter = int(h/2)
pixelPitch = 8e-6   # active area: 15.36mm x 8.64mm
beamWaist = 3e-3    # radius of the beam
waveLength = 810e-9
blaze = 1e-6        # grating period

x = np.linspace(0, w, w)*pixelPitch
y = np.linspace(0, h, h)*pixelPitch
X, Y = np.meshgrid(x,y)

X = X - xCenter*pixelPitch
Y = Y - yCenter*pixelPitch
print(X)
print(np.arctan2(1,0))

r = np.sqrt(X**2 + Y**2)
theta = np.arctan2(Y,X)
print(r.shape)

# TODO: compute the LG mode:
def lgMode(l,
           r,
           theta,
           omega0 = beamWaist):
    constantParameter = math.sqrt(1/math.pi/math.factorial(abs(l)))/omega0
    firstTerm = ((np.sqrt(2)*r/omega0)**abs(l))
    secondTerm = np.exp(-r**2/omega0**2)*np.exp(1j*l*theta)
    return  constantParameter*firstTerm*secondTerm
    

# print(phase_hologram)
# print(phase_hologram.shape)
# print(len(phase_hologram.shape))
# phase_hologram[:,:] = (0,0,0)

# TODO: convert the phase hologram to 8-bit image; use ConvertToBitmap() to convert the image to bitmap
# img = wx.Image(920, 308)
# print(phase_hologram.tobytes())

# img.SetData(phase_hologram.tobytes())
# wxBitmap = img.ConvertToBitmap()
ll = 1
amplitude = lgMode(ll,r,theta)
intensity = amplitude*amplitude.conjugate()
bw_array = amplitude/math.sqrt(sum(sum(intensity)))

# fig = plt.figure()
# ax = plt.axes(projection='3d')
# ax.plot3D(X,Y,bw_array)
# plt.show()
# plt.imshow(abs(bw_array))
print(sum(sum(bw_array)))



# TODO: compute the hologram
lgAbs = abs(bw_array)
lgAngle = np.angle(bw_array)
# plt.imshow(lgAbs)

def sinc(x):
    if x == 0:
        return 1
    else:
        return np.sin(x)/x
def asinc(y):
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
sincInverse = np.zeros((h,w), dtype = "float64")   
sincInverse = asinc(lgAbs)
# for ii in range(0, h):
#     for jj in range(0, w):
#         # sincInverse[ii,jj] = root(lambda x: np.sin(x)/x-lgAbs[ii,jj], 0.5)
#         res = root(lambda x: np.sin(x)/x-lgAbs[ii,jj], -1.57)
#         assert(res.fun[0] < 1e-3)
#         # print(res.x[0])
#         # print(res)
#         # print(type(res))
#         # print('-----------------------------------')
#         sincInverse[ii,jj] = res.x[0]

M = 1 - 1/math.pi * sincInverse         # need a extra minus sign
F = lgAngle - math.pi * M
mod = (F+2*math.pi*X/blaze)%(2*math.pi)

T = np.exp(1j*M*mod)
print(T)
bw_array = np.angle(T)

def mat2gray8bit(inputData):
    maxD = np.max(inputData)
    minD = np.min(inputData)
    inputData = (inputData - minD)/(maxD - minD)*255
    return np.around(inputData).astype('uint8')

bw_array = mat2gray8bit(bw_array)
print(bw_array)
plt.imshow(bw_array)
bw_array.shape = h, w, 1
# print(bw_array.shape)
# bw_array.shape = h, w, 1
# print((bw_array,bw_array,bw_array))
# logger.info('{}'.format((bw_array,bw_array,bw_array)))

# r = np.random.randint(0,256,(308,920,1))
# g = np.random.randint(0,256,(308,920,1))
# b = np.random.randint(0,256,(308,920,1))

# gg = np.zeros((308,920,1), dtype = "uint8")
# bb = np.zeros((308,920,1), dtype = "uint8")

# color_array = np.concatenate((r,g,b), axis=2)

# color_array = np.concatenate((r,r,r), axis=2)

# color_array = np.concatenate((bw_array,bw_array,bw_array), axis=2)
# data = color_array.tostring()

color_array = np.concatenate((bw_array,bw_array,bw_array), axis=2)
data = color_array.tobytes()
img = wx.ImageFromBuffer(w, h, dataBuffer=data)

# TODO: show the image on the frame
panel = wx.Panel(frame,-1)
wx.StaticBitmap(panel, -1, img, pos=(0, 0))

frame.Show()

frame2 = wx.Frame(None, -1, 'SLM_2')
frame2.SetDimensions(800,500,w,h)

# gray_array = np.zeros((1,308*920), dtype = "uint8")

color_array_2 = np.concatenate((bw_array,bw_array,bw_array), axis=2)
data_2 = color_array_2.tobytes()
img2 = wx.ImageFromBuffer(w, h, dataBuffer=data_2)
# img2 = wx.ImageFromBuffer(width=920, height=308, dataBuffer=data2)

# logger.error('{}'.format(len(gray_array)))

logger.info('show the first frame_2!')
panel2 = wx.Panel(frame2,-1)
wx.StaticBitmap(panel2, -1, img2, pos=(0, 0))

frame2.Show()
re = wx.Display.GetCount()
x0, y0, resX, resY = wx.Display(0).GetGeometry()
print(wx.Display(0).GetGeometry())
time.sleep(1)

# plt.show()
print(re)
def refreshHologram():
    time.sleep(5) 
    print('------------------------')
    # frame2.Hide()
    panel3 = wx.Panel(frame2,-1)
    wx.StaticBitmap(panel3, -1, img2, pos=(100,100))
    frame2.Show()
    return 0
thread = threading.Thread(target=refreshHologram)
# thread.daemon = True
thread.start()

app.MainLoop()
# time.sleep(5)
# wx.StaticBitmap(panel2, -1, img2, pos=(100,100))


