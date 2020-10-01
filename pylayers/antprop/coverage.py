"""
.. currentmodule:: pylayers.antprop.coverage

.. autosummary::
   :members:

"""
from pylayers.util.project import *
#from pylayers.measures.mesuwb import *
from pylayers.simul.radionode import *
import pylayers.util.pyutil as pyu
from pylayers.util.utilnet import str2bool
from pylayers.gis.layout import Layout
import pylayers.antprop.loss as loss
import pylayers.gis.ezone as ez
import pylayers.signal.standard as std

import matplotlib.cm  as cm
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as m
from mpl_toolkits.axes_grid1 import make_axes_locatable

if sys.version_info.major==2:
    import ConfigParser
else:
    import configparser as ConfigParser

import pdb
import doctest
from itertools import product

try:
    from mayavi import mlab
    from tvtk.tools import visual
except:
    print('mayavi not installed')


class Coverage(PyLayers):
    """ Handle Layout Coverage

        Methods
        -------

        creategrid()
            create a uniform grid for evaluating losses
        cover()
            run the coverage calculation
        showPower()
            display the map of received power
        showLoss()
            display the map of losses


        Attributes
        ----------

        All attributes are read from fileini ino the ini directory of the
        current project

        _fileini
            default coverage.ini

        L     : a Layout
        nx    : number of point on x
        ny    : number of point on y
        tx    : transmitter position
        txpe  : transmitter power emmission level
        show  : boolean for automatic display power map
        na : number of access point

    """


    def __init__(self,_fileini='coverage.ini'):
        """ object constructor

        Parameters
        ----------

        _fileini : string
            name of the configuration file

        Notes
        -----

        Coverage is described in an ini file.
        Default file is coverage.ini and is placed in the ini directory of the current project.

        """


        self.config = ConfigParser.ConfigParser(allow_no_value=True)
        self.config.read(pyu.getlong(_fileini,pstruc['DIRSIMUL']))

        # section layout
        self.layoutopt = dict(self.config.items('layout'))
        # section sector
        self.gridopt   = dict(self.config.items('grid'))
        # section ap (access point)
        self.apopt     = dict(self.config.items('ap'))
        # section receiver  parameters
        self.rxopt     = dict(self.config.items('rx'))
        # section receiver  parameters
        self.showopt   = dict(self.config.items('show'))

        # get the Layout
        filename = self.layoutopt['filename']
        if filename.endswith('lay'):
            self.typ = 'indoor'
            self.L = Layout(filename)

            # get the receiving grid
            self.nx = eval(self.gridopt['nx'])
            self.ny = eval(self.gridopt['ny'])
            if 'zgrid' in self.gridopt:
                self.zgrid = eval(self.gridopt['zgrid'])
            else:
                self.zgrid = 1.0
            self.mode = self.gridopt['mode']
            assert self.mode in ['file','full','zone'], "Error reading grid mode "
            self.boundary = eval(self.gridopt['boundary'])
            self.filespa = self.gridopt['file']
            #
            # create grid
            #
            self.creategrid(mode=self.mode, boundary=self.boundary, _fileini=self.filespa)

            self.dap = {}
            for k in self.apopt:
                kwargs  = eval(self.apopt[k])
                ap = std.AP(**kwargs)
                self.dap[eval(k)] = ap
            try:
                self.L.Gt.nodes()
            except:
                pass
            try:
                self.L.dumpr()
            except:
                self.L.build()
                self.L.dumpw()

        else:
            self.typ='outdoor'
            self.E = ez.Ezone(filename)
            self.E.loadh5()
            self.E.rebase()

        # The frequency is fixed from the AP nature
        self.fGHz = np.array([])
        #self.fGHz = eval(self.txopt['fghz'])
        #self.tx = np.array((eval(self.txopt['x']),eval(self.txopt['y'])))
        #self.ptdbm = eval(self.txopt['ptdbm'])
        #self.framelengthbytes = eval(self.txopt['framelengthbytes'])

        # receiver section
        #self.rxsens = eval(self.rxopt['sensitivity'])

        self.temperaturek  = eval(self.rxopt['temperaturek'])
        self.noisefactordb = eval(self.rxopt['noisefactordb'])

        # show section
        self.bshow = str2bool(self.showopt['show'])

        self.sinr = False
        self.snr = False
        self.best = False
        self.egd = False
        self.Pr = False
        self.capacity = False
        self.pr = False
        self.loss = False

    def __repr__(self):
        st=''
        if self.typ=='indoor':
            st = st+ 'Layout file : '+self.L._filename + '\n\n'
            st = st + '-----list of Access Points ------'+'\n'
            for k in self.dap:
                st = st + self.dap[k].__repr__()+'\n'
            st = st + '-----Rx------'+'\n'
            st= st+ 'temperature (K) : '+ str(self.temperaturek) + '\n'
            st= st+ 'noisefactor (dB) : '+ str(self.noisefactordb) + '\n\n'
            st = st + '--- Grid ----'+'\n'
            st= st+ 'mode : ' + str(self.mode) + '\n'
            if self.mode!='file':
                st= st+ 'nx : ' + str(self.nx) + '\n'
                st= st+ 'ny : ' + str(self.ny) + '\n'
            if self.mode=='zone':
                st= st+ 'boundary (xmin,ymin,xmax,ymax) : ' + str(self.boundary) + '\n\n'
            if self.mode=='file':
                st = st+' filename : '+self.filespa+'\n'
        return(st)

    def creategrid(self,mode='full',boundary=[],_fileini=''):
        """ create a grid

        Parameters
        ----------

        full : boolean
            default (True) use all the layout area
        boundary : (xmin,ymin,xmax,ymax)
            if full is False the boundary argument is used

        """

        if mode=="file":
            self.RN = RadioNode(name='',
                               typ='rx',
                               _fileini = _fileini,
                               _fileant = 'def.vsh3')
            self.grid =self.RN.position[0:2,:].T
        else:
            if mode=="full":
                mi=np.min(np.array(list(self.L.Gs.pos.values())),axis=0)+0.01
                ma=np.max(np.array(list(self.L.Gs.pos.values())),axis=0)-0.01
            if mode=="zone":
                assert boundary!=[]
                mi = np.array([boundary[0],boundary[1]])
                ma = np.array([boundary[2],boundary[3]])

            x = np.linspace(mi[0],ma[0],self.nx)
            y = np.linspace(mi[1],ma[1],self.ny)

            self.grid=np.array((list(np.broadcast(*np.ix_(x, y)))))

        self.ng = self.grid.shape[0]

    def where1(self):
        """
        Unfinished : Not sure this is the right place (too specific)
        """
        M1 = UWBMeasure(1)
        self.dap={}
        self.dap[1]={}
        self.dap[2]={}
        self.dap[3]={}
        self.dap[4]={}
        self.dap[1]['p']=M1.rx[1,0:2]
        self.dap[2]['p']=M1.rx[1,0:2]
        self.dap[3]['p']=M1.rx[1,0:2]
        self.dap[4]['p']=M1.rx[1,0:2]
        for k in range(300):
            try:
                M = UWBMeasure(k)
                tx = M.tx
                self.grid=np.vstack((self.grid,tx[0:2]))
                D  = M.rx-tx[np.newaxis,:]
                D2 = D*D
                dist = np.sqrt(np.sum(D2,axis=1))[1:]
                Emax = M.Emax()
                Etot = M.Etot()[0]
                try:
                    td1 = np.hstack((td1,dist[0]))
                    td2 = np.hstack((td2,dist[1]))
                    td3 = np.hstack((td3,dist[2]))
                    td4 = np.hstack((td4,dist[3]))
                    te1 = np.hstack((te1,Emax[0]))
                    te2 = np.hstack((te2,Emax[1]))
                    te3 = np.hstack((te3,Emax[2]))
                    te4 = np.hstack((te4,Emax[3]))
                    tt1 = np.hstack((tt1,Etot[0]))
                    tt2 = np.hstack((tt2,Etot[1]))
                    tt3 = np.hstack((tt3,Etot[2]))
                    tt4 = np.hstack((tt4,Etot[3]))
                    #tdist = np.hstack((tdist,dist))
                    #te = np.hstack((te,Emax))
                except:
                    td1=np.array(dist[0])
                    td2=np.array(dist[1])
                    td3=np.array(dist[2])
                    td4=np.array(dist[3])
                    te1 =np.array(Emax[0])
                    te2 =np.array(Emax[1])
                    te3 =np.array(Emax[2])
                    te4 =np.array(Emax[3])
                    tt1 =np.array(Etot[0])
                    tt2 =np.array(Etot[1])
                    tt3 =np.array(Etot[2])
                    tt4 =np.array(Etot[3])
            except:
                pass

    def cover(self, **kwargs):
        """ run the coverage calculation

        Parameters
        ----------

        sinr : boolean
        snr  : boolean
        best : boolean
        size : integer 
            size of grid points block

        Examples
        --------

        .. plot::
            :include-source:

            >>> from pylayers.antprop.coverage import *
            >>> C = Coverage()
            >>> C.cover()
            >>> f,a = C.show(typ='sinr',figsize=(10,8))
            >>> plt.show()

        Notes
        -----

        self.fGHz is an array, it means that Coverage is calculated at once
        for a whole set of frequencies. In practice, it would be the center
        frequency of a given standard channel.

        This function is calling `loss.Losst` which calculates Losses along a
        straight path.

        In a future implementation we will
        abstract the EM solver in order to make use of other calculation
        approaches as a full or partial Ray Tracing.

        The following members variables are evaluated :

        + freespace Loss @ fGHz   PL()  PathLoss (shoud be rename FS as free space) $
        + prdbmo : Received power in dBm .. math:`P_{rdBm} =P_{tdBm} - L_{odB}`
        + prdbmp : Received power in dBm .. math:`P_{rdBm} =P_{tdBm} - L_{pdB}`
        + snro : SNR polar o (H)
        + snrp : SNR polar p (H)

        See Also
        --------

        pylayers.antprop.loss.Losst
        pylayers.antprop.loss.PL

        """

        sizebloc = kwargs.pop('size',100)

        #
        # select active AP
        #
        lactiveAP = []

        try:
            del self.aap
            del self.ptdbm
        except:
            pass


        # Boltzmann constant
        kB = 1.3806503e-23

        #
        # Loop over access points
        #    set parameter of each active ap
        #        p
        #        PtdBm
        #        BMHz

        for iap in self.dap:
            if self.dap[iap]['on']:
                lactiveAP.append(iap)
                # set frequency for each AP
                fGHz = self.dap[iap].s.fcghz
                self.fGHz=np.unique(np.hstack((self.fGHz,fGHz)))
                apchan = self.dap[iap]['chan']
                #
                # stacking  AP position Power Bandwidth
                #
                try:
                    self.aap   = np.vstack((self.aap,self.dap[iap]['p']))
                    self.ptdbm = np.vstack((self.ptdbm,self.dap[iap]['PtdBm']))
                    self.bmhz  = np.vstack((self.bmhz,self.dap[iap].s.chan[apchan[0]]['BMHz']))
                except:
                    self.aap   = self.dap[iap]['p']
                    self.ptdbm = np.array(self.dap[iap]['PtdBm'])
                    self.bmhz  = np.array(self.dap[iap].s.chan[apchan[0]]['BMHz'])

        self.nf = len(self.fGHz)
        PnW = np.array((10**(self.noisefactordb/10.))*kB*self.temperaturek*self.bmhz*1e6)
        # Evaluate Noise Power (in dBm)

        self.pndbm = np.array(10*np.log10(PnW) + 30)

        #lchan = map(lambda x: self.dap[x]['chan'],lap)
        #apchan = zip(self.dap.keys(),lchan)
        #self.bmhz = np.array(map(lambda x: self.dap[x[0]].s.chan[x[1][0]]['BMHz']*len(x[1]),apchan))

        self.ptdbm = self.ptdbm.T
        self.pndbm = self.pndbm.T
        # creating all links
        # from all grid point to all ap
        #

        if len(self.pndbm.shape ) == 0:
            self.ptdbm = self.ptdbm.reshape(1,1)
            self.pndbm = self.pndbm.reshape(1,1)

        self.nf = len(self.fGHz)
        Nbloc = self.ng//sizebloc

        r1 = np.arange(0,(Nbloc+1)*sizebloc,sizebloc)
        if self.ng != r1[-1]:
            r1 = np.append(r1,self.ng)
        lblock = list(zip(r1[0:-1],r1[1:]))

        for bg in lblock:
            p = product(range(bg[0],bg[1]),lactiveAP)
            #
            # pa : access point ,3
            # pg : grid point ,2
            #
            # 1 x na

            for k in p:
                pg = self.grid[k[0],:]
                pa = np.array(self.dap[k[1]]['p'])
                # exemple with 3 AP
                # 321 0
                # 321 1
                # 321 2
                # 322 0
                try:
                    self.pa = np.vstack((self.pa,pa))
                except:
                    self.pa = pa
                try:
                    self.pg = np.vstack((self.pg,pg))
                except:
                    self.pg = pg

            self.pa = self.pa.T
            shpa = self.pa.shape
            shpg = self.pg.shape

            # extend in 3 dimensions if necessary

            if shpa[0] != 3:
                self.pa = np.vstack((self.pa,np.ones(shpa[1])))

            self.pg = self.pg.T
            self.pg = np.vstack((self.pg,self.zgrid*np.ones(shpg[0])))

            # retrieving dimensions along the 3 axis
            # a : number of active access points
            # g : grid block
            # f : frequency

            na = len(lactiveAP)
            self.na = na
            ng = self.ng
            nf = self.nf

            # calculate antenna gain from ap to grid point
            #
            # loop over all AP
            #
            k = 0
            for iap in self.dap:
                # select only one access point
                # n
                u = na*np.arange(0,bg[1]-bg[0],1).astype('int')+k
                if self.dap[iap]['on']:
                    pa = self.pa[:,u]
                    pg = self.pg[:,u]
                    azoffset = self.dap[iap]['phideg']*np.pi/180.
                    # the eval function of antenna should also specify polar
                    self.dap[iap].A.eval(fGHz=self.fGHz, pt=pa, pr=pg, azoffset=azoffset)
                    gain = (self.dap[iap].A.G).T
                    # to handle omnidirectional antenna (nf,1,1)
                    if gain.shape[1]==1:
                        gain = np.repeat(gain,bg[1]-bg[0],axis=1)
                    if k==0:
                        tgain = gain[:,:,None]
                    else:
                        tgain = np.dstack((tgain,gain[:,:,None]))
                    k = k+1

            tgain = tgain.reshape(nf,tgain.shape[1]*tgain.shape[2])
            Lwo,Lwp,Edo,Edp = loss.Losst(self.L, self.fGHz, self.pa, self.pg, dB=False)
            logger.info('Lwo[0][0] %.2f' % Lwo[0,0])
            freespace = loss.PL(self.fGHz, self.pa, self.pg, dB=False)
            try:
                self.Lwo = np.hstack((self.Lwo,Lwo))
                self.Lwp = np.hstack((self.Lwp,Lwp))
                self.Edo = np.hstack((self.Edo,Edo))
                self.Edp = np.hstack((self.Edp,Edp))
                self.freespace = np.hstack((self.freespace,freespace))
                self.tgain = np.hstack((self.tgain,tgain))
            except:
                self.Lwo = Lwo
                self.Lwp = Lwp
                self.Edo = Edo
                self.Edp = Edp
                self.freespace = freespace
                self.tgain = tgain


        self.Lwo = self.Lwo.reshape(nf,ng,na)
        self.Edo = self.Edo.reshape(nf,ng,na)
        self.Lwp = self.Lwp.reshape(nf,ng,na)
        self.Edp = self.Edp.reshape(nf,ng,na)
        self.tgain = self.tgain.reshape(nf,ng,na)

        self.freespace = self.freespace.reshape(nf,ng,na)

        # transmitting power
        # f x g x a

        # CmW : Received Power coverage in mW
        # TODO : tgain in o and p polarization
        self.CmWo = 10**(self.ptdbm[np.newaxis,...]/10.)*self.Lwo*self.freespace*self.tgain
        self.CmWp = 10**(self.ptdbm[np.newaxis,...]/10.)*self.Lwp*self.freespace*self.tgain
        #self.CmWo = 10**(self.ptdbm[np.newaxis,...]/10.)*self.Lwo*self.freespace
        #self.CmWp = 10**(self.ptdbm[np.newaxis,...]/10.)*self.Lwp*self.freespace


        if self.snr:
            self.evsnr()
        if self.sinr:
            self.evsinr()
        if self.best:
            self.evbestsv()

    def evsnr(self):
        """ calculates signal to noise ratio
        """

        NmW = 10**(self.pndbm/10.)[np.newaxis,:]

        self.snro = self.CmWo/NmW
        self.snrp = self.CmWp/NmW
        self.snr = True

    def evsinr(self):
        """ calculates sinr

        """

        # na : number of access point
        na = self.na

        # U : 1 x 1 x na x na
        U = (np.ones((na,na))-np.eye(na))[np.newaxis,np.newaxis,:,:]

        # CmWo : received power in mW orthogonal polarization
        # CmWp : received power in mW parallel polarization

        ImWo = np.einsum('ijkl,ijl->ijk',U,self.CmWo)
        ImWp = np.einsum('ijkl,ijl->ijk',U,self.CmWp)


        NmW = 10**(self.pndbm/10.)[np.newaxis,:]

        self.sinro = self.CmWo/(ImWo+NmW)
        self.sinrp = self.CmWp/(ImWp+NmW)

        self.sinr = True

    def evbestsv(self):
        """ determine the best server map

        Notes
        -----

        C.bestsv

        """
        na = self.na
        ng = self.ng
        nf = self.nf
        # find best server regions
        Vo = self.CmWo
        Vp = self.CmWp
        self.bestsvo = np.empty(nf*ng*na).reshape(nf,ng,na)
        self.bestsvp = np.empty(nf*ng*na).reshape(nf,ng,na)
        for kf in range(nf):
            MaxVo = np.max(Vo[kf,:,:],axis=1)
            MaxVp = np.max(Vp[kf,:,:],axis=1)
            for ka in range(na):
                uo = np.where(Vo[kf,:,ka]==MaxVo)
                up = np.where(Vp[kf,:,ka]==MaxVp)
                self.bestsvo[kf,uo,ka]=ka+1
                self.bestsvp[kf,up,ka]=ka+1
        self.best = True


#    def showEd(self,polar='o',**kwargs):
#        """ shows a map of direct path excess delay
#
#        Parameters
#        ----------
#
#        polar : string
#        'o' | 'p'
#
#        Examples
#        --------
#
#        .. plot::
#            :include-source:
#
#            >> from pylayers.antprop.coverage import *
#            >> C = Coverage()
#            >> C.cover()
#            >> C.showEd(polar='o')
#
#        """
#
#        if not kwargs.has_key('alphacy'):
#            kwargs['alphacy']=0.0
#        if not kwargs.has_key('colorcy'):
#            kwargs['colorcy']='w'
#        if not kwargs.has_key('nodes'):
#            kwargs['nodes']=False
#
#        fig,ax = self.L.showG('s',**kwargs)
#        l = self.grid[0,0]
#        r = self.grid[-1,0]
#        b = self.grid[0,1]
#        t = self.grid[-1,-1]
#
#        cdict = {
#        'red'  :  ((0., 0.5, 0.5), (1., 1., 1.)),
#        'green':  ((0., 0.5, 0.5), (1., 1., 1.)),
#        'blue' :  ((0., 0.5, 0.5), (1., 1., 1.))
#        }
#        #generate the colormap with 1024 interpolated values
#        my_cmap = m.colors.LinearSegmentedColormap('my_colormap', cdict, 1024)
#
#        if polar=='o':
#            prdbm=self.prdbmo
#        if polar=='p':
#            prdbm=self.prdbmp
#
#
#
#        if polar=='o':
#            mcEdof = np.ma.masked_where(prdbm < self.rxsens,self.Edo)
#
#            cov=ax.imshow(mcEdof.reshape((self.nx,self.ny)).T,
#                             extent=(l,r,b,t),cmap = 'jet',
#                             origin='lower')
#
#
#
#            # cov=ax.imshow(self.Edo.reshape((self.nx,self.ny)).T,
#            #           extent=(l,r,b,t),
#            #           origin='lower')
#            titre = "Map of LOS excess delay, polar orthogonal"
#
#        if polar=='p':
#            mcEdpf = np.ma.masked_where(prdbm < self.rxsens,self.Edp)
#
#            cov=ax.imshow(mcEdpf.reshape((self.nx,self.ny)).T,
#                             extent=(l,r,b,t),cmap = 'jet',
#                             origin='lower')
#
#            # cov=ax.imshow(self.Edp.reshape((self.nx,self.ny)).T,
#            #           extent=(l,r,b,t),
#            #           origin='lower')
#            titre = "Map of LOS excess delay, polar parallel"
#
#        ax.scatter(self.tx[0],self.tx[1],linewidth=0)
#        ax.set_title(titre)
#
#        divider = make_axes_locatable(ax)
#        cax = divider.append_axes("right", size="5%", pad=0.05)
#        clb = fig.colorbar(cov,cax)
#        clb.set_label('excess delay (ns)')
#
#        if self.show:
#            plt.show()
#        return fig,ax
#
#    def showPower(self,rxsens=True,nfl=True,polar='o',**kwargs):
#        """ show the map of received power
#
#        Parameters
#        ----------
#
#        rxsens : bool
#              clip the map with rx sensitivity set in self.rxsens
#        nfl : bool
#              clip the map with noise floor set in self.pndbm
#        polar : string
#            'o'|'p'
#
#        Examples
#        --------
#
#        .. plot::
#            :include-source:
#
#            > from pylayers.antprop.coverage import *
#            > C = Coverage()
#            > C.cover()
#            > C.showPower()
#
#        """
#
#        if not kwargs.has_key('alphacy'):
#            kwargs['alphacy']=0.0
#        if not kwargs.has_key('colorcy'):
#            kwargs['colorcy']='w'
#        if not kwargs.has_key('nodes'):
#            kwargs['nodes']=False
#        fig,ax = self.L.showG('s',**kwargs)
#
#        l = self.grid[0,0]
#        r = self.grid[-1,0]
#        b = self.grid[0,1]
#        t = self.grid[-1,-1]
#
#        if polar=='o':
#            prdbm=self.prdbmo
#        if polar=='p':
#            prdbm=self.prdbmp
#
##        tCM = plt.cm.get_cmap('jet')
##        tCM._init()
##        alphas = np.abs(np.linspace(.0,1.0, tCM.N))
##        tCM._lut[:-3,-1] = alphas
#
#        title='Map of received power - Pt = ' + str(self.ptdbm) + ' dBm'+str(' fGHz =') + str(self.fGHz) + ' polar = '+polar
#
#        cdict = {
#        'red'  :  ((0., 0.5, 0.5), (1., 1., 1.)),
#        'green':  ((0., 0.5, 0.5), (1., 1., 1.)),
#        'blue' :  ((0., 0.5, 0.5), (1., 1., 1.))
#        }
#
#        if not kwargs.has_key('cmap'):
#        # generate the colormap with 1024 interpolated values
#            cmap = m.colors.LinearSegmentedColormap('my_colormap', cdict, 1024)
#        else:
#            cmap = kwargs['cmap']
#        #my_cmap = cm.copper
#
#
#        if rxsens :
#
#            ## values between the rx sensitivity and noise floor
#            mcPrf = np.ma.masked_where((prdbm > self.rxsens)
#                                     & (prdbm < self.pndbm),prdbm)
#            # mcPrf = np.ma.masked_where((prdbm > self.rxsens) ,prdbm)
#
#            cov1 = ax.imshow(mcPrf.reshape((self.nx,self.ny)).T,
#                             extent=(l,r,b,t),cmap = cm.copper,
#                             vmin=self.rxsens,origin='lower')
#
#            ### values above the sensitivity
#            mcPrs = np.ma.masked_where(prdbm < self.rxsens,prdbm)
#            cov = ax.imshow(mcPrs.reshape((self.nx,self.ny)).T,
#                            extent=(l,r,b,t),
#                            cmap = cmap,
#                            vmin=self.rxsens,origin='lower')
#            title=title + '\n black : Pr (dBm) < %.2f' % self.rxsens + ' dBm'
#
#        else :
#            cov=ax.imshow(prdbm.reshape((self.nx,self.ny)).T,
#                          extent=(l,r,b,t),
#                          cmap = cmap,
#                          vmin=self.pndbm,origin='lower')
#
#        if nfl:
#            ### values under the noise floor
#            ### we first clip the value below the noise floor
#            cl = np.nonzero(prdbm<=self.pndbm)
#            cPr = prdbm
#            cPr[cl] = self.pndbm
#            mcPruf = np.ma.masked_where(cPr > self.pndbm,cPr)
#            cov2 = ax.imshow(mcPruf.reshape((self.nx,self.ny)).T,
#                             extent=(l,r,b,t),cmap = 'binary',
#                             vmax=self.pndbm,origin='lower')
#            title=title + '\n white : Pr (dBm) < %.2f' % self.pndbm + ' dBm'
#
#
#        ax.scatter(self.tx[0],self.tx[1],s=10,c='k',linewidth=0)
#
#        ax.set_title(title)
#        divider = make_axes_locatable(ax)
#        cax = divider.append_axes("right", size="5%", pad=0.05)
#        clb = fig.colorbar(cov,cax)
#        clb.set_label('Power (dBm)')
#
#        if self.show:
#            plt.show()
#
#        return fig,ax
#
#
#    def showTransistionRegion(self,polar='o'):
#        """
#
#        Notes
#        -----
#
#        See  : "Analyzing the Transitional Region in Low Power Wireless Links"
#                Marco Zuniga and Bhaskar Krishnamachari
#
#        Examples
#        --------
#
#        .. plot::
#            :include-source:
#
#            > from pylayers.antprop.coverage import *
#            > C = Coverage()
#            > C.cover()
#            > C.showTransitionRegion()
#
#        """
#
#        frameLength = self.framelengthbytes
#
#        PndBm = self.pndbm
#        gammaU = 10*np.log10(-1.28*np.log(2*(1-0.9**(1./(8*frameLength)))))
#        gammaL = 10*np.log10(-1.28*np.log(2*(1-0.1**(1./(8*frameLength)))))
#
#        PrU = PndBm + gammaU
#        PrL = PndBm + gammaL
#
#        fig,ax = self.L.showGs()
#
#        l = self.grid[0,0]
#        r = self.grid[-1,0]
#        b = self.grid[0,1]
#        t = self.grid[-1,-1]
#
#        if polar=='o':
#            prdbm=self.prdbmo
#        if polar=='p':
#            prdbm=self.prdbmp
#
#        zones = np.zeros(np.shape(prdbm))
#        #pdb.set_trace()
#
#        uconnected  = np.nonzero(prdbm>PrU)
#        utransition = np.nonzero((prdbm < PrU)&(prdbm > PrL))
#        udisconnected = np.nonzero(prdbm < PrL)
#
#        zones[uconnected] = 1
#        zones[utransition] = (prdbm[utransition]-PrL)/(PrU-PrL)
#        cov = ax.imshow(zones.reshape((self.nx,self.ny)).T,
#                             extent=(l,r,b,t),cmap = 'BuGn',origin='lower')
#
#        title='PDR region'
#        ax.scatter(self.tx[0],self.tx[1],linewidth=0)
#
#        ax.set_title(title)
#        divider = make_axes_locatable(ax)
#        cax = divider.append_axes("right", size="5%", pad=0.05)
#        fig.colorbar(cov,cax)
#        if self.show:
#            plt.show()
#
    def plot(self,**kwargs):
        """
        """
        defaults = { 'typ': 'pr',
                     'grid': False,
                     'f' : 0,
                     'a' : 0,
                     'db':True,
                     'label':'',
                     'pol':'p',
                     'col':'b'
                   }
        for k in defaults:
            if k not in kwargs:
                kwargs[k]=defaults[k]

        if 'fig' in kwargs:
            fig=kwargs['fig']
        else:
            fig=plt.figure()

        if 'ax' in kwargs:
            ax = kwargs['ax']
        else:
            ax = fig.add_subplot(111)

        if kwargs['typ']=='pr':
            if kwargs['a']!=-1:
                if kwargs['pol']=='p':
                    U = self.CmWp[kwargs['f'],:,kwargs['a']]
                if kwargs['pol']=='o':
                    U = self.CmWo[kwargs['f'],:,kwargs['a']]
            else:
                if kwargs['pol']=='p':
                    U = self.CmWp[kwargs['f'],:,:].reshape(self.na*self.ng)
                else:
                    U = self.CmWo[kwargs['f'],:,:].reshape(self.na*self.ng)
            if kwargs['db']:
                U = 10*np.log10(U)

        D = np.sqrt(np.sum((self.pa-self.pg)*(self.pa-self.pg),axis=0))
        if kwargs['a']!=-1:
            D = D.reshape(self.ng,self.na)
            ax.semilogx(D[:,kwargs['a']],U,'.',color=kwargs['col'],label=kwargs['label'])
        else:
            ax.semilogx(D,U,'.',color=kwargs['col'],label=kwargs['label'])

        return fig,ax

    def show(self,**kwargs):
        """ show coverage

        Parameters
        ----------

        typ : string
            'pr' | 'sinr' | 'capacity' | 'loss' | 'best' | 'egd' | 'ref'
        grid : boolean
        polar : string
            'o' | 'p'
        best : boolean
            draw best server contour if True
        f : int
            frequency index
        a : int
            access point index (-1 all access point)

        Examples
        --------

        .. plot::
            :include-source:

            >>> from pylayers.antprop.coverage import *
            >>> C = Coverage()
            >>> C.cover()
            >>> f,a = C.show(typ='pr',figsize=(10,8))
            >>> plt.show()
            >>> f,a = C.show(typ='best',figsize=(10,8))
            >>> plt.show()
            >>> f,a = C.show(typ='loss',figsize=(10,8))
            >>> plt.show()
            >>> f,a = C.show(typ='sinr',figsize=(10,8))
            >>> plt.show()

        See Also
        --------

        pylayers.gis.layout.Layout.showG

        """
        defaults = { 'typ': 'pr',
                     'grid': False,
                     'polar':'p',
                     'scale':30,
                     'f' : 0,
                     'a' :-1,
                     'db':True,
                     'cmap' :cm.jet,
                     'best':False,
                     'title': ''
                   }


        for k in defaults:
            if k not in kwargs:
                kwargs[k]=defaults[k]

        title = self.dap[list(self.dap.keys())[0]].s.name+ ' : ' + kwargs['title'] + " :"
        polar = kwargs['polar']
        best = kwargs['best']
        scale = kwargs['scale']

        assert polar in ['p','o'],"polar wrongly defined in show coverage"

        if 'fig' in kwargs:
            if 'ax' in kwargs:
                fig,ax=self.L.showG('s',fig=kwargs['fig'],ax=kwargs['ax'])
            else:
                fig,ax=self.L.showG('s',fig=kwargs['fig'])
        else:
            if 'figsize' in kwargs:
                fig,ax=self.L.showG('s',figsize=kwargs['figsize'])
            else:
                fig,ax=self.L.showG('s')

        # plot the grid
        if kwargs['grid']:
            for k in self.dap:
                p = self.dap[k].p
                ax.plot(p[0],p[1],'or')

        f = kwargs['f']
        a = kwargs['a']
        typ = kwargs['typ']
        assert typ in ['best','egd','sinr','snr','capacity','pr','loss','ref'],"typ unknown in show coverage"
        best = kwargs['best']

        dB = kwargs['db']

        # setting the grid

        l = self.grid[0,0]
        r = self.grid[-1,0]
        b = self.grid[0,1]
        t = self.grid[-1,-1]

        if typ=='best' and self.best:
            title = title + 'Best server'+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
            for ka in range(self.na):
                if polar=='p':
                    bestsv =  self.bestsvp[f,:,ka]
                if polar=='o':
                    bestsv =  self.bestsvo[f,:,ka]
                m = np.ma.masked_where(bestsv == 0,bestsv)
                if self.mode!='file':
                    W = m.reshape(self.nx,self.ny).T
                    ax.imshow(W, extent=(l,r,b,t),
                            origin='lower',
                            vmin=1,
                            vmax=self.na+1)
                else:
                    ax.scatter(self.grid[:,0],self.grid[:,1],c=m,s=scale,linewidth=0)
            ax.set_title(title)
        else:
            if typ == 'egd':
                title = title + 'excess group delay (ortho): '+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
                if polar=='o':
                    V = self.Edo
                if polar=='p':
                    V = self.Edp
                dB = False
                legcb =  'Delay (ns)'
            if typ == 'sinr':
                title = title + 'SINR : '+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
                if dB:
                    legcb = 'dB'
                else:
                    legcb = 'Linear scale'
                if polar=='o':
                    V = self.sinro
                if polar=='p':
                    V = self.sinrp
            if typ == 'snr':
                title = title + 'SNR : '+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
                if dB:
                    legcb = 'dB'
                else:
                    legcb = 'Linear scale'
                if polar=='o':
                    V = self.snro
                if polar=='p':
                    V = self.snrp
            if typ == 'capacity':
                title = title + 'Capacity : '+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
                legcb = 'Mbit/s'
                if polar=='o':
                    V = self.bmhz.T[np.newaxis,:]*np.log(1+self.sinro)/np.log(2)
                if polar=='p':
                    V = self.bmhz.T[np.newaxis,:]*np.log(1+self.sinrp)/np.log(2)
            if typ == "pr":
                title = title + 'Pr : '+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
                if dB:
                    legcb = 'dBm'
                else:
                    lgdcb = 'mW'
                if polar=='o':
                    V = self.CmWo
                if polar=='p':
                    V = self.CmWp

            if typ == "ref":
                title = kwargs['title']
                V = 10**(self.ref/10)
                if dB:
                    legcb = 'dB'
                else:
                    legcb = 'Linear scale'

            if typ == "loss":
                title = title + 'Loss : '+' fc = '+str(self.fGHz[f])+' GHz'+ ' polar : '+polar
                if dB:
                    legcb = 'dB'
                else:
                    legcb = 'Linear scale'
                if polar=='o':
                    V = self.Lwo*self.freespace
                if polar=='p':
                    V = self.Lwp*self.freespace

            if a == -1:
                V = np.max(V[f,:,:],axis=1)
            else:
                V = V[f,:,a]

            # reshaping the data on the grid
            if self.mode!='file':
                U = V.reshape((self.nx,self.ny)).T
            else:
                U = V

            if dB:
                U = 10*np.log10(U)

            if 'vmin' in kwargs:
                vmin = kwargs['vmin']
            else:
                vmin = U.min()

            if 'vmax' in kwargs:
                vmax = kwargs['vmax']
            else:
                vmax = U.max()

            if self.mode!='file':
                img = ax.imshow(U,
                            extent=(l,r,b,t),
                            origin='lower',
                            vmin = vmin,
                            vmax = vmax,
                            cmap = kwargs['cmap'])
            else:
                img=ax.scatter(self.grid[:,0],
                               self.grid[:,1],
                               c=U,
                               s=scale,
                               linewidth=0,
                               cmap=kwargs['cmap'],
                               vmin=vmin,
                               vmax=vmax)

            # for k in range(self.na):
            #     ax.annotate(str(k),xy=(self.pa[0,k],self.pa[1,k]))
            for k in self.dap.keys():
                ax.annotate(str(self.dap[k]['name']),xy=(self.dap[k]['p'][0],self.dap[k]['p'][1]))
            ax.set_title(title)

            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.05)
            clb = fig.colorbar(img,cax)
            clb.set_label(legcb)
            if best:
                if self.mode!='file':
                    if polar=='o':
                        ax.contour(np.sum(self.bestsvo,axis=2)[f,:].reshape(self.nx,self.ny).T,extent=(l,r,b,t),linestyles='dotted')
                    if polar=='p':
                        ax.contour(np.sum(self.bestsvp,axis=2)[f,:].reshape(self.nx,self.ny).T,extent=(l,r,b,t),linestyles='dotted')

        # display access points
        if a==-1:
            ax.scatter(self.pa[0,:],self.pa[1,:],s=scale+10,c='r',linewidth=0)
        else:
            ax.scatter(self.pa[0,a],self.pa[1,a],s=scale+10,c='r',linewidth=0)
        plt.tight_layout()
        return(fig,ax)

#    def showLoss(self,polar='o',**kwargs):
#        """ show losses map
#
#        Parameters
#        ----------
#
#        polar : string
#            'o'|'p'|'both'
#
#        Examples
#        --------
#
#        .. plot::
#            :include-source:
#
#            >>> from pylayers.antprop.coverage import *
#            >>> C = Coverage()
#            >>> C.cover(polar='o')
#            >>> f,a = C.show(typ='pr',figsize=(10,8))
#            >>> plt.show()
#        """
#
#        fig = plt.figure()
#        fig,ax=self.L.showGs(fig=fig)
#
#        # setting the grid
#
#        l = self.grid[0,0]
#        r = self.grid[-1,0]
#        b = self.grid[0,1]
#        t = self.grid[-1,-1]
#
#        Lo = self.freespace+self.Lwo
#        Lp = self.freespace+self.Lwp
#
#        # orthogonal polarization
#
#        if polar=='o':
#            cov = ax.imshow(Lo.reshape((self.nx,self.ny)).T,
#                            extent=(l,r,b,t),
#                            origin='lower',
#                            vmin = 40,
#                            vmax = 130)
#            str1 = 'Map of losses, orthogonal (V) polarization, fGHz='+str(self.fGHz)
#            title = (str1)
#
#        # parallel polarization
#        if polar=='p':
#            cov = ax.imshow(Lp.reshape((self.nx,self.ny)).T,
#                            extent=(l,r,b,t),
#                            origin='lower',
#                            vmin = 40,
#                            vmax = 130)
#            str2 = 'Map of losses, orthogonal (V) polarization, fGHz='+str(self.fGHz)
#            title = (str2)
#
#        ax.scatter(self.tx[0],self.tx[1],s=10,c='k',linewidth=0)
#        ax.set_title(title)
#
#        divider = make_axes_locatable(ax)
#        cax = divider.append_axes("right", size="5%", pad=0.05)
#        clb = fig.colorbar(cov,cax)
#        clb.set_label('Loss (dB)')
#
#        if self.show:
#            plt.show()



if (__name__ == "__main__"):
    doctest.testmod()

