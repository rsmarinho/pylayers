import numpy as np
from pylayers.measures.vna.E5072A import *
from pylayers.measures.parker.smparker import *
from pylayers.antprop.channel import *
from pylayers.measures.exploith5 import *

M = Mesh5('mimocal')
dcal = M.get_dcal(1)
#M.plot(cmd='mes',mes='mes1',lg=[2,0,1,0])
#M.plot(cmd='cal',mes='mes1',lg=[2,0,1,0])
#M.plot(cmd='ri',mes='mes1',lg=[2,0,1,0])
#f = h5py.File(M.filename,'r')
#f['mes3']
#H = np.array(f['mes3'])
#plt.imshow(np.abs(H[0,0,0,:,:]))
#plt.show()
#plt.ion()
#M.dmes
#M.mes
#M.read('mes',1)
#M.read('mes',[1,1])
#M.mes.plot()
#cir = M.mes.ift(ffts=1)
#cir.plot()


