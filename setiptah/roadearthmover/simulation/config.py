
import random
import itertools

import tempfile
import pickle       # to save non-human readables
import yaml         # to save human-readables

# scientific
import numpy
import networkx


# setiptah
import setiptah.roadgeometry.roadmap_basic as ROAD
import setiptah.roadgeometry.probability as roadprob
import setiptah.roadearthmover.probability as massprob




class SimConfig() :
    def __init__(self) :
        # physical qualities
        self.roadnet = None
        self.rategraph = None
        self.numveh = None
        self.vehspeed = None
        
        # simulation configs
        self.horizon = None
    
    
    @classmethod
    def sampleNetwork(cls) :
        g = nx.erdos_renyi_graph( 10, .3 )      # magical, yes.
        g = nx.connected_component_subgraphs( g )[0]
        
        roadnet = nx.MultiDiGraph()
        
        def roadmaker() :
            for i in itertools.count() : yield 'road%d' % i, np.random.exponential()
            
        road_iter = roadmaker()
        for i, ( u,v,data ) in enumerate( g.edges_iter( data=True ) ) :
            label, length = road_iter.next()
            roadnet.add_edge( u, v, label, length=length )
            
        return roadnet
    
            
    @classmethod
    def sampleRateGraph(cls, roadnet ) :
        rates = nx.DiGraph()
        ROADS = [ key for u,v,key in roadnet.edges_iter( keys=True ) ]
        for i in range(5) :     # magical, yes.
            r1 = random.choice( ROADS )
            r2 = random.choice( ROADS )
            if not rates.has_edge( r1, r2 ) :
                rates.add_edge( r1, r2, rate=0. )
            
            data = rates.get_edge_data( r1, r2 )
            data['rate'] += .25 * (1./5) * np.random.exponential()      # magical, yes.
        
        return rates
    
        
    @classmethod
    def sample(cls) :
        if False :
            roadnet = testcases.RoadnetExamples.get( 'nesw' )
            for _,__,road, data in roadnet.edges_iter( keys=True, data=True ) :
                data['length'] = 5.
            roadset = [ road for _,__,road in roadnet.edges_iter( keys=True ) ]
            
            normrategraph = nx.DiGraph()
            # is it a "true zero" issue?
            if False :      # ...apparently not
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
            
            
    def totalRate(self) :
        x = 0.
        for r1,r2, data in self.rategraph.edges_iter( data=True ) :
            x += data.get('rate')
        return x
        
    def scaleToRate(self, targetRate ) :
        T = self.totalRate()
        K = targetRate/T
        for r1,r2, data in self.rategraph.edges_iter( data=True ) :
            data['rate'] *= K
            
    def utilization(self) :
        moverscplx = road_complexity.MoversComplexity( self.roadnet, self.rategraph )
        return self.arrivalrate * moverscplx / self.numveh / self.vehspeed




if __name__ == '__main__' :
    simc = SimConfig.sampleSim()
    
    simc.numveh = 1
    simc.vehspeed = 1.
    simc.horizon = 10000.
    
    
    """ end parameters """
        
    """ derived parameters """
    # the function which will be used by various components to compute distances
    #f_dist = lambda p, q : ROAD.distance( roadnet, p, q, 'length' )
    
    # Note: rates sum to 1.
    # compute necessary "service velocity"
    #demvel_enroute = road_complexity.demand_enroute_velocity( roadnet, normrategraph )
    #demvel_balance = road_complexity.demand_balance_velocity( roadnet, normrategraph )
    #
        
    """ end derived parameters """
    
    
    
    
    