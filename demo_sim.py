
# builtin
import itertools
import random

# science common
import numpy as np
import scipy as sp

import matplotlib as mpl
mpl.rcParams['ps.useafm'] = True
mpl.rcParams['pdf.use14corefonts'] = True
mpl.rcParams['text.usetex'] = True

font = {'family' : 'normal',
        'weight' : 'bold',
        'size'   : 22 }
mpl.rc('font', **font)       # oh please, work!

import matplotlib.pyplot as plt
import networkx as nx

# dev
from setiptah.eventsim.signaling import Signal, Message
#from signaling import Signal, Message




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



class RoadmapDistance() :
    """ a function object to pass around """
    def __init__(self, roadnet ) :
        self.roadnet = roadnet
        
    def __call__(self, p, q ) :
        ROAD.distance( self.roadnet, p, q, 'length' )










if __name__ == '__main__' :
    import tempfile
    #tf = tempfile.NamedTemporaryFile(prefix="zz")
    
    import setiptah.roadearthmover.tests.testcases as testcases
    import setiptah.roadearthmover.probability as massprob
    #import mass_transport
    #import mass_transport.tests.testcases as testcases
    #import mass_transport.probability as massprob
    
    import setiptah.roadgeometry.roadmap_basic as ROAD
    import setiptah.roadgeometry.probability as roadprob
    #import roadgeometry.roadmap_basic as ROAD
    #import roadgeometry.probability as roadprob
    
    import setiptah.roadearthmover.road_complexity as road_complexity
    #from mass_transport import road_complexity
    
    import setiptah.roadearthmover.road_complexity as mcplx
    #import mass_transport.road_complexity as mcplx
    
    
    
    """ SIMULATION SETUP """
    
    roaddist = RoadmapDistance( roadnet )
    
    # construct the simulation blocks
    from setiptah.eventsim.simulation import Simulation
    from setiptah.roadearthmover.simulation.sources import RoadnetDemandSource
    from setiptah.roadearthmover.simulation.queues import GatedQueue, BatchNNeighDispatcher 
    from setiptah.roadearthmover.simulation.servers import Vehicle
    
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
    
    vehicles = {}       # need to hold them somewhere, or they get garbage collected
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
    
    def display() :
        n = len( recorder.tape )
        T = record_interval * np.arange( n )
        plt.plot( T, recorder.tape )
        plt.xlabel( 'Time elapsed' )
        plt.ylabel( 'Number of Demands Waiting' )
    
    
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
        
        
        