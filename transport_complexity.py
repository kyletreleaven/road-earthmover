
import itertools
import random

import numpy as np
import networkx as nx

import matplotlib.pyplot as plt

import nxopt.max_flow_min_cost as FLOW


class Wassnode(object) : pass

def WassersteinNetwork( digraph, rate='rate', distance='distance' ) :
    W_graph = nx.DiGraph()
    s = Wassnode() ; t = Wassnode()
    
    for u,v, data in digraph.edges_iter( data=True ) :
        W_graph.add_edge( u,v, weight=data.get( distance ) )
        
    for u, data in digraph.nodes_iter( data=True ) :
        surplus = digraph.in_degree( u, rate ) - digraph.out_degree( u, rate )
        if surplus > 0. :
            W_graph.add_edge( s, u, capacity=surplus, weight=0. )
        elif surplus < 0. :
            W_graph.add_edge( u, t, capacity=-surplus, weight=0. )
            
    return W_graph, s, t


def compute_marginals( digraph, rate='rate' ) :
    rate_orig = dict()
    rate_dest = dict()
    for u, data in digraph.nodes_iter( data=True ) :
        rate_orig[u] = digraph.out_degree( u, rate )
        rate_dest[u] = digraph.in_degree( u, rate )
        
    return rate_orig, rate_dest

def compute_surplus( digraph, rate='rate' ) :
    surplus = dict()
    for u, data in digraph.nodes_iter( data=True ) :
        surplus[u] = digraph.out_degree( u, rate ) - digraph.in_degree( u, rate )
        
    return surplus




def MoversComplexity( digraph, rate='rate', distance='distance' ) :
    # enroute cost
    enroute_costs = [ data.get(rate) * data.get(distance) for _,__,data in digraph.edges_iter( data=True ) ]
    enroute_cost = sum( enroute_costs )
    
    # balancing costs
    W_graph, s, t = WassersteinNetwork( digraph, rate, distance )
    flow = FLOW.max_flow_min_cost( W_graph, s, t )
    balance_cost = FLOW.flow_cost( flow, W_graph )
        
    return enroute_cost + balance_cost, enroute_cost, balance_cost




def randompoint() :
    return np.random.rand(2)

def display( graph, coord='coord' ) :
    map = [ ( u, data.get('coord') ) for u,data in graph.nodes_iter( data=True ) ]
    layout = dict( map )
    
    nx.draw( graph, pos=layout )
    
    


if True :
    DEMAND = nx.DiGraph()
    
    #PLACES = [ 'HOME', 'WORK', 'SHOPPING' ]
    PLACES = [ 'HOME', 'WORK', 'SHOPPING', 'GYM', 'MOVIE' ]
    for place in PLACES :
        DEMAND.add_node( place, coord=randompoint() )
        
    for o, o_data in DEMAND.nodes_iter( data=True ) :
        o_loc = o_data.get( 'coord' )
        
        for d, d_data in DEMAND.nodes_iter( data=True ) :
            #if d is o : continue
            # this is actually important, max_flow_min_cost chokes without it
            
            # geometry
            d_loc = d_data.get( 'coord' )
            distance = np.linalg.norm( d_loc - o_loc )
            
            # demand
            rate = np.random.exponential()
            
            DEMAND.add_edge( o, d, distance=distance, rate=rate )
            
            
            
            
