# -*- coding:Utf-8 -*-
import doctest
import os
import logging
import pdb
import sys
import numpy as np
import scipy as sp
import scipy.io as io
import scipy.signal as si
import scipy.linalg as la
import matplotlib.pylab as plt
import pylayers.signal.bsignal as bs
from pylayers.measures import mesuwb

class Waveform(dict):
    """

    Attributes
    ----------

    st  : time domain
    sf  : frequency domain
    sfg : frequency domain integrated

    Methods
    -------

    eval
    showpsd
    ip_generic
    fromfile
    fromfile2
    read
    gui
    show

    """
    def __init__(self,**kwargs):
        """

        Parameters
        ----------

        'typ' : string
            'generic',
         'WGHz': float
            0.499
         'fcGHz': float
            4.493
         'fsGHz': float
            100,
         'threshdB':
              3,
         'twns': float
            30

        typ  :  'generic','W1compensate','W1offset'

        """
        defaults = {'typ':'generic',
                'fGHz':[],
                'WGHz': 0.499,
                'fcGHz': 4.493,
                'fsGHz': 100,
                'threshdB': 3,
                'twns': 30}

        for key, value in defaults.items():
            if key not in kwargs:
                self[key] = value
            else:
                self[key] = kwargs[key]
        self.eval()

    def eval(self):
        u""" evaluate waveform

        The :math:`\lambda/4*\pi` factor which is necessary to get the proper budget
        link ( from the Friis formula) is introduced in this function.

        """

        if self['typ']  == 'generic':
            [st,sf]=self.ip_generic()
        #elif self['typ']  == 'mbofdm':
        #    [st,sf]=self.mbofdm()
        elif self['typ'] == 'W1compensate':
            [st,sf]=self.fromfile()
        elif self['typ'] == 'W1offset':
            [st,sf]=self.fromfile2()
        elif self['typ'] == 'blackmann':
            sf = bs.FUsignal(x=fGHz,y=np.blackman(len(fGHz)))
            st = sf.ift()
        elif self['typ'] == 'rect':
            sf = bs.FUsignal(x=fGHz,y=np.ones(len(fGHz)))
            st = sf.ift()
        elif self['typ'] == 'hamming':
            sf = bs.FUsignal(x=fGHz,y=np.hamming(len(fGHz)))
            st = sf.ift()
        elif self['typ'] == 'ref156':
            [st,sf] = self.ref156()
        else:
            logging.critical('waveform typ not recognized, check your config \
                             file')

        self.st       = st
        self.sf       = sf
        self.fGHz     = self.sf.x

        ygamma        = -1j*0.3/(4*np.pi*self.fGHz)
        self.gamm     = bs.FUsignal(x=self.fGHz,y=ygamma)
        self.sfg      = self.sf*self.gamm
        self.sfgh     = self.sfg.symH(0)
        self.stgh     = self.sfgh.ifft(1)

    def info(self):
        """  display information about waveform

        Results
        -------

        >>> from pylayers.signal.waveform import *
        >>> w = Waveform(typ='generic',WGHz=0.499,fcGHz=4.49,fsGHz=100,threshdB=3,twns=30)
        >>> w.show()
        >>> plt.show()


        """
        if self['typ']=='generic':
            for k in self.keys():
                print(k , " : ",self[k])
        else:
            print("typ:",self['typ'])


    def showpsd(self,Tpns=1000):
        """ show psd

        Parameters
        ----------

        Tpns : float

        """
        plt.subplot(211)
        self.st.plot()
        plt.subplot(212)
        psd = self.st.psd(Tpns,50)
        plt.title('Tp = '+str(Tpns)+' ns')
        psd.plotdB(mask=True)

    def ip_generic(self):
        """ Create an energy normalized Gaussian impulse (Usignal)

        ip_generic(self,parameters)


        """
        Tw = self['twns']
        fcGHz = self['fcGHz']
        WGHz = self['WGHz']
        thresh = self['threshdB']
        fsGHz = self['fsGHz']
        ts = 1.0/fsGHz

        self['ts'] = ts
        Np = fsGHz*Tw
        self['Np'] = Np
        #x = np.linspace(-0.5*Tw+ts/2,0.5*Tw+ts/2,Np,endpoint=False)
        #x = arange(-Tw,Tw,ts)
        w = bs.TUsignal()
        w.EnImpulse(fcGHz=fcGHz,WGHz=WGHz,threshdB=thresh,fsGHz=fsGHz)
        #W = w.ft()
        W = w.ft()
        return (w,W)

    def ref156(self,beta=0.5):
        """ reference pulse of IEEE 802.15.6 UWB standard

        Parameters
        ----------

        beta : float
            roll-off factor
        Tns = 1/499.2MHz

        Notes
        -----

        From P8O2.15.6/D02 December 2010  Formula 96 p 215

        """
        Tw = self['twns']
        fs = self['fsGHz']
        Np = Tw*fs
        Ts = 1./fs
        beta = 0.5
        Tns = 1./0.4992
        x = np.linspace(-0.5*Tw+Ts/2, 0.5*Tw+Ts/2, Np, endpoint=False)
        z = x/Tns
        t1 = np.sin(np.pi*(1-beta)*z)
        t2 = np.cos(np.pi*(1+beta)*z)
        t3 = (np.pi*z)*(1-(4*beta*z)**2)
        y = (t1 + 4*beta*z*t2)/t3

        st = bs.TUsignal()
        st.x = x
        st.y = y[None,:]
        sf = st.ftshift()

        return(st,sf)


    def fromfile(self):
        """ get the measurement waveform from WHERE1 measurement campaign

        This function is not yet generic

        >>> from pylayers.signal.waveform import *
        >>> wav = Waveform(typ='W1compensate')
        >>> wav.show()

        """

        M = mesuwb.UWBMeasure(1,h=1)
        w = bs.TUsignal()

        ts = M.RAW_DATA.timetx[0]
        tns = ts*1e9
        ts = tns[1]-tns[0]

        y  = M.RAW_DATA.tx[0]

        # find peak position  u is the index of the peak
        # yap :after peak
        # ybp : before peak
        # yzp : zero padding
        maxy = max(y)
        u = np.where(y ==maxy)[0][0]
        yap = y[u:]
        ybp = y[0:u]

        yzp = np.zeros(len(yap)-len(ybp)-1)

        tnsp = np.arange(0, tns[-1]-tns[u]+0.5*ts, ts)
        tnsm = np.arange(-(tns[-1]-tns[u]), 0, ts)

        y = np.hstack((yzp, np.hstack((ybp, yap))))
        tns = np.hstack((tnsm, tnsp))

        #
        # Warning (check if 1/sqrt(30) is not applied elsewhere
        #
        w.x = tns
        w.y = y[None,:]*(1/np.sqrt(30))

        #  w : TUsignal
        #  W : FUsignal (Hermitian redundancy removed)

        W   = w.ftshift()
        return (w,W)

    def fromfile2(self):
        """
        get the measurement waveform from WHERE1 measurement campaign

        This function is not yet generic

        >>> from pylayers.signal.waveform import *
        >>> wav = Waveform(typ='W1offset')
        >>> wav.show()

        """
        M = mesuwb.UWBMeasure(1,1)
        w = bs.TUsignal()

        ts = M.RAW_DATA.timetx[0]
        tns = ts*1e9
        Ts = tns[1]-tns[0]

        y  = M.RAW_DATA.tx[0]

        # find peak position  u is the index of the peak
        # yap :after peak
        # ybp : before peak
        # yzp : zero padding
#        maxy = max(y)
#        u = np.where(y ==maxy)[0][0]
#        yap = y[u:]
#        ybp = y[0:u]

        yzp = np.zeros(len(y)-1)

#        tnsp = np.arange(0,tns[-1]-tns[u]+0.5*ts,ts)
#        tnsm = np.arange(-(tns[-1]-tns[u]),0,ts)
        N = len(ts)-1
        tnsm = np.linspace(-tns[-1],-Ts,N)
        y = np.hstack((yzp,y))
        tns = np.hstack((tnsm,tns))

        #
        # Warning (check if 1/sqrt(30) is not applied elsewhere
        #
        w.x = tns
        w.y = (y*(1/np.sqrt(30)))[None,:]

        #  w : TUsignal
        #  W : FUsignal (Hermitian redundancy removed)
        W   = w.ftshift()
        return (w,W)


    def read(self,config):
        """
        Parameters
        ----------

        config : ConfigParser object

        Returns
        -------
        w      : waveform

        """

        par = config.items("waveform")
        for k in range(len(par)):
            key = par[k][0]
            val = par[k][1]
            if key == "WGHz":
                self[key] = float(val)
            if key == "fcGHz":
                self[key] = float(val)
            if key == "feGHz":
                self[key] = float(val)
            if key == "threshdB":
                self[key] = float(val)
            if key == "twns":
                self[key] = float(val)
            if key == "typ":
                self[key] = val

        self.eval()

    def bandwidth(self,th_ratio=10000,Npt=100):
        """ Determine effective bandwidth of the waveform.

        Parameters
        ----------

        th_ratio : float
            threshold ratio
            threshold = max(abs())/th_ratio
        Npt : Number of points

        """
        u=np.where(np.abs(self.sf.y)>np.max(np.abs(self.sf.y))/th_ratio)
        #fGHz = self.sf.x[u[1]]
        fGHz_start = self.sf.x[u[1]][0]
        fGHz_stop = self.sf.x[u[1]][-1]
        fGHz = np.linspace(fGHz_start,fGHz_stop,Npt)
        return fGHz

    def gui(self):
        """
        Get the Waveform parameter
        """
        if self['typ'] == 'generic':
            self.st.plot()
            show()
            wavegui = multenterbox('','Waveform Parameter',
            ('Tw (ns) integer value',
             'fc (GHz)',
             'W (GHz)',
             'thresh (dB)',
             'fs (GHz) integer value'),
            ( self['twns'] ,
            self['fcGHz'] ,
            self['WGHz'] ,
            self['threshdB'],
            self['feGHz']
            ))

            self.parameters['Twns']    = eval(wavegui[0])
            self.parameters['fcGHz']    = eval(wavegui[1])
            self.parameters['WGHz']  = eval(wavegui[2])
            self.parameters['threshdB'] = eval(wavegui[3])
            self.parameters['fsGHz']    = eval(wavegui[4])

            [st,sf]       = self.ip_generic()
            self.st       = st
            self.sf       = sf
            st.plot()
            show()

    def show(self,fig=[]):
        """ show waveform in time and frequency domain

        Parameters
        ----------

        fig : figure

        """
        # title construction
        if fig ==[]:
            fig = plt.figure()
        title =''
        for pk in self.keys():
            val   = self[pk]
            title = title + pk + ': '
            if type(val) != 'str':
                title = title + str(val) + ' '
        #plt.title(title)
        ax1 = fig.add_subplot(2,1,1)
        ax1.plot(self.st.x,self.st.y[0,:])
        plt.xlabel('time (ns)')
        plt.ylabel('level in linear scale')
        ax2 = fig.add_subplot(2,1,2)
        ax2.plot(self.sf.x,abs(self.sf.y[0,:]))
        plt.xlabel('frequency (GHz)')
        plt.ylabel('level in linear scale')
        fig.suptitle(title)


if __name__ == "__main__":
    plt.ion()
    doctest.testmod()
