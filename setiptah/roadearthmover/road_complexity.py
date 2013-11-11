
# common
import itertools
import random

# science common
import numpy as np
import networkx as nx

import matplotlib.pyplot as plt

# setiptah dependencies
import setiptah.roadgeometry.roadmap_basic as ROAD
import setiptah.roadgeometry.probability as roadprob

# local dependencies
import road_Ed, roademd



""" algorithms """

def MoversComplexity( roadnet, rategraph, length='length', rate='rate' ) :
    # enroute cost
    enroute_cost = demand_enroute_velocity( roadnet, rategraph, length, rate )
    balance_cost = demand_balance_velocity( roadnet, rategraph, length, rate )
    return enroute_cost + balance_cost



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
            
            
            
            
            
            
""" VALIDATION """

class demand :
    def __init__(self, p, q ) :
        self.pick = p
        self.delv = q


def sample_demands( T, rategraph, roadnet, rate='rate' ) :
    demands = []
    point_on = lambda road : roadprob.sample_onroad( road, roadnet, 'length' )
    for road1, road2, data in rategraph.edges_iter( data=True ) :
        n = np.random.poisson( data.get( rate, 0. ) * T )
        newdems = [ demand( point_on( road1 ), point_on( road2 ) ) for i in range(n) ]
        demands.extend( newdems )
        
    return demands


def enroute_cost( demands, roadnet ) :
    distfunc = lambda p, q : ROAD.distance( roadnet, p, q, 'length' )
    
    enroutes = [ distfunc( dem.pick, dem.delv ) for dem in demands ]
    total_enroute = sum( enroutes )
    return total_enroute

def balance_cost( demands, roadnet ) :
    distfunc = lambda p, q : ROAD.distance( roadnet, p, q, 'length' )
    
    graph = nx.Graph()
    for dem1, dem2 in itertools.product( demands, demands ) :
        dist = distfunc( dem1.delv, dem2.pick )
        graph.add_edge( (dem1,0), (dem2,1), weight = -dist )    # about to do MAX_weight_matching
            
    mate = nx.matching.max_weight_matching( graph, maxcardinality=True )
    balances = [ -graph.get_edge_data( (dem1,0), (dem2,1) ).get('weight') 
                for ( (dem1,side1), (dem2,side2) ) in mate.iteritems() if side1 == 0 ]
    total_balance = sum( balances )
    return total_balance




""" self test """
if __name__ == '__main__' :
    
    # make a random roadnet
    roadnet = roadprob.sampleroadnet()
    
    # make a random rate graph
    rategraph = nx.DiGraph()
    for _,__,road1, data1 in roadnet.edges_iter( keys=True, data=True ) :
        for _,__,road2, data2 in roadnet.edges_iter( keys=True, data=True ) :
            
            curr_rate = np.random.exponential()
            rategraph.add_edge( road1, road2, rate=curr_rate )
            
    # compute the components of cost rate
    enroute_velocity = demand_enroute_velocity( roadnet, rategraph )
    balance_velocity = demand_balance_velocity( roadnet, rategraph )
    
    # flowgraph, costgraph = obtainWassersteinProblem( DEMAND, DEMAND, length='distance' )
    
    print enroute_velocity, balance_velocity
    
    if True :
        T = .5
        DEMANDS = sample_demands( T, rategraph, roadnet )
        
        mean_enroute = enroute_cost( DEMANDS, roadnet ) / T
        
        if True :
            mean_balance = balance_cost( DEMANDS, roadnet ) / T
        else :
            mean_balance = None
        
        print mean_enroute, mean_balance
        



