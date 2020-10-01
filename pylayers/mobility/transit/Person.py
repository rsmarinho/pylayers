"""
.. currentmodule:: pylayers.mobility.transit.Person

Utility Functions
=================

.. autosummary
    :toctree: generated/

    scale
    copy

Person Class
=================

.. autosummary
    :toctree: generated/

    Person.__init__
    Person.__repr__
    Person.move
    Person.delete
"""

import datetime
import sys

if sys.version_info.major==2:
    import ConfigParser
    from SimPy.SimulationRT import Process,Simulation,hold
else:
    import configparser as ConfigParser
    from  simpy import Process

#from math import *
#from random import normalvariate,uniform
from pylayers.mobility.transit.vec3 import vec3
from pylayers.mobility.transit.World import world
from pylayers.mobility.transit.SteeringBehavior import default_steering_mind
# from random import uniform,gauss,sample,seed
import random
import numpy as np

from pylayers.network.network import Network
from pylayers.util.utilnet import conv_vecarr

import matplotlib.pylab as plt
import pandas as pd
#from pylayers.util.pymysqldb import Database 
import pylayers.util.pyutil as pyu
import pylayers.util.plotutil as plu

import pdb

def truncate(self, max):
    """
    Parameters 
    ----------

    max

    References 
    ----------

    "near collision avoidance" inspired from
    http://people.revoledu.com/kardi/publication/Kouchi2001.pdf

    """
    if self.length() > max:
        return self.normalize() * max
    else:
        return vec3(self)

vec3.truncate = truncate

def scale(self, size):
    """
    Parameters
    ----------

    size : float 
        scaling factor

    Returns
    -------

    scaled version of self


    """
    return self.normalize() * size


vec3.scale = scale

def copy(self):
    return vec3(self)

vec3.copy = copy

class Person(Process):
    """ Person Process

    Attributes
    ----------

    ID    : float/hex/str/...
            agent Id
    interval : float
            refresh interval of agent mobility
    roomId : int
            room ID where agent start when simulation is launched
    L : pylayers.gis.layout.Layout()
        Layout instance, in which the agent is moving
    net : pylayers.network.Network()
        Network instance, in which network agent are communicating.
        This is used for fill the true position filed of the graph
        It must be removed in a further version ( when a proper save instance
        would be created)
    wld : pylayers.mobility.transit.world.world()
        world instance. equivalent to layout but in the pytk framework. 
        TODO : remove in a further version
    sim : SimPy.Simulation.Simulation.RT()
        Simulation instance share by all the pylayer project. 
    moving : bool 
        indicate if the agent is moving or not ( relevant for acces poitns)
    froom : list
        list of forbiden rooms. 
    wait : float
        wait time of the agent when he has reach teh desitaion
    cdest : str
        method for choosing setination 'random ' of file read
    save : list
        list of save option type .
        It will be removed in a further version ( when a proper save instance
        would be created)


    Methods
    -------

    Move : make the agent move

    """
    max_acceleration = 2.0 # m/s/s
    max_speed    = 1.2 # m/s
    #radius = 0.2106  # if one person takes 1.5 feet^2 of space, per traffic stds
    # 2r = 0.5 to 0.7 for "sports fans", per the Helbing, Farkas, Vicsek paper
    radius       = 2.85   # per the Teknomo, et al, paper
    mass         = 80 # kg
    average_radius   = 0.8/(2*np.pi)# Radius = Perimeter / 2pi 
    npers        = 0
    #GeomNet      = np.array((0,0,[[1,2,3]],[[1,0,0]],[[0,0,1]]),dtype=GeomNetType)
    def __init__(self, ID = 0, interval=0.05,roomId=-1, L=[], net=Network(),
        wld = world(),seed=0,sim=None,moving=True,froom=[],wait=1.0,cdest='random',
        save=[],color='k',pdshow=False):
        """ Class Person
            inherits of Simpy.SimulationRT
            """
        #GeomNetType = np.dtype([('Id',int), 
        #        ('time',int), 
        #           ('p',float,(1,3)),
        #           ('v',float,(1,3)),
        #           ('a',float,(1,3))])
        Person.npers +=1
        Process.__init__(self,name='Person_ID'+str(ID),sim=sim)
        self.ID=ID
        self.color=color
        self.pdshow=pdshow
        self.L = L 
        self.world = wld
        self.interval = interval
        self.manager = None
        self.manager_args = []
        self.waypoints = []
        self.moving=moving
        # random.seed(seed)
        
        if roomId < 0:
            try :
                self.roomId   = random.sample(self.L.Gr.nodes(),1)[0]
            except:
                raise NameError('This error is due to the lack of Gr graph in the Layout argument passed to Person(Object)')
        else:
            self.roomId    = roomId
        self.forbidroomId = froom
        self.cdest = cdest # choose tdestination type
        if self.cdest == 'random':
            # self.nextroomId   = int(np.floor(random.uniform(0,self.L.Gr.size())))
            try :
                self.nextroomId   = random.sample(self.L.Gr.nodes(),1)[0]
            except:
                raise NameError('This error is due to the lack of Gr graph in the Layout argument passed to Person(Object)')
            while self.nextroomId == self.roomId or (self.nextroomId in self.forbidroomId): # or (self.nextroomId in self.sim.roomlist): # test destination different de l'arrive
                # self.nextroomId   = int(np.floor(random.uniform(0,self.L.Gr.size())))
                self.nextroomId   = random.sample(self.L.Gr.nodes(),1)[0]
            #self.sim.roomlist.append(self.nextroomId) # list of all destiantion of all nodes in object sim
        elif self.cdest == 'file':
           cfg = ConfigParser.ConfigParser()
           cfg.read(pyu.getlong('nodes_destination.ini','ini'))
           self.room_seq=eval(dict(cfg.items(self.ID))['room_seq'])
           self.room_wait=eval(dict(cfg.items(self.ID))['room_wait'])
           print( 'WARNING: when nodes_destination ini file is read:')
           print( '1) the room initialization starts in the first room of the list, not in the room configured in agent.ini')
           print( '2) forbiden rooms are neglected')
           self.room_counter=1
           self.nb_room=len(self.room_seq)
           self.roomId=self.room_seq[0]
           self.nextroomId=self.room_seq[self.room_counter]
           self.wait=self.room_wait[self.room_counter]
        #self.sim.roomlist.append(self.nextroomId) # list of all destiantion of all nodes in object sim

        self.rooms, self.wp =  self.L.waypointGw(self.roomId,self.nextroomId)
        # self.dlist =  [i in self.L.Gw.ldo for i in self.rooms]
        for tup in self.wp[1:]:
                self.waypoints.append(vec3(tup))
        try:
            self.position = vec3(L.Gr.pos[self.roomId][0],L.Gr.pos[self.roomId][1])
        except:
            self.position = vec3()
#           self.old_pos = vec3()
        self.stuck = 0
        self.destination = self.waypoints[0]
        self.arrived_in = False
        self.velocity = vec3()
        self.acceleration = vec3()
        self.localx = vec3(1, 0)
        self.localy = vec3(0, 1)
        self.world.add_boid(self)

        # from Helbing, et al "Self-organizing pedestrian movement"
        maxspeed = 0.8
        self.max_speed = maxspeed#random.normalvariate(maxspeed, 0.1)
        self.desired_speed = maxspeed
        self.radius = self.average_radius#random.normalvariate(self.average_radius, 0.025) / 2
        self.intersection = vec3()
        self.arrived = False 
        self.endpoint = False 
        self.behaviors = []
        self.steering_mind = default_steering_mind
        self.cancelled = 0
        self.net=net
        self.wait=wait
        self.df = pd.DataFrame(columns=['t','x','y','vx','vy','ax','ay'])
        self.df._metadata = self.ID
        self.save=save



        if 'mysql' in self.save:
           config = ConfigParser.ConfigParser()
           config.read(pyu.getlong('simulnet.ini','ini'))
           sql_opt = dict(config.items('Mysql'))
           self.db = Database(sql_opt['host'],sql_opt['user'],sql_opt['passwd'],sql_opt['dbname'])
           self.date = datetime.datetime.now()

    def __repr__(self):
        s = 'Mechanical information\n***********************\n'
        s = s + 'agent ID: ' + str(self.ID) +'\n'
        s = s + 'color: ' + str(self.color) +'\n'

        s = s + '\nposition: ' + str(conv_vecarr(self.position)) +'\n'
        s = s + 'velocity: ' + str(conv_vecarr(self.velocity)) +'\n'
        s = s + 'acceleration: ' + str(conv_vecarr(self.acceleration)) +'\n'

        s = s + '\nOriginal room ID --->' + ' Current room ID ' +'---> Destination room ID\n'
        s = s + str(self.roomId).ljust(16) +' ---> '+\
              str(self.L.pt2ro(self.position)).ljust(16) +'---> ' + str(self.nextroomId)
        s = s + '\ncurrent waypoint ID :' + str(self.rooms[0])
        s = s + '\nremaining waypoint ID :' + str(self.rooms)
        s = s + '\npos destination room ID: ' + str(conv_vecarr(self.destination))
        s = s + '\nforbiden room list: ' + str(self.forbidroomId)
        return s





    def move(self):
        """ Move the Person

        """
        if self.pdshow:
            fig =plt.gcf()
            fig,ax=self.L.showG('w',labels=False,alphacy=0.,edges=False,fig=fig)
            plt.draw()
            plt.ion()
        while True:
            if self.moving:
                if self.sim.verbose:
                    print('meca: updt ag ' + self.ID + ' @ ',self.sim.now())

                # if np.allclose(conv_vecarr(self.destination)[:2],self.L.Gw.pos[47]):
                #     import ipdb
                #     ipdb.set_trace()


                while self.cancelled:
                    yield passivate, self
                    print("Person.move: activated after being cancelled")
                checked = []
                for zone in self.world.zones(self):
                    if zone not in checked:
                        checked.append(zone)
                        zone(self)

                # updating acceleration
                acceleration = self.steering_mind(self)
                acceleration = acceleration.truncate(self.max_acceleration)
                self.acceleration = acceleration

                # updating velocity
                velocity = self.velocity + acceleration * self.interval
                self.velocity = velocity.truncate(self.max_speed)


                if velocity.length() > 0.2:
                    # record direction only when we've really had some
                    self.localy = velocity.normalize()
                    self.localx = vec3(self.localy.y, -self.localy.x)

                # updating position
                self.position = self.position + self.velocity * self.interval
#                self.update()
                self.position.z=0
                self.world.update_boid(self)

                self.net.update_pos(self.ID,conv_vecarr(self.position),self.sim.now())
                p=conv_vecarr(self.position).reshape(3,1)
                v=conv_vecarr(self.velocity).reshape(3,1)
                a=conv_vecarr(self.acceleration).reshape(3,1)

                # fill panda dataframe 2D trajectory
                self.df = self.df.append(pd.DataFrame({'t':pd.Timestamp(self.sim.now(),unit='s'),
                'x':p[0],
                'y':p[1],
                'vx':v[0],
                'vy':v[1],
                'ax':a[0],
                'ay':a[1]},
                columns=['t','x','y','vx','vy','ax','ay']))

                if self.pdshow:
                    ptmp =np.array([p[:2,0],p[:2,0]+v[:2,0]])

                    if hasattr(self, 'pl'):
                        self.pl[0].set_data(self.df['x'].tail(1),self.df['y'].tail(1))
                        self.pla[0].set_data(ptmp[:,0],ptmp[:,1])
                        circle= plt.Circle((self.df['x'].tail(1),self.df['y'].tail(1)),radius = self.radius,alpha=0.3)
                        ax.add_patch(circle)
                    else :
                        self.pl = ax.plot(self.df['x'].tail(1),self.df['y'].tail(1),'o',color=self.color,ms=self.radius*10)
                        self.pla = ax.plot(ptmp[:,0],ptmp[:,1],'r')
                        circle= plt.Circle((self.df['x'].tail(1),self.df['y'].tail(1)),radius = self.radius,alpha=0.3)
                        ax.add_patch(circle)
                    # try:
                    #     fig,ax=plu.displot(p[:2],p[:2]+v[:2],'r')
                    # except:
                    #     pass
                    # import ipdb
                    # ipdb.set_trace()
                    plt.draw()
                    plt.pause(0.0001) 
                if 'mysql' in self.save:
                    self.db.writemeca(self.ID,self.sim.now(),p,v,a)

                if 'txt' in self.save:
                    pyu.writemeca(self.ID,self.sim.now(),p,v,a)

                # new target when arrived in poi

                if self.arrived and\
                    (self.L.pt2ro(self.position) ==\
                        self.L.Gw.node[self.rooms[1]]['room']):

                    self.arrived = False
                    if self.endpoint:
                        self.endpoint=False
                        self.roomId = self.nextroomId
                        # remove the remaining waypoint which correspond 
                        # to current room position
                        del self.waypoints[0]
                        del self.rooms[0]
                        # del self.dlist[0]
                    #
                    # If door lets continue 
                    #
                    #
                    # ig destination --> next room
                    #
                    #adjroom  = self.L.Gr.neighbors(self.roomId)
                    #Nadjroom = len(adjroom)
                        if self.cdest == 'random':
                            # self.nextroomId   = int(np.floor(random.uniform(0,self.L.Gr.size())))
                            self.nextroomId   = random.sample(self.L.Gr.nodes(),1)[0]
                            # test 1 ) next != actualroom
                            #      2 ) nextroom != fordiden room
                            #      3 ) room not share without another agent
                            while self.nextroomId == self.roomId or (self.nextroomId in self.forbidroomId):# or (self.nextroomId in self.sim.roomlist):
                                # self.nextroomId   = int(np.floor(random.uniform(0,self.L.Gr.size())))
                                self.nextroomId   = random.sample(self.L.Gr.nodes(),1)[0]
                        elif self.cdest == 'file':
                           self.room_counter=self.room_counter+1
                           if self.room_counter >= self.nb_room:
                                self.room_counter=0
                           self.nextroomId=self.room_seq[self.room_counter]
                           self.wait=self.room_wait[self.room_counter]
                        #self.sim.roomlist.append(self.nextroomId) # list of all destiantion of all nodes in object sim
                        self.rooms, wp =  self.L.waypointGw(self.roomId,self.nextroomId)
                        # self.dlist =  [i in self.L.Gw.ldo for i in self.rooms]
                        for tup in wp[1:]:
                            self.waypoints.append(vec3(tup)) 
                    #nextroom = adjroom[k]
                    #    print "room : ",self.roomId
                    #    print "nextroom : ",self.nextroomId
                    #p_nextroom = self.L.Gr.pos[self.nextroomId]
                    #setdoors1  = self.L.Gr.node[self.roomId]['doors']
                    #setdoors2  = self.L.Gr.node[nextroom]['doors']
                    #doorId     = np.intersect1d(setdoors1,setdoors2)[0]
                    #
                    # coord door
                    #
                    #unode = self.L.Gs.neighbors(doorId)
                    #p1    = self.L.Gs.pos[unode[0]]
                    #p2    = self.L.Gs.pos[unode[1]]
                    #print p1
                    #print p2
                    #pdoor = (np.array(p1)+np.array(p2))/2
                        self.destination = self.waypoints[0]

                        if self.sim.verbose:
                            print('meca: ag ' + self.ID + ' wait ' + str(self.wait) ) 
                        yield hold, self, self.wait

                    else:
                        del self.waypoints[0]
                        del self.rooms[0]
                        # del self.dlist[0]
                    #print "wp : ", self.waypoints
                        if len(self.waypoints)==1:
                            self.endpoint=True
                        self.destination = self.waypoints[0]
                    #print "dest : ", self.destination
                else:
                    yield hold, self, self.interval
            else:
#                self.update()
                self.world.update_boid(self)
                self.net.update_pos(self.ID,conv_vecarr(self.position),self.sim.now())

                yield hold, self, self.interval

    def delete(self):
        """
            delete boid from world.tk
        """
        tk = self.world.tk
        tk.canvas.delete(self.graphic)
        self.world.remove_boid(self)
        self.cancelled = 1

#    def update(self):
#        tk = self.world.tk
#        if tk is None: return
#        if not hasattr(self, 'graphic'):
#            self.graphic = tk.canvas.create_polygon(0, 0, 0, 1, 1, 1, 1, 0, smooth=True, fill='red', outline='black', tag='person')
#            if tk.collision_vectors:
#                self.graphic_front_collision = tk.canvas.create_line(0, 0, 1, 0, fill='white')
#                self.graphic_left_collision = tk.canvas.create_line(0, 0, 1, 0, fill='white')
#                self.graphic_right_collision = tk.canvas.create_line(0, 0, 1, 0, fill='white')
#                self.graphic_intersection = tk.canvas.create_oval(0, 0, 1, 1, fill='red')
#                self.graphic_intersection_normal = tk.canvas.create_line(0, 0, 1, 1, fill='red')
#            if tk.vectors:
#                self.graphic_velocity = tk.canvas.create_line(0, 0, 1, 0, fill='green')
#                self.graphic_acceleration = tk.canvas.create_line(0, 0, 1, 0, fill='blue')
#        x_, y_ = tk.x_, tk.y_
#        position = self.position
#        width, depth = self.localx * (self.radius), self.localy * (self.radius * 0.65)
#        ul = position - depth + width
#        ur = position + depth + width
#        lr = position + depth - width
#        ll = position - depth - width
#        tk.canvas.coords(self.graphic,
#                 x_(ul.x), y_(ul.y), x_(ur.x), y_(ur.y),
#                 x_(lr.x), y_(lr.y), x_(ll.x), y_(ll.y))
#        tk.canvas.create_line(x_(ur.x),y_(ur.y),x_(ul.x),y_(ul.y))




#        if tk.vectors:
#            xx, yy, unused_z = position
#            velocity = self.velocity
#            tk.canvas.coords(self.graphic_velocity,
#                     x_(xx), y_(yy), x_(xx + velocity.x), y_(yy + velocity.y))
#            acceleration = self.acceleration
#            tk.canvas.coords(self.graphic_acceleration,
#                     x_(xx), y_(yy), x_(xx + acceleration.x), y_(yy + acceleration.y))
#        if tk.collision_vectors:
#            xx, yy, unused_z = position
#            speed = self.velocity.length()
#            front_check = 0.5 + speed * 1.5
#            side_check = 0.5 + speed * 0.5
#            point = self.localy.scale(front_check)
#            tk.canvas.coords(self.graphic_front_collision,
#                     x_(xx), y_(yy), x_(xx + point.x), y_(yy + point.y))
#            point = (self.localy + self.localx).scale(side_check)
#            tk.canvas.coords(self.graphic_left_collision,
#                     x_(xx), y_(yy), x_(xx + point.x), y_(yy + point.y))
#            point = (self.localy - self.localx).scale(side_check)
#            tk.canvas.coords(self.graphic_right_collision,
#                     x_(xx), y_(yy), x_(xx + point.x), y_(yy + point.y))
#            if self.intersection:
#            xx, yy, unused_z = self.intersection
#            tk.canvas.coords(self.graphic_intersection,
#                     x_(xx-0.2), y_(yy-0.2), x_(xx + 0.2), y_(yy + 0.2))
#            point = self.intersection_normal
#            tk.canvas.coords(self.graphic_intersection_normal,
#                     x_(xx), y_(yy), x_(xx + point.x), y_(yy + point.y))
#            else:
#            tk.canvas.coords(self.graphic_intersection,
#                     0, 0, 0, 0)
#            tk.canvas.coords(self.graphic_intersection_normal,
#                     0, 0, 0, 0)
#        tk.canvas.lower(self.graphic, 'vehicle')




