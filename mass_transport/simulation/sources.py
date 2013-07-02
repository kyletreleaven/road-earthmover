
import numpy as np
from signaling import Signal, Message

# dev
import mass_transport
import roadgeometry.roadmap_basic as ROAD
import roadgeometry.probability as roadprob



class PoissonClock(object) :
    
    def __init__(self, rate=1. ) :
        self.rate = rate
        self._output = Signal()
        
    def _reschedule(self) :
        tau = np.random.exponential( 1. / self.rate )
        self.sim.schedule( self.tick, tau )
        
    def join_sim(self, sim ) :
        self.sim = sim
        self._reschedule()
        
    def tick(self) :
        self._output()
        self._reschedule()
        
    def source(self) :
        return self._output




class RoadnetDemandSource(object) :
    def __init__(self, roadnet, rategraph, length_key='length', rate_key='rate' ) :
        self.roadnet = roadnet
        self.length_key = length_key
        #self.rates = rates
        
        """ state vars """
        #self.clocks = {}
        self.clocks = set()
        
        """ signal """
        self.output = Signal()
        
        for r1, r2, data in rategraph.edges_iter( data=True ) :
            rate = data.get( rate_key, 0. )
            if rate <= 0. : continue
            
            clock = PoissonClock( rate )
            msg = Message( self.emit_point, r1, r2 )
            clock.source().connect( msg )
            
            self.clocks.add( clock )
            
            
    def join_sim(self, sim ) :
        self.sim = sim
        for clock in self.clocks :
            clock.join_sim( sim )
            
    """ auto slotoid """
    def emit_point(self, road1, road2 ) :
        #_, data1 = ROAD.obtain_edge( self.roadnet, road1, data_flag=True )
        #_, data2 = ROAD.obtain_edge( self.roadnet, road2, data_flag=True )
        
        p = roadprob.sample_onroad( road1, self.roadnet )
        q = roadprob.sample_onroad( road2, self.roadnet )
        
        self.output( (p,q) )
        
        
    def source(self) : return self.output



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







