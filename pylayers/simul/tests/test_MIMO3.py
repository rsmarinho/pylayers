from pylayers.simul.link import *
import pylayers.signal.waveform as wvf
from pylayers.antprop.aarray import *
import matplotlib.animation as animation 
import pdb
import warnings 

# warnings.filterwarnings("error")
# set the frequency range
fcGHz=28
WMHz = 3000
Nf = 1 
fGHz = np.linspace(fcGHz-WMHz*0.5e-3,fcGHz+WMHz*0.5e-3,Nf)
#fGHz = np.array([fcGHz])
# set the layout
L=Layout('defstr.lay',bbuild=1)
#L=Layout('defstr.ini',bdiffraction=True)
#L=Layout('defstr.ini',bbuild=True)
#L=Layout('TC2_METIS.ini',bbuild=1)
#L=Layout('W2PTIN.ini',build=False)
# set the link
DL=DLink(L=L,fGHz=fGHz,outdoor=False,applywav=True)
DL.L.indoor=True
#DL.L.indoor=False
DL.L.build()
#DL.ca= 23
#DL.cb=14
DL.ca= 2
DL.cb= 5
#DL.b = np.array([761.5,1113,1.2])
#DL.Aa=Antenna(typ='Omni')
lmbda = 0.3/fcGHz
DL.Aa = AntArray(tarr='UA',N=[10,10,1],dm=[lmbda*0.5,lmbda*0.5,0],fGHz=fcGHz)
DL.Ab = AntArray(tarr='UA',N=[10,10,1],dm=[lmbda*0.5,lmbda*0.5,0],fGHz=fcGHz)
#DL.b=np.array([766,1115,1.8])
tic = time.time()
#DL.eval(verbose=True,force=True,bt=False,cutoff=4,threshold=0.1,ra_vectorized=False)
DL.eval(verbose=True,force=True,bt=False,cutoff=4,threshold=0.1,ra_vectorized=True,nD=1)
toc = time.time()
print(toc-tic)
#DL.b=np.array([755,1110,1.5])
#DL.eval(force=['sig','ray','Ct','H'],ra_vectorized=True,diffraction=True)
#dist_a_b = np.sqrt(np.sum((DL.a-DL.b)**2))
#
#if DL.R.los:
#    ak0 = DL.H.ak[0]
#    tk0 = DL.H.tk[0]
#   assert tk0*0.3 == dist_a_b, 'invalid distance'
#    lak0 = 20* np.log10(ak0)
#    Friss= 20*np.log10(2.4)+20*np.log10(dist_a_b) + 32.4
#    assert np.allclose(-lak0,Friss,0.1), 'issue in Friss'

# Point outside
#DL.eval(force=['sig','ray','Ct','H'],ra_vectorized=True,diffraction=True,ra_ceil_H=0)
#DL.eval(force=['sig','ray','Ct','H'],ra_vectorized=True,diffraction=True)
# Angular Spread 
doa = DL.H.doa
dod = DL.H.dod
tau = DL.H.taud
E   = DL.H.energy()[:,0,0]
APSthd=np.sum(dod[:,0]*E)/np.sum(E)
APSphd=np.sum(dod[:,1]*E)/np.sum(E)
APStha=np.sum(doa[:,0]*E)/np.sum(E)
APSpha=np.sum(doa[:,1]*E)/np.sum(E)

#
# calculate baseband H matrix Nf frequency points
#
H = DL.H.baseband(fcGHz=fcGHz,WMHz=200,Nf=128)

#fig = plt.figure()
#ax = plt.gca()
#k = 0  
#def init():
#    global k  
#    im = ax.imshow(np.log10(np.abs(H.y[:,:,k])),animated=True,interpolation='nearest',cmap='jet')
#    plt.axis('auto')
#    tit = ax.set_title('f ='+str(fcGHz+H.x[k]/1000.)+ ' GHz',fontsize=24)
#    #cb = plt.colorbar(im)
#    return im,tit
#
#def updatefig(*args):
#    global k 
#    k = k+ 1
#    im.set_array(np.log10(np.abs(H.y[:,:,k%128])))
#    tit.set_label('f =' + str(fcGHz+H.x[k%128]/1000.)+' GHz')
#    return im,tit
#
#ani = animation.FuncAnimation(fig,updatefig,init_func=init,interval=0.5,blit=True) 
##writer = animation.writers['ffmpeg'](fps=30)
##ani.save('MIMO.mp4',writer=writer,dpi=100)
#ani.save('MIMO.gif',writer='imagemagick',fps=60)
#plt.show()
