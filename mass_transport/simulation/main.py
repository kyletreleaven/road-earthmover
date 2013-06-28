
# builtin
import itertools
import random

# science common
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx

# dev
from signaling import Signal, Message


""" simulation object definitions """







""" convenient constructors """

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








if __name__ == '__main__' :
    import mass_transport
    import mass_transport.tests.testcases as testcases
    
    import roadgeometry.roadmap_basic as ROAD
    import roadgeometry.probability as roadprob
    
    from mass_transport import road_complexity
    
    import mass_transport.road_complexity as mcplx
    
    # make the roadnet and rategraph
    
    #roadnet, rates = get_sim_setting()
    
    roadnet = testcases.RoadnetExamples.get( 'nesw' )
    normrategraph = nx.DiGraph()
    normrategraph.add_edge( 'N', 'E', rate=1./5 )
    normrategraph.add_edge( 'W', 'E', rate=1./5 )
    normrategraph.add_edge( 'W', 'S', rate=3./5 )
    # Note: rates sum to 1.
    
    # compute max rate
    MM = road_complexity.MoversComplexity( roadnet, normrategraph )
    max_rate = 1. / MM
    arrivalrate = max_rate * 3.     # having some issues right now
    
    rategraph = nx.DiGraph()
    for r1, r2, data in normrategraph.edges_iter( data=True ) :
        rategraph.add_edge( r1, r2, rate=arrivalrate * data.get('rate') )
        
    # construct the simulation blocks
    from simulation import Simulation
    from sources import RoadnetDemandSource
    from queues import NNeighDispatcher
    from servers import Vehicle
    
    sim = Simulation()
    
    source = RoadnetDemandSource( roadnet, rategraph )
    source.join_sim( sim )
    
    f_dist = lambda p, q : ROAD.distance( roadnet, p, q, 'length' )
    
    dispatch = NNeighDispatcher()
    dispatch.set_environment( f_dist )
    dispatch.join_sim( sim )
    
    veh = Vehicle()
    veh.set_environment( f_dist )
    randpoint = roadprob.sampleaddress( roadnet, 'length' )
    veh.set_location( randpoint )
    veh.join_sim( sim )
    
    # connect components in simulation schematic
    """ signal connections """
    
    vehconn = dispatch.spawn_interface()
    veh.ready.connect( vehconn.request_in )
    vehconn.demand_out.connect( veh.receive_demand )
    
    """ source -> dispatch adapter """
    class keepcount() :
        def __init__(self) :
            self.count = 0
            
        def increment(self, *args, **kwargs ) :
            self.count += 1
            
    counting = keepcount()
    
    def give_to_dispatch( dem ) :
        p, q = dem
        loc = p
        dispatch.demand_arrived( dem, loc )
        
    source_out = source.source()
    source_out.connect( counting.increment )
    source_out.connect( give_to_dispatch )
    #source.source().connect( give_to_dispatch )
    
    class data : pass
    timer = data()
    timer.last_time = sim.time
    def say( dem ) :
        p, q = dem
        new_time = sim.time
        elapsed = new_time - timer.last_time
        print 'tick, %f: %s, %s' % ( elapsed, repr(p), repr(q) )
        timer.last_time = new_time
        
    source.source().connect( say )
    
    horizon = 1000.
    while sim.get_time() < horizon :
        call = sim.get_next_action()
        call()
        
        
    print 'arrival rate (simulated, empirical): %f, %f' % ( arrivalrate, counting.count / horizon )
    
    nleft = len( dispatch.demands )
    overrate_est = float( nleft ) / horizon
    max_rate_observed = arrivalrate - overrate_est
    
    if nleft >= 0 : 
        print 'max sustainable rate, observed): %f' % max_rate_observed
    print 'max sustainable rate (predicted): %f' % max_rate
    
    T = 10.
    demands = mcplx.sample_demands( T, rategraph, roadnet )
    min_total_velocity = mcplx.enroute_cost( demands, roadnet ) / T + mcplx.balance_cost( demands, roadnet ) / T
    print 'empirical expected max rate: %f' % ( 1. / min_total_velocity )
    
    
    
