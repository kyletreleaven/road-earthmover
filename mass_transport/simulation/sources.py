
import numpy as np
import networkx as nx

from spatialq_basic.sources.basic import PoissonClock

import roadEMD_git.roadmap_basic as ROAD
import roadEMD_git.roademd as road_EMD
import roadEMD_git.road_Ed as road_Ed
from basicsim.signaling import Signal




class RoadnetDemandSource(object) :
    def __init__(self, roadnet, rates, length_key='length', rate_key='rate' ) :
        self.roadnet = roadnet
        self.rates = rates
        self.length_key = length_key
        
        self.output = Signal()
        self.clocks = {}
        
        class PointEmitter :
            def __init__(self, source, road1, road2 ) :
                self.source = source
                self.road1 = road1
                self.road2 = road2
                
            def emit(self) :
                self.source.emit_point( self.road1, self.road2 )
        
        for r1, r2, data in rates.edges_iter( data=True ) :
            rate = data.get( rate_key, 0. )
            if rate <= 0. : continue
            clock = PoissonClock( rate )
            
            emitter = PointEmitter( self, r1, r2 )
            
            clock.source().connect( emitter.emit )
            self.clocks[ clock ] = emitter
            
        
    def join_sim(self, sim ) :
        self.sim = sim
        for clock in self.clocks :
            clock.join_sim( sim )
                    
            
    def report_clock(self, clock ) :
        print clock
            
    def emit_point(self, road1, road2 ) :
        _, data1 = ROAD.obtain_edge( self.roadnet, road1, data_flag=True )
        _, data2 = ROAD.obtain_edge( self.roadnet, road2, data_flag=True )
        roadlen1 = data1.get( self.length_key )
        roadlen2 = data2.get( self.length_key )
        
        x = roadlen1 * np.random.rand()
        y = roadlen2 * np.random.rand()
        p = ROAD.RoadAddress( road1, x )
        q = ROAD.RoadAddress( road2, y )
        
        self.output( ( p, q ) )
            
            
    def source(self) :
        return self.output
        
        





if __name__ == '__main__' :
    import itertools
    from basicsim.simulation import Simulation
    import random
    
    
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
        data['rate'] += np.random.exponential()
        
        
        
    print 'Hello.'
    
    sim = Simulation()
    rnet_demands = RoadnetDemandSource( roadnet, rates )

    class data : pass
    timer = data()
    timer.last_time = sim.time
    def say( p, q ) :
        new_time = sim.time
        elapsed = new_time - timer.last_time
        print 'tick, %f: %s, %s' % ( elapsed, repr(p), repr(q) )
        timer.last_time = new_time
        
        
    rnet_demands.source().connect( say )
    
    rnet_demands.join_sim( sim )
    
    for i in range(100) :
        call = sim.get_next_action()
        call()







