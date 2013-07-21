
# builtin
import itertools
import random

# science common
import numpy as np
import scipy as sp
import matplotlib.pyplot as plt
import networkx as nx

# dev
from signaling import Signal, Message


""" simulation object definitions """

class UniformPoller :
    def __init__(self, T ) :
        self.T = T
        self._counter = itertools.count()
        
        self.tape = []
        
    def set_query(self, callback ) :
        self.callback = callback
        
    def join_sim(self, sim ) :
        self.sim = sim
        self.sim.schedule( self.tick )
        
    """ auto slot """
    def tick(self) :
        amount = self.callback()
        self.tape.append( amount )
        self.sim.schedule( self.tick, self.T )




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
    import mass_transport.probability as massprob
    
    import roadgeometry.roadmap_basic as ROAD
    import roadgeometry.probability as roadprob
    
    from mass_transport import road_complexity
    
    import mass_transport.road_complexity as mcplx
    
    # make the roadnet and rategraph
    
    #roadnet, rates = get_sim_setting()
    """ SIM PARAMETERS """
    if True :
        roadnet = testcases.RoadnetExamples.get( 'nesw' )
        roadset = [ road for _,__,road in roadnet.edges_iter( keys=True ) ]
        
        normrategraph = nx.DiGraph()
        # is it a "true zero" issue?
        if False :
            for road1, road2 in itertools.product( roadset, roadset ) :
                normrategraph.add_edge( road1, road2, rate=.001 )
        # add the meaningful rates
        normrategraph.add_edge( 'N', 'E', rate=1./5 )
        normrategraph.add_edge( 'W', 'E', rate=1./5 )
        normrategraph.add_edge( 'W', 'S', rate=3./5 )
    
    elif False :
        roadnet = roadprob.sampleroadnet()
        normrategraph = massprob.sample_rategraph( roadnet, normalize=True )
        
    else :
        roadnet = nx.MultiDiGraph()
        roadnet.add_edge( 0,1, 'LEFT', length=1. )
        roadnet.add_edge( 1,2, 'RIGHT', length=1. )
        normrategraph = nx.DiGraph()
        normrategraph.add_edge( 'LEFT', 'RIGHT', rate=1. )
        
    numveh = 1      # DEBUG: for some reason, multiple vehicles is a no-no?!?
    vehspeed = 1.
    
    horizon = 10000.
        
    """ end parameters """
        
    """ derived parameters """
    # the function which will be used by various components to compute distances
    f_dist = lambda p, q : ROAD.distance( roadnet, p, q, 'length' )

    # Note: rates sum to 1.
    # compute necessary "service velocity"
    demvel_enroute = road_complexity.demand_enroute_velocity( roadnet, normrategraph )
    demvel_balance = road_complexity.demand_balance_velocity( roadnet, normrategraph )
    #
    MM = road_complexity.MoversComplexity( roadnet, normrategraph )
    max_rate = numveh * vehspeed / MM
    #arrivalrate = max_rate * 1. + 1.
    #arrivalrate = max_rate * .99 + 0.
    arrivalrate = max_rate * 1. + .1
    
    rategraph = nx.DiGraph()
    for r1, r2, data in normrategraph.edges_iter( data=True ) :
        rategraph.add_edge( r1, r2, rate=arrivalrate * data.get('rate') )



    
    """ end derived parameters """
    
    
    
    """ simulation setup """
    # construct the simulation blocks
    from simulation import Simulation
    from sources import RoadnetDemandSource
    from queues import GatedQueue, BatchNNeighDispatcher 
    from servers import Vehicle
    
    sim = Simulation()
    
    source = RoadnetDemandSource( roadnet, rategraph )
    source.join_sim( sim )
    
    gate = GatedQueue()
    gate.join_sim( sim )
    
    dispatch = BatchNNeighDispatcher()
    # dispatch = NNeighDispatcher()
    dispatch.set_environment( roadnet )
    dispatch.join_sim( sim )
    
    """ add some demands to jump-start the simulation """
    preload = 0
    distr = {}
    for road1, road2, rate_data in normrategraph.edges_iter( data=True ) :
        distr[(road1,road2)] = rate_data.get( 'rate', 0. )
    bonus_demands = [ roadprob.samplepair( roadnet, distr ) for i in range(preload) ]
    for p, q in bonus_demands : gate.demand_arrived( (p,q) )
    """ end cheats """
    
    vehicles = {}
    for k in range( numveh ) :
        veh = Vehicle() ; vehicles[ veh ] = None
        veh.set_environment( f_dist )
        veh.set_speed( vehspeed )
        randpoint = roadprob.sampleaddress( roadnet, 'length' )
        veh.set_location( randpoint )
        veh.join_sim( sim )
    
    # connect components in simulation schematic
    """ source output connections """    
    # report demand arrivals to several places
    ALL_DEMANDS = []
    def record_arrival( dem ) :
        ALL_DEMANDS.append( dem )
    
    def give_to_dispatch( dem ) :
        p, q = dem
        loc = p
        #dispatch.demand_arrived( dem, loc )
        gate.demand_arrived( dem )
        
    source_out = source.source()
    #source_out.connect( counting.increment )
    source_out.connect( give_to_dispatch )
    source_out.connect( record_arrival )
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
        
    source_out.connect( say )
    
    gate_if = gate.spawn_interface()
    dispatch.request_batch.connect( gate_if.request_in )
    gate_if.batch_out.connect( dispatch.batch_arrived )
    
    """ vehicle signal connections """
    for veh in vehicles :
        vehconn = dispatch.spawn_interface() ; vehicles[veh] = vehconn
        veh.ready.connect( vehconn.request_in )
        #veh.ready.connect( vehconn.request_in )
        vehconn.demand_out.connect( veh.receive_demand )

    
    record_interval = 1.
    recorder = UniformPoller( record_interval )
    unserviced_query = lambda : len( gate.demands ) + len( dispatch.demands )
    recorder.set_query( unserviced_query )
    recorder.join_sim( sim )
    
    
    """ run the simulation """
    while sim.get_time() < horizon :
        call = sim.get_next_action()
        call()
        
        
        
    """ COMPUTE STATISTICS """
    total_demands = len( ALL_DEMANDS )
    nleft = len( dispatch.demands )
    print 'arrival rate (simulated, observed): %f, %f' % ( arrivalrate, total_demands / horizon )
    
    #overrate_est = float( nleft - preload ) / horizon
    take_only_last = int( .25 * horizon )
    overrate_est = float( recorder.tape[-1] - recorder.tape[-take_only_last] ) / take_only_last
    overrate_est = float( recorder.tape[-1] ) / horizon
    max_rate_observed = arrivalrate - overrate_est
    
    if nleft >= 0 : 
        print 'max sustainable rate (observed): %f' % max_rate_observed
    print 'max sustainable rate (predicted): %f' % max_rate
    
    print 'cost per demand (predicted): %f' % ( demvel_enroute + demvel_balance )
    print 'cost per demand (observed): %f' % ( veh.odometer / veh.notches )
    
    
    DEMS = {}
    for dem in ALL_DEMANDS :
        p, q = dem
        road1 = p.road
        road2 = q.road
        row = DEMS.setdefault( (road1,road2), [] )
        row.append( dem )
        
    empirical_distr = [ ( key, len( val ) / horizon ) for key, val in DEMS.items() ]
    
    
    num_steps = len( recorder.tape )
    time_axis = record_interval * np.arange( num_steps )
    (slope,intercept) = sp.polyfit( time_axis, recorder.tape, 1 )
    
    
    #
    Ed_computed = road_complexity.demand_enroute_velocity( roadnet, normrategraph )
    #EMD_domain_knowledge = 31./6 / 5
    #MMM = Ed_computed + EMD_domain_knowledge
    #max_rate_domain_knowledge = numveh * vehspeed / MMM
    #print 'max rate (domain knowledge): %f' % max_rate_domain_knowledge
    
    
    if False :
        # do matching-based checking
        T = 1.
        demands = mcplx.sample_demands( T, normrategraph, roadnet )
        min_total_velocity = mcplx.enroute_cost( demands, roadnet ) / T + mcplx.balance_cost( demands, roadnet ) / T
        print 'empirical expected max rate: %f' % ( 1. / min_total_velocity )
    
    
    
    
    
