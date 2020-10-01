#   -*- coding:Utf-8 -*-
from __future__ import print_function
"""
.. currentmodule:: pylayers.simul.simulnet

.. autosummary::

"""
import doctest
import os
import glob
#####################################################################
# authors :
# Nicolas AMIOT        : nicolas.amiot@univ-rennes1.fr
# Bernard UGUEN        : bernard.uguen@univ-rennes1.fr
#####################################################################

import pkgutil
import warnings
warnings.filterwarnings('ignore')
import numpy as np
import scipy as sp
import networkx as nx
import pandas as pd
import random
from random import seed

import time
import matplotlib.pyplot as plt
import sys
if sys.version_info.major==2:
    import ConfigParser
    from simpy.SimulationRT import SimulationRT, Process, hold
else:
    import configparser as ConfigParser
    import simpy

import pylayers.util.pyutil as pyu

from pylayers.network.network import Network, Node, PNetwork
from pylayers.network.communication import Gcom
from pylayers.network.show import ShowNet, ShowTable
from pylayers.mobility.agent import Agent
from pylayers.mobility.trajectory import *
from pylayers.network.emsolver import EMSolver
from pylayers.gis.layout import Layout
from pylayers.antprop.slab import Slab
from pylayers.util.utilnet import str2bool
from pylayers.mobility.transit.World import world
#from pylayers.util.pymysqldb import Database as DB
from pylayers.util.project import *
from pylayers.util.save import *


import pdb
import os


#~class Simul(SimulationRT):  # Simpy 2
class Simul(object):  # Simpy 3
    """

    Attributes
    ----------

    config  : config parser instance
    sim_opt : dictionary of configuration option for simulation
    ag_opt : dictionary of configuration option for agent
    lay_opt : dictionary of  configuration option for layout
    meca_opt : dictionary of  configuration option for mecanic
    net_opt : dictionary of  configuration option for network
    loc_opt : dictionary of  configuration option for localization
    save_opt : dictionary of  configuration option for save
    sql_opt : dictionary of  configuration option for sql


    Parameters
    ----------

    self.lAg  : list of Agent(Object)
        list of agents involved in simulation
    self.L : Layout
        Layout used in simulation

    Note
    ----

    All the previous dictionnary are obtained from the chosen simulnet.ini file
    in the project directory

    """

    def __init__(self):

        #SimulationRT.__init__(self)  # Simpy 2
        simpy.RealtimeEnvironment.__init__(self)  #simpy 3
        #self.initialize()

        self.config = ConfigParser.ConfigParser()
        filename = pyu.getlong('simulnet.ini', pstruc['DIRSIMUL'])

        self.config.read(filename)
        self.sim_opt = dict(self.config.items('Simulation'))
        self.lay_opt = dict(self.config.items('Layout'))
        self.meca_opt = dict(self.config.items('Mechanics'))
        self.net_opt = dict(self.config.items('Network'))
        self.loc_opt = dict(self.config.items('Localization'))
        self.save_opt = dict(self.config.items('Save'))
        self.sql_opt = dict(self.config.items('Mysql'))
        self.seed = eval(self.sim_opt['seed'])

        self.traj = Trajectories()

        self.verbose = str2bool(self.sim_opt['verbose'])
        if str2bool(self.net_opt['ipython_nb_show']):
            self.verbose = False
        self.roomlist = []

        self.finish = False
        self.create()

    def __repr__(self):

        s = 'Simulation information' + '\n----------------------'
        s = s + '\nLayout: ' + self.lay_opt['filename']
        s = s + '\nSimulation duration: ' + str(self.sim_opt['duration'])
        s = s + '\nRandom seed: ' + str(self.sim_opt['seed'])
        s = s + '\nSave simulation: ' + self.save_opt['savep']

        s = s + '\n\nUpdate times' + '\n-------------'
        s = s + '\nMechanical update: ' + \
            str(self.meca_opt['mecanic_update_time'])
        s = s + '\nNetwork update: ' + str(self.net_opt['network_update_time'])
        s = s + '\nLocalization update: ' + self.net_opt['communication_mode']

        s = s + '\n\nAgents => self.lAg[i]' + '\n------'
        s = s + '\nNumber of agents :' + str(len(self.lAg))
        s = s + '\nAgents IDs: ' + \
            str([self.lAg[i].ID for i in range(len(self.lAg))])
        s = s + '\nAgents names: ' + \
            str([self.lAg[i].name for i in range(len(self.lAg))])
        s = s + '\nDestination of chosen agents: ' + \
            self.meca_opt['choose_destination']

        s = s + '\n\nNetwork' + '\n-------'
        s = s + '\nNodes per wstd: ' + str(self.net.wstd)

        s = s + '\n\nLocalization' + '\n------------'
        s = s + '\nLocalization enable: ' + self.loc_opt['localization']
        s = s + '\nPostion estimation methods: ' + self.loc_opt['method']

        return s

    def create_layout(self):
        """ create Layout in Simpy the_world thanks to Tk backend

        """

        _filename = self.lay_opt['filename']

        self.L = Layout(_filename)
        self.L.build()
        self.L.buildGr()
        self.L.buildGw()

        self.the_world = world()

        try:
            self.L.dumpr()
            print('Layout graphs are loaded from ' + basename + '/struc/ini')
        except:
            #self.L.sl = sl
            # self.L.loadGr(G1)
            print('This is the first time the layout file is used\
            Layout graphs are curently being built, it may take few minutes.')
            self.L.build()
            self.L.dumpw()

        #
        # Create Layout
        #
        walls = self.L.thwall(0, 0)
        for wall in walls:
            for ii in range(0, len(wall) - 1):
                self.the_world.add_wall(wall[ii], wall[ii + 1])

    def create_agent(self):
        """ create simulation's Agents

        ..todo:: change lAg list to a dictionnary ( modification in show.py too) 

        """

        self.lAg = []
        agents = []
        Cf = ConfigParser.ConfigParser()
        Cf.read(pyu.getlong('agent.ini', 'ini'))
        agents = eval(dict(Cf.items('used_agent'))['list'])
        for i, ag in enumerate(agents):
            ag_opt = dict(Cf.items(ag))
            self.lAg.append(
                    Agent(
                    ID=ag_opt['id'],
                    name=ag_opt['name'],
                    typ=ag_opt['typ'],
                    color=eval(ag_opt['color']),
                    pdshow=str2bool(self.meca_opt['pdshow']),
                    pos=np.array(eval(ag_opt['pos'])),
                    roomId=int(ag_opt['roomid']),
                    froom=eval(ag_opt['froom']),
                    meca_updt=float(self.meca_opt['mecanic_update_time']),
                    wait=float(ag_opt['wait']),
                    cdest=eval(self.meca_opt['choose_destination']),
                    loc=str2bool(self.loc_opt['localization']),
                    loc_updt=float(self.loc_opt['localization_update_time']),
                    loc_method=eval(self.loc_opt['method']),
                    L=self.L,
                    network=str2bool(self.net_opt['network']),
                    net=self.net,
                    epwr=dict([(eval((ag_opt['wstd']))[ep], 
                                eval((ag_opt['epwr']))[ep]) 
                                for ep in range(len(eval((ag_opt['wstd']))))]),
                    sens=dict([(eval((ag_opt['wstd']))[ep],
                                eval((ag_opt['sensitivity']))[ep]) 
                                for ep in range(len(eval((ag_opt['wstd']))))]),
                    world=self.the_world,
                    wstd=eval(ag_opt['wstd']),
                    save=eval(self.save_opt['save']),
                    gcom=self.gcom,
                    comm_mode=eval(self.net_opt['communication_mode']),
                    sim=self,
                    seed=self.seed))

    def create_EMS(self):
        """ create electromagnetic Solver object

        """
        self.EMS = EMSolver(L=self.L)

    def create_network(self):
        """ create the whole network
        """

        self.net = Network(EMS=self.EMS)
        self.gcom = Gcom(net=self.net, sim=self)

        self.create_agent()
        # create network
        if str2bool(self.net_opt['network']):
            self.net.create()

            # create All Personnal networks
            for n in self.net.nodes():
                self.net.node[n]['PN']._get_wstd()
                self.net.node[n]['PN']._get_SubNet()
            self.gcom.create()

           # create Process Network
            self.Pnet = PNetwork(net=self.net,
                                 net_updt_time=float(
                                     self.net_opt['network_update_time']),
                                 L=self.L,
                                 sim=self,
                                 show_sg=str2bool(self.net_opt['show_sg']),
                                 disp_inf=str2bool(self.net_opt['dispinfo']),
                                 save=eval(self.save_opt['save']))
            self.activate(self.Pnet, self.Pnet.run(), 0.0)

    def create_visual(self):
        """ create visual Tk process
        """

        self.visu = Updater(
            interval=float(self.sim_opt['show_interval']), sim=self)
        self.activate(self.visu, self.visu.execute(), 0.0)

    def create(self):
        """ create the simulation
            This method is called at the end of __init__

        """
        # this is to redump the database at each simulation
        if 'mysql' in self.save_opt['save']:
            if str2bool(self.sql_opt['dumpdb']):
                os.popen('mysql -u ' + self.sql_opt['user'] + ' -p ' + self.sql_opt['dbname'] +
                         '< /private/staff/t/ot/niamiot/svn2/devel/simulator/pyray/SimWHERE2.sql')

        # TODO remove the hard reference
        if 'txt' in self.save_opt['save']:
            pyu.writeDetails(self)
            if os.path.isfile(os.path.join(basename, 'output', 'Nodes.txt')):
                print('would you like to erase previous txt files ?')
                A = raw_input()
                if A == 'y':
                    for f in os.listdir(os.path.join(basename, 'output')):
                        try:
                            fi, ext = f.split('.')
                            if ext == 'txt':
                                os.remove(os.path.join(basename, 'output' + f))
                        except:
                            pass

        # Layout
        self.create_layout()
        # Electro Magnetic Simulator
        self.create_EMS()
        # Network
        self.create_network()

        if str2bool(self.sim_opt['showtk']):
            self.create_visual()
        self.create_show()

        if str2bool(self.save_opt['savep']):
            self.save = Save(L=self.L, net=self.net, sim=self)
            self.activate(self.save, self.save.run(), 0.0)

    def create_show(self):
        """ create a vizualization
        """

        plt.ion()
        fig_net = 'network'
        fig_table = 'table'

        if str2bool(self.net_opt['show']):
            if str2bool(self.net_opt['ipython_nb_show']):
                notebook = True
            else:
                notebook = False
            self.sh = ShowNet(net=self.net, L=self.L, sim=self,
                              fname=fig_net, notebook=notebook)
            self.activate(self.sh, self.sh.run(), 1.0)

        if str2bool(self.net_opt['show_table']):
            self.sht = ShowTable(net=self.net, lAg=self.lAg,
                                 sim=self, fname=fig_table)
            self.activate(self.sht, self.sht.run(), 1.0)

    def savepandas(self):
        """ save mechanics in pandas hdf5 format
        """
        filename = pyu.getlong(
            eval(self.sim_opt["filename"]), pstruc['DIRNETSAVE'])
        layfile = self.L._filename.split('.')[0]
        store = pd.HDFStore(filename + '_' + layfile + '.h5', 'w')
        for a in self.lAg:

            if a.typ != 'ap':
                store.put(a.ID, a.meca.df.convert_objects())

            else:  # if agent acces point, its position is saved
                store.put(a.ID, a.posdf)

            store.get_storer(a.ID).attrs.typ = a.typ
            store.get_storer(a.ID).attrs.name = a.name
            store.get_storer(a.ID).attrs.ID = a.ID
            store.get_storer(a.ID).attrs.layout = self.L._filename
        # saving metadata
        store.root._v_attrs.attributes=self.sim_opt
        store.close()
        self.traj.loadh5(
            eval(self.sim_opt["filename"]) + '_' + layfile + '.h5')





    def runsimul(self):
        """ run simulation
        """

        if not self.finish:
            # random number seed
            seed(self.seed)
            self.simulate(until=float(self.sim_opt['duration']),
                          real_time=True,
                          rel_speed=float(self.sim_opt['speedratio']))

            self.the_world._boids = {}

            # if str2bool(self.save_opt['savep']):
            # print 'Processing save results, please wait'
            # self.save.mat_export()

            if str2bool(self.save_opt['savepd']):
                self.savepandas()
            self.finish = True
        else:
            raise NameError('Reinstantiate a new simul object to run again')

if __name__ == '__main__':

    S = Simul()
    S.runsimul()
