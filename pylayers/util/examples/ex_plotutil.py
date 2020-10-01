import os
import scipy as sp
import numpy as np
from pylayers.util.plotutil import *
import matplotlib.pylab as plt

x = np.arange(100)
y = np.random.rand(4,100)+1j*np.random.rand(4,100)
fig,ax=mulcplot(x,y,typ=['m'],color='b',marker='o',linestyle='dashed')

x = np.arange(100)
y = np.random.rand(4,100)+1j*np.random.rand(4,100)
fig,ax=mulcplot(x,y,typ=['m'],color='r',marker='o',linestyle='dot',fig=fig,ax=ax)


x = np.arange(100)
y = np.random.rand(4,100)+1j*np.random.rand(4,100)
fig,ax=mulcplot(x,y,typ=['l10'],color='b')

y = np.random.rand(4,100)+1j*np.random.rand(4,100)
fig,ax=mulcplot(x,y,typ=['l10'],color='k',fig=fig,ax=ax)
