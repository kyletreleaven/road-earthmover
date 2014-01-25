
# built-in
import itertools
import random

# science common
import numpy as np
import scipy as sp
import networkx as nx

# dev
from setiptah.eventsim.signaling import Signal, Message

# mass transport framework
#import mass_transport
import setiptah.roadearthmover.tests.testcases as testcases
import setiptah.roadearthmover.probability as massprob

import setiptah.roadearthmover.road_Ed as road_Ed
import setiptah.roadearthmover.roademd as roademd
import setiptah.roadearthmover.road_complexity as road_complexity
#from mass_transport import road_Ed, roademd, road_complexity

mcplx = road_complexity     # another alias
#import mass_transport.road_complexity as mcplx

# roadmap framework
import setiptah.roadgeometry.roadmap_basic as ROAD
import setiptah.roadgeometry.probability as roadprob


# simulation framework
from setiptah.eventsim.simulation import Simulation
from setiptah.roadearthmover.simulation.sources import RoadnetDemandSource, ScriptSource
from setiptah.roadearthmover.simulation.queues import GatedQueue, BatchNNeighDispatcher
from setiptah.roadearthmover.simulation.servers import Vehicle


class data : pass


def debug_input() :
    if False : return raw_input()



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

class demand :
    def __init__(self, p, q ) :
        self.pick = p
        self.delv = q

def sample_demands( T, rategraph, roadnet, rate='rate' ) :
    demands = []
    point_on = lambda road : roadprob.sample_onroad( road, roadnet, 'length' )
    for road1, road2, data in rategraph.edges_iter( data=True ) :
        n = np.random.poisson( data.get( rate, 0. ) * T )
        #newdems = [ demand( point_on( road1 ), point_on( road2 ) ) for i in range(n) ]
        newdems = [ ( point_on( road1 ), point_on( road2 ) ) for i in range(n) ]
        demands.extend( newdems )
        
    numdem = len( demands )
    print 'sampled %d' % numdem
    debug_input()
    
    times = T * np.random.rand(numdem)
    script = sorted( zip( times, demands ) )
    return script
    #return demands

def demand_enroute_velocity( roadnet, rategraph, length='length', rate='rate' ) :
    """
    TODO: implement node <-> object checking
    """
    V = {}
    for road1, road2, data in rategraph.edges_iter( data=True ) :
        curr_rate = data.get( rate )
        if curr_rate is None : continue
        curr_v = curr_rate * road_Ed.roadEd_conditional( roadnet, road1, road2, length )
        V[ (road1,road2) ] = curr_v
        
    return sum( V.values() )

def demand_balance_velocity( roadnet, rategraph, length='length', rate='rate' ) :
    computeImbalance( roadnet, rategraph, rate )
    return roademd.EarthMoversDistance( roadnet, length )

def computeImbalance( roadnet, rategraph, rate='rate' ) :
    for road in rategraph.nodes_iter() :
        supply = rategraph.in_degree( road, rate ) - rategraph.out_degree( road, rate )
        _, road_data = ROAD.obtain_edge( roadnet, road, True )
        if supply > 0. :
            road_data['weight1'] = supply
        elif supply < 0. :
            road_data['weight2'] = -supply




def moverscomplexity( roadnet, n_rategraph, length='length', rate='rate' ) :
    miles_per_dem = road_complexity.MoversComplexity( roadnet, n_rategraph, length='length', rate='rate' )
    return miles_per_dem

def convert_complexity_and_servicerate( arg, sys_speed ) :
    return float( sys_speed ) / arg
    
    

""" simulation-based network tester """
class RoadmapEMD(object) :
    def __init__(self) :
        self.vehspeed = 1.
        #self.horizon = 500.
        
    def scenario(self, roadnet, rategraph, numveh=1, vehspeed=1. ) :
        self.roadnet = roadnet
        self.rategraph = rategraph
        self.numveh = numveh
        self.vehspeed = vehspeed
        
    def distance(self, p, q ) :
        return ROAD.distance( self.roadnet, p, q, 'length' )
    
    """ make simulation """
    def sim_init( self ) :
        """ simulation setup """
        # construct the simulation blocks
        sim = Simulation()
        self.sim = sim
        
        if False :
            script = sample_demands( self.horizon, self.rategraph, self.roadnet )
            source = ScriptSource( script )
            print 'obtained %d demands' % len( source.script )
            debug_input()
        else :
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
        
        
    def rate_observed(self) :
        # convenience
        horizon = self.horizon
        recorder = self.recorder
        dispatch = self.dispatch
        
        arrivalrate = totalrate( self.rategraph )
        total_demands = len( self.DEMANDS )
        nleft = len( dispatch.demands )
        
        print 'arrival rate (simulated, observed): %f, %f' % ( arrivalrate, total_demands / horizon )
        
        if True :
            # see what this does
            rate_observed = sum([ veh.notches for veh in self.vehicles ]) / self.horizon
        else :
            #overrate_est = float( nleft - preload ) / horizon
            take_only_last = .25 * horizon
            take_num = int( np.ceil( take_only_last / recorder.T ) )
            DY = float( recorder.tape[-1] - recorder.tape[-take_num] )
            DT = take_num * recorder.T
            overrate_est = float( DY ) / DT
            rate_observed = arrivalrate - overrate_est
        
        return rate_observed




if __name__ == '__main__' :
    import pickle
    
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
    
    def showresults() :
        plt.scatter( complexity_computed, complexity_estimated )
        
    for t in range(50) :
        roadnet, rategraph = get_sim_setting( mu=2. )
        
        R = totalrate( rategraph )
        n_rategraph = scale_rates( rategraph, 1. / R )
        
        enroute_velocity = demand_enroute_velocity( roadnet, n_rategraph )
        balance_velocity = demand_balance_velocity( roadnet, n_rategraph )
        complexity = enroute_velocity + balance_velocity
        #complexity = moverscomplexity( roadnet, n_rategraph )
        
        
        for k in range(1) :
            numveh = np.random.randint(1,5+1)
            
            rate_predicted = convert_complexity_and_servicerate( complexity, numveh )
            simrates = scale_rates( n_rategraph, 2. * rate_predicted )
            
            probe.scenario( roadnet, simrates, numveh, 1. )
            
            probe.sim_init()
            probe.run_sim()
            rate_observed = probe.rate_observed()
            
            complexity_observed = convert_complexity_and_servicerate( rate_observed, numveh )
            
            complexity_computed.append( complexity )
            complexity_estimated.append( complexity_observed )
        
        
    showresults()
    plt.show()
    
    def saveresult( filename ) :
        data = {}
        data['complexity_estimated'] = complexity_estimated
        data['complexity_computed'] = complexity_computed
        
        pickle.dump( data, open( filename, 'w' ) )
        
