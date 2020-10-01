from pylayers.gis.layout import Layout
from pylayers.util.project import * 
import pylayers.util.pyutil as pyu
import networkx as nx
import matplotlib.pyplot as plt
import warnings
import shutil

warnings.filterwarnings("error")

#doctest.testmod(layout)
#L = Layout('TA-Office.ini')
L =  Layout()
lL = L.ls()
for tL in lL:
    print('Layout :     ',tL)
    print( '--------------------------')
    if 'Munich' not in tL:
        L = Layout(tL,bbuild=0,bgraphs=0)
        f,a = L.showG('s')
        plt.title(tL,fontsize=32)
        plt.show()
        plt.close('all')
    #if L.check():
    #    L.save()
        #filein = pyu.getlong(L._filename, pstruc['DIRLAY'])
        #fileout = '/home/uguen/Documents/rch/devel/pylayers/data/struc/lay/'+L._filename
        #print fileout
        #shutil.copy2(filein,fileout)
#figure(figsize=(20,10))
#plt.axis('off')
#f,a = L.showG('s',nodes=False,fig=f)
#plt.show()
#f,a = L.showG('r',edge_color='b',linewidth=4,fig=f)
#L= Layout('11Dbibli.ini')
#L.show()
#L = Layout('PTIN.ini')
#L = Layout('DLR.ini')
#L.buildGt()
#Ga = L.buildGr()
#L.showGs()
#nx.draw(Ga,Ga.pos)
