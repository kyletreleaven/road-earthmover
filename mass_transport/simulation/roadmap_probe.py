
# built-in
import itertools
import random

# science common
import numpy as np
import scipy as sp
import networkx as nx

# dev
from signaling import Signal, Message

# mass transport framework
import mass_transport
import mass_transport.tests.testcases as testcases
import mass_transport.probability as massprob

from mass_transport import road_complexity
import mass_transport.road_complexity as mcplx


# roadmap framework
import roadgeometry.roadmap_basic as ROAD
import roadgeometry.probability as roadprob


# simulation framework
from simulation import Simulation
from sources import RoadnetDemandSource
from queues import GatedQueue, BatchNNeighDispatcher
from servers import Vehicle

class data : pass


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
        res = self.callback()
        self.tape.append( res )
        self.sim.schedule( self.tick, self.T )


""" convenient constructors """

def get_sim_setting( N=10, p=.3, mu=1., K=5, lam=1. ) :
    """
    get largest connected component of Erdos(N,p) graph
    with exponentially distr. road lengths (avg. mu);
    Choose k road pairs randomly and assign intensity randomly,
    exponential lam
    """
    g = nx.erdos_renyi_graph( N, p )
    g = nx.connected_component_subgraphs( g )[0]
    
    roadnet = nx.MultiDiGraph()
    
    def roadmaker() :
        for i in itertools.count() : yield 'road%d' % i, np.random.exponential( mu )
    road_iter = roadmaker()
    
    for i, ( u,v,data ) in enumerate( g.edges_iter( data=True ) ) :
        label, length = road_iter.next()
        roadnet.add_edge( u, v, label, length=length )
    
    rates = nx.DiGraph()
    ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
    for i in range( K ) :
        r1 = random.choice( ROADS )
        r2 = random.choice( ROADS )
        if not rates.has_edge( r1, r2 ) :
            rates.add_edge( r1, r2, rate=0. )
        
        data = rates.get_edge_data( r1, r2 )
        data['rate'] += np.random.exponential( lam )
        
    return roadnet, rates


def totalrate( rategraph, rate='rate' ) :
    totalrate = 0.
    for _,__, data in rategraph.edges_iter( data=True ) :
        totalrate += data.get( rate, 0. )
    return totalrate

def scale_rates( rategraph, alpha, rate='rate' ) :
    res = nx.DiGraph()
    for u,v, data in rategraph.edges_iter( data=True ) :
        r = data.get( rate, 0. )
        res.add_edge( u, v, { rate : alpha * r } )
    return res


""" simulation-based network tester """
class RoadmapEMD(object) :
    def __init__(self) :
        self.vehspeed = 1.
        self.horizon = 500.
        
        
    def scenario(self, roadnet, rategraph ) :
        self.roadnet = roadnet
        self.rategraph = rategraph
        
        # Note: rates sum to 1.
        # compute necessary "service velocity"
        demvel_enroute = road_complexity.demand_enroute_velocity( roadnet, rategraph )
        demvel_balance = road_complexity.demand_balance_velocity( roadnet, rategraph )
        MM = road_complexity.MoversComplexity( roadnet, rategraph )
        self.complexity = MM
        
        #assert demvel_enroute + demvel_balance == MM
        print demvel_enroute + demvel_balance, MM
        self.numveh = int( np.floor( MM / self.vehspeed ) )
        
        
    def distance(self, p, q ) :
        return ROAD.distance( self.roadnet, p, q, 'length' )
    
    """ make simulation """
    def sim_init( self ) :
        """ simulation setup """
        # construct the simulation blocks
        sim = Simulation()
        self.sim = sim
        
        source = RoadnetDemandSource( self.roadnet, self.rategraph )
        self.source = source
        source.join_sim( sim )
        
        gate = GatedQueue()
        self.gate = gate
        gate.join_sim( sim )
        
        dispatch = BatchNNeighDispatcher()
        self.dispatch = dispatch
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
        self.vehicles = vehicles
        for k in range( self.numveh ) :
            veh = Vehicle() ; vehicles[ veh ] = None
            veh.set_environment( self.distance )
            veh.set_speed( self.vehspeed )
            randpoint = roadprob.sampleaddress( roadnet, 'length' )
            veh.set_location( randpoint )
            veh.join_sim( sim )
        
        # make a recorder
        recorder = UniformPoller( 1. )
        self.recorder = recorder
        def unassigned_query() :
            return len( self.gate.demands ) + len( self.dispatch.demands )
        recorder.set_query( unassigned_query )
        recorder.join_sim( sim )
        
        # report demand arrivals to several places
        self.DEMANDS = []
        def record_arrival( dem ) :
            self.DEMANDS.append( dem )
        
        def give_to_dispatch( dem ) :
            p, q = dem
            loc = p
            #dispatch.demand_arrived( dem, loc )
            self.gate.demand_arrived( dem )
            
        source_out = source.source()
        #source_out.connect( counting.increment )
        source_out.connect( give_to_dispatch )
        source_out.connect( record_arrival )
        #source.source().connect( give_to_dispatch )
        
        self.timer = data()
        self.timer.last_time = sim.time
        def say( dem ) :
            p, q = dem
            new_time = self.sim.time
            elapsed = new_time - self.timer.last_time
            print 'tick, %f: %s, %s' % ( elapsed, repr(p), repr(q) )
            self.timer.last_time = new_time
            
        source_out.connect( say )
        
        
        def gimme( *args, **kwargs ) :
            print "need a batch!!"
            
        # creates an interface from gate to interactive dispatcher
        gate_if = gate.spawn_interface()
        self.gate_if = gate_if
        dispatch.request_batch.connect( gate_if.request_in )
        dispatch.request_batch.connect( gimme )
        gate_if.batch_out.connect( dispatch.batch_arrived )
        
        def hello( *args, **kwargs ) :
            print 'vehicle is ready!'
        
        # vehicle signal connections
        for veh in vehicles :
            vehconn = dispatch.spawn_interface() ; vehicles[veh] = vehconn
            veh.ready.connect( vehconn.request_in )
            veh.ready.connect( hello )
            #veh.ready.connect( vehconn.request_in )
            vehconn.demand_out.connect( veh.receive_demand )
            
            
    """ run simulation """
    def run_sim(self) :
        sim = self.sim
        horizon = self.horizon
        
        while sim.get_time() < horizon :
            call = sim.get_next_action()
            call()
            
            
    """ after the simulation """
    def display(self) :
        recorder = self.recorder
        n = len( recorder.tape )
        T = recorder.T * np.arange( n )
        plt.plot( T, recorder.tape )
        plt.xlabel( 'Time elapsed' )
        plt.ylabel( 'Number of Demands Waiting' )
        
        
    def compute_statistic(self) :
        # convenience
        horizon = self.horizon
        recorder = self.recorder
        dispatch = self.dispatch
        
        arrivalrate = totalrate( self.rategraph )
        total_demands = len( self.DEMANDS )
        nleft = len( dispatch.demands )
        
        print 'arrival rate (simulated, observed): %f, %f' % ( arrivalrate, total_demands / horizon )
        
        #overrate_est = float( nleft - preload ) / horizon
        take_only_last = .25 * horizon
        take_num = int( np.ceil( take_only_last / recorder.T ) )
        DY = float( recorder.tape[-1] - recorder.tape[-take_num] )
        DT = take_num * recorder.T
        overrate_est = float( DY ) / DT
        max_rate_observed = arrivalrate - overrate_est
        
        miles_per_demand = self.complexity / arrivalrate
        max_rate = self.numveh * self.vehspeed / miles_per_demand
        
        if nleft >= 0 : 
            print 'max sustainable rate (observed): %f' % max_rate_observed
        print 'max sustainable rate (predicted): %f' % max_rate
        
        miles_per_demand_observed = self.vehspeed * self.numveh / max_rate_observed
        complexity_est = arrivalrate * miles_per_demand_observed
        return ( self.complexity, complexity_est )
    
    
        #print 'cost per demand (predicted): %f' % ( self.complexity / arrivalrate )
        #print 'cost per demand (observed): %f' % ( veh.odometer / veh.notches )
        if False :
            DEMS = {}
            for dem in ALL_DEMANDS :
                p, q = dem
                road1 = p.road
                road2 = q.road
                row = DEMS.setdefault( (road1,road2), [] )
                row.append( dem )
                
            empirical_distr = [ ( key, len( val ) / horizon ) for key, val in DEMS.items() ]
        
        num_steps = len( recorder.tape )
        time_axis = recorder.T * np.arange( num_steps )
        (slope,intercept) = sp.polyfit( time_axis, recorder.tape, 1 )
        
        if False :
            # do matching-based checking
            T = 1.
            demands = mcplx.sample_demands( T, normrategraph, roadnet )
            min_total_velocity = mcplx.enroute_cost( demands, roadnet ) / T + mcplx.balance_cost( demands, roadnet ) / T
            print 'empirical expected max rate: %f' % ( 1. / min_total_velocity )




if __name__ == '__main__' :
    # plotting
    import matplotlib as mpl
    mpl.rcParams['ps.useafm'] = True
    mpl.rcParams['pdf.use14corefonts'] = True
    mpl.rcParams['text.usetex'] = True
    
    font = {'family' : 'normal',
            'weight' : 'bold',
            'size'   : 22 }
    mpl.rc('font', **font)       # oh please, work!
    
    import matplotlib.pyplot as plt
    plt.close('all')
    
    
    
    
    # make the roadnet and rategraph
    
    #roadnet, rates = get_sim_setting()
    """ SIM PARAMETERS """
    if False :
        roadnet = testcases.RoadnetExamples.get( 'nesw' )
        for _,__,road, data in roadnet.edges_iter( keys=True, data=True ) :
            data['length'] = 5.
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
    
    elif True :
        roadnet = roadprob.sampleroadnet()
        normrategraph = massprob.sample_rategraph( roadnet, normalize=True )
        
    else :
        roadnet = nx.MultiDiGraph()
        roadnet.add_edge( 0,1, 'LEFT', length=1. )
        roadnet.add_edge( 1,2, 'RIGHT', length=1. )
        normrategraph = nx.DiGraph()
        normrategraph.add_edge( 'LEFT', 'RIGHT', rate=1. )
        

    probe = RoadmapEMD()
    probe.horizon = 1000.
    
    complexity_computed = []
    complexity_estimated = []
    for t in range(10) :
        roadnet, rategraph = get_sim_setting()
        probe.scenario( roadnet, rategraph )
        probe.sim_init()
        probe.run_sim()
        a, b  = probe.compute_statistic()
        #probe.display()
        #plt.show()
        
        complexity_computed.append( a )
        complexity_estimated.append( b )
    
    
    
    
    
