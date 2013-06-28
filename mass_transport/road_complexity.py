
import itertools
import random

import numpy as np
import networkx as nx

import matplotlib.pyplot as plt

#import road_Ed, roademd
#import nxopt.max_flow_min_cost as FLOW

import mass_transport       # loads the relevant path, too hacky... should fix this

import roadgeometry.roadmap_basic as ROAD
import road_Ed, roademd




def MoversComplexity( lengraph, rategraph, length='length', rate='rate' ) :
    # enroute cost
    enroute_cost = demand_enroute_velocity( lengraph, rategraph, length, rate )
    balance_cost = demand_balance_velocity( lengraph, rategraph, length, rate )
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
        
    return V


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
            
            
            

if __name__ == '__main__' :
    #import mass_transport
    import roadgeometry.probability as roadprob

    roadnet = roadprob.sampleroadnet()
    
    rategraph = nx.DiGraph()
    #
    for _,__,road1, data1 in roadnet.edges_iter( keys=True, data=True ) :
        for _,__,road2, data2 in roadnet.edges_iter( keys=True, data=True ) :
            
            curr_rate = np.random.exponential()
            rategraph.add_edge( road1, road2, rate=curr_rate )
            
    enroute_velocity = demand_enroute_velocity( roadnet, rategraph )
    balance_velocity = demand_balance_velocity( roadnet, rategraph )
    
    
    
    #flowgraph, costgraph = obtainWassersteinProblem( DEMAND, DEMAND, length='distance' )
    
    print enroute_velocity, balance_velocity
    
    if False :
        distance_between = lambda u, v : GRAPH.get_edge_data( u, v ).get('distance')
        
        class demand :
            def __init__(self, p, q ) :
                self.pick = p
                self.delv = q
                
        T = 20.
        DEMANDS = []
        for u, v, data in GRAPH.edges_iter( data=True ) :
            n = np.random.poisson( data.get('rate') * T )
            DEMANDS.extend([ demand(u,v) for i in range(n) ])
            
        total_enroute = sum( [ distance_between( dem.pick, dem.delv ) for dem in DEMANDS ] )
        mean_enroute = total_enroute / T
        
        
        
        if True :
            graph = nx.Graph()
            for dem1, dem2 in itertools.product( DEMANDS, DEMANDS ) :
                #if dem2 is dem1 : continue  # those edges aren't in there
                
                dist = distance_between( dem1.delv, dem2.pick )
                graph.add_edge( (dem1,0), (dem2,1), weight = -dist )    # about to do MAX_weight_matching
                    
            mate = nx.matching.max_weight_matching( graph, maxcardinality=True )
            total_balance = sum( [ distance_between( dem1.delv, dem2.pick )
                                  for ( (dem1,side1), (dem2,side2) ) in mate.iteritems() if side1 == 0 ] )
            mean_balance = total_balance / T
        else :
            mean_balance = None
        
        print mean_enroute, mean_balance
        
        
        




