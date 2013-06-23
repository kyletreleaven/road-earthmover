
import itertools
import random

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

import pydot


from basicsim.signaling import Signal, Message



def get_sim_setting() :
    g = nx.erdos_renyi_graph( 10, .3 )
    g = nx.connected_component_subgraphs( g )[0]
    
    roadnet = nx.MultiDiGraph()
    
    def roadmaker() :
        for i in itertools.count() : yield 'road%d' % i, np.random.exponential()
    road_iter = roadmaker()
    
    for i, ( u,v,data ) in enumerate( g.edges_iter( data=True ) ) :
        label, length = road_iter.next()
        roadnet.add_edge( u, v, label, length=length )
    
    
    rates = nx.DiGraph()
    ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
    for i in range(5) :
        r1 = random.choice( ROADS )
        r2 = random.choice( ROADS )
        if not rates.has_edge( r1, r2 ) :
            rates.add_edge( r1, r2, rate=0. )
        
        data = rates.get_edge_data( r1, r2 )
        data['rate'] += .25 * (1./5) * np.random.exponential()
        
    return roadnet, rates







class Vehicle :
    def __init__(self, dispatch ) :
        self.dispatch = dispatch
        self.ready = Signal()
        
    def join_sim(self, sim ) :
        self.sim = sim
        self.sim.schedule( self.ready_at )
        
        
    def set_environment(self, f_dist ) :
        self.f_dist = f_dist
        
    def set_location(self, location ) :
        self.location = location
        
    """ signaloid """
    def ready_at(self) : self.ready( self.location )
        
    """ slot """
    def receive_demand(self, demand ) :
        p, q = demand
        time = self.sim.get_time()
        print 'got demand at %f: (%s, %s)' % ( time, repr(p), repr(q) )
        
        self.pick = p ; self.delv = q
        
        dist_curr_to_pick = self.f_dist( self.location, p )
        print 'moving to pickup, there in %f' % dist_curr_to_pick
        self.sim.schedule( self.arrived_at_pickup, dist_curr_to_pick )
        
    """ auto slot """
    def arrived_at_pickup(self) :
        self.location = self.pick
        time = self.sim.get_time()
        print 'arrived to pickup at %f' % time
        
        q = self.delv
        dist_pick_to_delv = self.f_dist( self.location, q )
        print 'moving to delivery, there in %f' % dist_pick_to_delv
        self.sim.schedule( self.delivered, dist_pick_to_delv )
        
    """ auto slot """
    def delivered(self) :
        time = self.sim.get_time()
        print 'delivered at %f' % time
        self.ready_at()





if __name__ == '__main__' :
    import roadEMD_git.roadmap_basic as ROADS
    
    from basicsim.simulation import Simulation
    from sources import RoadnetDemandSource 
    from queues import NNeighDispatcher
    
    roadnet, rates = get_sim_setting()
    
    sim = Simulation()
    
    rnet_demands = RoadnetDemandSource( roadnet, rates )
    rnet_demands.join_sim( sim )
    
    f_dist = lambda p, q : ROADS.distance( roadnet, p, q, 'length' )
    
    dispatch = NNeighDispatcher()
    dispatch.join_sim( sim )
    
    veh = Vehicle( dispatch )
    veh.join_sim( sim )
    
    dispatch.set_environment( f_dist )
    veh.set_environment( f_dist )
    
    def randomaddress( roadnet, length='length' ) :
        _,__,road,data = random.choice( roadnet.edges( keys=True, data=True ) )
        roadlen = data.get(length,1)
        y = roadlen * np.random.rand()
        return ROADS.RoadAddress(road,y)
    
    randpoint = randomaddress( roadnet )
    veh.set_location( randpoint )
    
    """ signal connections """
    
    interface = dispatch.spawn_interface()
    veh.ready.connect( interface.request_in )
    interface.demand_out.connect( veh.receive_demand )
    
    """ source -> dispatch adapter """
    def give_to_dispatch( dem ) :
        p, q = dem
        loc = p
        dispatch.demand_arrived( dem, loc )
        
    rnet_demands.source().connect( give_to_dispatch )
    
    class data : pass
    timer = data()
    timer.last_time = sim.time
    def say( dem ) :
        p, q = dem
        new_time = sim.time
        elapsed = new_time - timer.last_time
        print 'tick, %f: %s, %s' % ( elapsed, repr(p), repr(q) )
        timer.last_time = new_time
        
    rnet_demands.source().connect( say )
    
    
    for i in range(20) :
        call = sim.get_next_action()
        call()
        
        
    
    
