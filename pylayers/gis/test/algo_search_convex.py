#-*- coding:Utf-8 -*-

# from pylayers.gis.layout import *
# from itertools import combinations
# from scipy.spatial import Delaunay
# import shapely.geometry as sh
# L = Layout('WHERE1_2.ini')
# L.build('t')
# # L.dumpr()
# L.showG('s')

# for n in L.Gt.nodes():
#     no = L.Gt.node[n]['cycle'].cycle
#     nop = L.Gt.node[n]['cycle'].cycle

#     tcc, nn = L.Gt.node[n]['polyg'].ptconvex()

#     utconvex = np.nonzero(tcc == 1)[0]
#     utsconvex = np.nonzero(abs(tcc) == 1)[0]
#     if len(utconvex) != 0:
#         # get points ID in the cycle
#         uu = filter(lambda x: x<0,no)
#         uus = filter(lambda x: x<0,no)
#         # get point convex ID
#         uc = np.array(uu)[utconvex]
#         ucs = np.array(uus)[utsconvex]
#         puc = array(map(lambda x: L.Gs.pos[x], uc))
#         pucs = array(map(lambda x: L.Gs.pos[x], ucs))

#         trid=Delaunay(pucs)
#         tri =trid.simplices
#         # filter tri in the cycle
#         kt = []
#         pkt = []
#         for t in tri:
#             ts = sh.Polygon(pucs[t])
#             U = ts.intersection(L.Gt.node[n]['polyg'])
#             if not U.area < 1e-2:
#                 #pkt.append(pucs[t])
#                 kt.append(t) 
#             # # ptt = puc[tt]
#         plt.triplot(pucs[:,0],pucs[:,1], np.array(kt))




# for n in L.Gt.nodes():
#     if n > 0:
#         no = L.Gt.node[n]['cycle'].cycle
#         tcc, nn = L.Gt.node[n]['polyg'].ptconvex()
#         utconvex = np.nonzero(tcc == 1)[0]
#         utsconvex = np.nonzero(abs(tcc) == 1)[0]
#         if len(utconvex) != 0:
#             # get points ID in the cycle
#             uu = filter(lambda x: x<0,no)
#             uus = filter(lambda x: x<0,no)
#             # get point convex ID
#             # uc = np.array(uu)[utconvex]
#             ucs = np.array(uus)[utsconvex]
#             puc = array(map(lambda x: L.Gs.pos[x], uc))
#             pucs = array(map(lambda x: L.Gs.pos[x], ucs))
#             if len(ucs) >2:
#                 trid=Delaunay(pucs)
#                 tri =trid.simplices
#                 # filter tri in the cycle
#                 kt = []
#                 pkt = []
#                 for t in tri:
#                     ts = sh.Polygon(pucs[t])
#                     U = L.Gt.node[n]['polyg'].contains(ts)
#                     if U:
#                         #pkt.append(pucs[t])
#                         kt.append(t) 
#                     # # ptt = puc[tt]
#             try:
#                 plt.triplot(pucs[:,0],pucs[:,1], np.array(kt))
#             except: 
#                 pass

from pylayers.gis.layout import *
from itertools import combinations
from scipy.spatial import Delaunay
import shapely.geometry as sh

Lfile = 'scattering_nonconvex.ini'
data = '/home/niamiot/Documents/code/pylayers/data/struc/ini/'+Lfile
proj = '/home/niamiot/Documents/Pylayers_project/P1/struc/ini/'+Lfile

shutil.copyfile(data,proj)

L = Layout(Lfile,force=True)
#L.dumpr()
L.build('t')
fig,ax=L.showG('s',labels=True)
        
def polyplot(poly,fig=[]):
    if fig == []:
        fig=plt.figure()
    fig,ax=L.showG('s',fig=fig)
    color=['r','b','g']*10
    for ip, p in enumerate(poly):
        fig,ax = p.plot(fig=fig,ax=ax,color=color[ip],alpha =0.5)

# lacy : list of added cycles
lacy =[]
for n in L.Gt.nodes():
    #if indoor cycles
    if n > 0:
        ncy=max(L.Gt.nodes())

        ####
        #### 1 Determine if pt convex in cycle
        ####

        if L.Gt.node[n]['indoor']:
            no = L.Gt.node[n]['cycle'].cycle
            tcc, nn = L.Gt.node[n]['polyg'].ptconvex()
            # diffracting points 
            utconvex = np.nonzero(tcc == 1)[0]
            #all possible diffracting point (in and out of cycle)
            utsconvex = np.nonzero(abs(tcc) == 1)[0]
            if len(utconvex) != 0:
                # get points ID in the cycle
                uus = filter(lambda x: x<0,no)
                # get point convex ID
                uc = np.array(uus)[utconvex]
                ucs = np.array(uus)[utsconvex]
                pucs = array(map(lambda x: L.Gs.pos[x], ucs))
                pucs = np.vstack((pucs,pucs[-1]))

                ####
                #### 2 perform a Delaunay Partioning 
                ####

                if len(ucs) >2:
                    trid=Delaunay(pucs)
                    tri =trid.simplices
                    aucs = np.arange(len(ucs))
                    # filter tri in the cycle
                    kt = []
                    pkt = []
                    polys = []
                    naw = []
                    for t in tri:
                        ts = geu.Polygon(pucs[t])
                        # check if the new polygon is contained into 
                        #the original polygon (non guaratee by Delaunay)
                        #U = L.Gt.node[n]['polyg'].contains(ts)
                        U = L.Gt.node[n]['polyg'].intersection(ts)
                        if not isinstance(U,sh.MultiPolygon):
                            U=[U]
                        for p in U:
                            if L.Gt.node[n]['polyg'].contains(p):
                                cp = geu.Polygon(p)
                                cp.setvnodes(L)
                                uaw = np.where(cp.vnodes == 0)[0]
                                lvn = len(cp.vnodes)
                                for i in uaw:
                                    #keep trace of created airwalls, because some 
                                    #of them will be destroyed in step 3.
                                    naw.append(L.add_segment(
                                               cp.vnodes[np.mod(i-1,lvn)],
                                               cp.vnodes[np.mod(i+1,lvn)]
                                               ,name='AIR'))
                                polys.append(cp)
                import ipdb
                ipdb.set_trace()
                #
                # 3. merge delaunay triangulation in order to obtain
                #   the larger convex polygons partioning 
                #
                cpolys = []
                nbpolys = len(polys)
                while polys !=[]:
                    p = polys.pop(0)
                    for ip2,p2 in enumerate(polys):
                        conv=False
                        inter = p.intersection(p2)
                        #if 2 triangles have a common segment
                        pold = p
                        if isinstance(inter,sh.LineString):
                            p = p + p2
                            if p.isconvex():
                                if p.area < 1e-1:
                                    import ipdb
                                    ipdb.set_trace()
                                polys.pop(ip2)
                                polys.insert(0,p)
                                conv=True
                                break
                            else:
                                # if pold not in cpolys:
                                #     cpolys.append(pold)
                                p = pold
                    # if (ip2 >= len(polys)):# and (conv):
                    # if conv :
                    #     if p not in cpolys:
                    #         cpolys.append(p)
                    if not conv:#else:
                        if pold not in cpolys:
                            cpolys.append(pold)
                    if len(polys) == 0:
                        cpolys.append(p)
                    # polyplot(cpolys,fig=plt.gcf())
                    # plt.draw()
                    # import ipdb
                    # ipdb.set_trace()
                ####
                #### 4. ensure the correct vnode numerotaion of the polygons
                #### and remove unecessary airwalls

                # ncpol : new created polygons
                ncpol = []
                vnodes=[]
                for p in cpolys:
                    interpoly = L.Gt.node[n]['polyg'].intersection(p)
                    if isinstance(interpoly,sh.MultiPolygon):
                        raise AttributeError('multi polygon encountered')
                    else :
                        ptmp = geu.Polygon(interpoly)
                    ptmp.setvnodes(L)
                    ncpol.append(ptmp)
                    vnodes.extend(ptmp.vnodes)
                #air walls to be deleted (because origin Delaunay triangle
                # has been merged )
                daw = filter(lambda x: x not in vnodes,naw)
                [L.del_segment(d,verbose=False) for d in daw]
                nbpolys=len(ncpol)

                #remove old cycle
                L.Gt.remove_node(n)
                # lcyid: (new) list of cycle id 
                lcyid = [n] + range(ncy+1,ncy+(nbpolys))
                lacy.extend(lcyid)
                for ip,p in enumerate(ncpol):
                    #p.coorddeter()
                    cyid = lcyid[ip]
                    # replace by new ones
                    lnode = p.vnodes
                    G = nx.subgraph(L.Gs,lnode)
                    G.pos = {}
                    G.pos.update({l: L.Gs.pos[l] for l in lnode})
                    cy  = cycl.Cycle(G,lnode=p.vnodes)
                    L.Gt.add_node(cyid,cycle=cy)
                    # WARNING
                    # recreate polygon is mandatory otherwise cycle.cycle and polygon.vnodes
                    #are shifted.
                    L.Gt.node[cyid]['polyg'] = p#geu.Polygon(p.xy,cy.cycle)
                    L.Gt.node[cyid]['indoor']=True
                    L.Gt.node[cyid]['isopen']=True
                    L.Gt.pos[cyid] = tuple(cy.g)

                Gtnodes= filter(lambda x: x>0,L.Gt.nodes())
                for k in combinations(Gtnodes, 2):
                    vnodes0 = np.array(L.Gt.node[k[0]]['cycle'].cycle)
                    vnodes1 = np.array(L.Gt.node[k[1]]['cycle'].cycle)
                    #
                    # Connect Cycles if they share at least one segments
                    #
                    intersection_vnodes = np.intersect1d(vnodes0, vnodes1)

                    if len(intersection_vnodes) > 1:
                        segment = intersection_vnodes[np.where(intersection_vnodes>0)]
                        L.Gt.add_edge(k[0], k[1],segment= segment)

#update self.Gs.node[x]['ncycles']
L._updGsncy()
#add outside cycle to Gs.node[x]['ncycles']
L._addoutcy()
#update interaction list into Gt.nodes (cycles)
L._interlist(nodelist=lacy)


# polyplot(ncpol)




# for n in L.Gt.nodes():
#     if n > 0:
#         no = L.Gt.node[n]['cycle'].cycle
#         tcc, nn = L.Gt.node[n]['polyg'].ptconvex()
#         # diffracting points 
#         utconvex = np.nonzero(tcc == 1)[0]
#         #all possible diffracting point (in and out of cycle)
#         utsconvex = np.nonzero(abs(tcc) == 1)[0]
#         if len(utconvex) != 0:
#             # get points ID in the cycle
#             uus = filter(lambda x: x<0,no)
#             # get point convex ID
#             uc = np.array(uus)[utconvex]
#             ucs = np.array(uus)[utsconvex]
#             pucs = array(map(lambda x: L.Gs.pos[x], ucs))
#             pucs = np.vstack((pucs,pucs[-1]))

#             if len(ucs) >2:
#                 trid=Delaunay(pucs)
#                 tri =trid.simplices
#                 utri = ucs[tri]
#                 # filter tri in the cycle
#                 kt = []
#                 pkt = []
#                 polys = []
#                 for t in tri:
#                     ts = geu.Polygon(pucs[t])
#                     #check if inside the original polygon
#                     # U = L.Gt.node[n]['polyg'].contains(ts)

#                     U = L.Gt.node[n]['polyg'].intersection(ts)
#                     ats = ts.area
#                     # fig,ax=ts.plot(fig=fig,ax=ax)
#                     if U.area > (1*ats/100):
#                         #pkt.append(pucs[t])
#                         kt.append(t) 
#                         polys.append(ts)
#             polyplot(polys)
  
#                     # # ptt = puc[tt]
#             # try:
#             #     plt.triplot(pucs[:,0],pucs[:,1], np.array(kt))
#             # except: 
#             #     pass
#             kt = array(kt)
#             npttri = np.arange(0,np.max(kt))
#             # search for each triangle, which is connecte
#             conecttri = [np.where(kt == i) for i in npttri]

#             cpolys = []
#             nbpolys = len(polys)
#             while polys !=[]:
#                 p = polys.pop(0)
#                 for ip2,p2 in enumerate(polys):
#                     conv=False
#                     inter = p.intersection(p2)
#                     #if 2 triangles have a common segment
#                     pold = p
#                     if isinstance(inter,sh.LineString):
                        
#                         p = p + p2
#                         if p.isconvex():
#                             polys.pop(ip2)
#                             polys.insert(0,p)
#                             conv=True
#                             break
#                         elif len(cpolys) != 0:
#                             if pold != cpolys[-1]:
#                                 cpolys.append(pold)
#                                 p = pold
#                         else : 
#                             cpolys.append(pold)
#                             p = pold

#                 # if (ip2 >= len(polys)):# and (conv):
#                 if conv :
#                     cpolys.append(p)
#                 else:
#                     cpolys.append(pold)
#                 if len(polys) == 0:
#                     cpolys.append(p)
#                 # polyplot(polys)
#                 # import ipdb
#                 # ipdb.set_trace()

# polyplot(cpolys)










###################################################
#################################################
####################################################
###################################################
#################################################
####################################################
###################################################
#################################################
####################################################


            # for n in range(nbpolys):
            #     p = polys.pop(-1)
            #     ip = iter(polys)
            #     for p2 in ip:
            #         inter = p.intersection(p2)
            #         if isinstance(inter,sh.LineString):
                        

            #     import ipdb
            #     ipdb.set_trace()
            #     try:
            #         mpold = mp
            #         if mp.touches(p):
            #             mp = mp + p
            #             if mp.isconvex():
            #                 mpold = mp
            #             else :
            #                 cpolys.append(mpold)
            #                 del mp
            #         else    
            #     except:
            #         mp = p

    


################
#############""

# for n in L.Gt.nodes():
#     no = L.Gt.node[n]['cycle'].cycle
#     nop = L.Gt.node[n]['cycle'].cycle

#     tcc, nn = L.Gt.node[n]['polyg'].ptconvex()

#     utconvex = np.nonzero(tcc == 1)[0]
#     if len(utconvex) != 0:
#         # get points ID in the cycle
#         ii = filter(lambda x: x<0,no)
#         # get point convex ID
#         ic = np.array(ii)[utconvex]
#         pic = array(map(lambda x: L.Gs.pos[x], ic))
#         luc = [nqp.where(ic[x]==no)[0][0] for x in range(len(ic))]
#         # to close the cycle
#         luc.append(luc[0])
#         # distance between each uc
#         duc = np.roll(np.mod(np.diff(luc),len(no)),1)
          # rnp.mod(np.diff(luc[::-1]),len(no))

#         lenic = len(ic)
#         ptbl=[]
        
#         for u in range(lenic-1,-1,-1):
#             # find which convex point is the closest but not directly connected
#             if duc[u-1] == duc[np.mod(u+1,lenic)]:
#                 import ipdb
#                 ipdb.set_trace()
#             if (duc[u-1] < duc[np.mod(u+1,lenic)]) and duc[u-1] > 2:
#                 #node to be linked
#                 tbl = no[luc[np.mod(u+1,lenic)]]
#             else:
#                 tbl = no[luc[u-1]]
#                 #node to be linked
#             ptbl.append(L.Gs.pos[tbl])
        
#         X=np.array(ptbl)
#         plu.displot(X.T,pic.T)

# ################
# #############""
# for n in L.Gt.nodes():
#     if n != 0:
#         no = L.Gt.node[n]['cycle'].cycle
#         tcc, nn = L.Gt.node[n]['polyg'].ptconvex()
#         utconvex = np.nonzero(tcc == 1)[0]
#         if len(utconvex) != 0:
#             # get points ID in the cycle
#             ii = filter(lambda x: x<0,no)
#             # get point convex ID
#             ic = np.array(ii)[utconvex]
#             pic = array(map(lambda x: L.Gs.pos[x], ic))
#             luc = [np.where(ic[x]==no)[0][0] for x in range(len(ic))]
#             lenuc = len(luc)
#             # to close the cycle
#             luc.append(luc[0])
#             duc = np.roll(np.mod(np.diff(luc),len(no)),1)

#             # distance between each uc
#             ptbl=[]
#             for u in range(len(duc)):

#                 um = np.mod(u-1,lenuc)
#                 up = np.mod(u+1,lenuc)
#                 print no[luc[u]],no[luc[um]]
#                 print no[luc[u]],no[luc[up]]

#                 if (duc[u] < duc[up]) and (duc[u] >2):
#                     print 'choose',no[luc[u]],no[luc[um]]
#                     tbl = no[luc[um]]
#                     ptbl.append([pic[u],pic[um]])
#                 elif duc[up] >2:
#                     print 'choose',no[luc[u]],no[luc[up]]
#                     tbl = no[luc[up]]
#                     ptbl.append([pic[u],pic[up]])
#                 # import ipdb
#                 # ipdb.set_trace()
#             X=np.array(ptbl)
#             plu.displot(X[:,0].T,X[:,1].T)


#             import ipdb
#             ipdb.set_trace()
                
            # import ipdb
            # ipdb.set_trace()

# for n in L.Gt.nodes():
#     no = L.Gt.node[n]['cycle'].cycle
#     lno = len(no)
#     nop = L.Gt.node[n]['cycle'].cycqle

#     tcc, nn = L.Gt.node[n]['polyg'].ptconvex()

#     utconvex = np.nonzero(tcc == 1)[0]
#     if len(utconvex) != 0:
#         # get points ID in the cycle
#         uu = filter(lambda x: x<0,no)
#         # get point convex ID (utconvex*2 because point follow segment in 
#         # cycles. and utconvex only concern points)
#         uc = no[utconvex*2]
#         pc = array(map(lambda x: L.Gs.pos[x], uc))
#         # id of adjacent segemnts 1
#         ucm = no[np.mod((utconvex*2)-1,lno)]
#         pcm = array(map(lambda x: L.Gs.pos[x], ucm))
#         # id of adjacent segemnts 2
#         ucp = no[np.mod((utconvex*2)+1,lno)]
#         pcp = array(map(lambda x: L.Gs.pos[x], ucp))
#         # build vector director of segment1-point and segment 2-point
#         vcm = (pcm-pc)/(np.sum(pcm-pc,axis=0))
#         vcp = (pcp-pc)/(np.sum(pcp-pc,axis=0))
#         import ipdb
#         ipdb.set_trace()
#         ss = L.seginline(pc[0],pcm[0])
        

        # if len(uc) > 1:
        #     for nw in combinations(uc,2):
        #             pf = map(lambda x: self.Gw.pos[x],nw)
        #             pf =  np.array((pf))
        #             if self.seginline(pf[0],pf[1]).shape[1] <= 1:
        #                 d = np.sqrt(np.sum((pf[0]-pf[1])**2))
        #                 self.Gw.add_edges_from([(nw[0],nw[1])],weight=d)
