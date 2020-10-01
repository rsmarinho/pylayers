import matplotlib.pyplot as plt
import shapely.geometry as sh
import shapely.ops as sho
import numpy as np
from pylayers.gis.layout import *


# seg_connect = [L.Gs.edge[x].keys() for x in L.Gs.nodes() if x >0]
# pts = [(L.Gs.pos[x[0]],L.Gs.pos[x[1]]) for x in seg_connect ]
# lines = [sh.LineString(p) for p in pts]
# X=sho.polygonize(lines)
# P=[x for x in X]
# pols = sho.cascaded_union(P)

# test simple add / delete
L=Layout('Luebbers_raw.ini',force=True)

L.add_segment(-2,-5)
L.add_segment(-3,-8)
L.del_segment(18)

L=Layout('Luebbers_raw.ini',force=True)

L.add_pons(8,0.5)
L.add_pons(6,0.5)
L.add_segment(-17,-18)
# import ipdb
# ipdb.set_trace()
# L.del_segment(19)
# L._updateGt()

