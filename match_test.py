
import itertools
import random

import pickle

import numpy as np
import networkx as nx

import matplotlib.pyplot as plt

#import road_Ed, roademd
#import nxopt.max_flow_min_cost as FLOW

import mass_transport       # loads the relevant path, too hacky... should fix this

import roadgeometry.roadmap_basic as ROAD
import roadgeometry.probability as roadprob

road_Ed = mass_transport.road_Ed
roademd = mass_transport.roademd

import bpmatch_roads.bm_roadnet as ROADBM




# use to get a random scenario: roadnet + rategraph
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
    PP = [ dem.pick for dem in demands ]
    PP = [ (a.road,a.coord) for a in PP ]
    
    QQ = [ dem.delv for dem in demands ]
    QQ = [ (a.road,a.coord) for a in QQ ]
    
    match = ROADBM.ROADSBIPARTITEMATCH( PP, QQ, roadnet )
    return ROADBM.ROADMATCHCOST( match, PP, QQ, roadnet )


def balance_cost2( demands, roadnet ) :
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








def save_result( filename ) :
    DATA = dict()
    DATA['enroute_predict'] = enroute_predict
    DATA['enroute_compute'] = enroute_compute
    DATA['balance_predict'] = balance_predict
    DATA['balance_compute'] = balance_compute
    
    pickle.dump( DATA, open( filename, 'w' ) )
    
if __name__ == '__main__' :
    plt.close('all')
    
    enroute_predict = []
    enroute_compute = []
    balance_predict = []
    balance_compute = []

    
    for k in range(20) :
        print 'SAMPLING A SCENARIO'
        if True :
            roadnet, rategraph = get_sim_setting( mu = 10. )
        else :
            # make a random roadnet
            roadnet = roadprob.sampleroadnet()
            
            # make a random rate graph
            rategraph = nx.DiGraph()
            for _,__,road1, data1 in roadnet.edges_iter( keys=True, data=True ) :
                for _,__,road2, data2 in roadnet.edges_iter( keys=True, data=True ) :
                    
                    curr_rate = np.random.exponential()
                    rategraph.add_edge( road1, road2, rate=curr_rate )
                    
        # compute the components of cost rate
        print 'PREDICTING ENROUTE VELOCITY'
        enroute_velocity = demand_enroute_velocity( roadnet, rategraph )
        print 'PREDICTING BALANCE VELOCITY'
        balance_velocity = demand_balance_velocity( roadnet, rategraph )
        
        print enroute_velocity, balance_velocity
        
        if True :
            T = 100.
            print 'SIMULATING %F TIME PASSAGE' % T
            DEMANDS = sample_demands( T, rategraph, roadnet )
            print '%d DEMANDS ARRIVED' % len( DEMANDS )
            
            print 'COMPUTING EMPIRICAL ENROUTE VELOCITY'
            mean_enroute = enroute_cost( DEMANDS, roadnet ) / T
            
            if True :
                print 'COMPUTING EMPIRICAL BALANCE VELOCITY'
                mean_balance = balance_cost( DEMANDS, roadnet ) / T
                
                if False :
                    print 'AND BY THE SLOW ALGORITHM'
                    mean_balance2 = balance_cost2( DEMANDS, roadnet ) / T
                else :
                    mean_balance2 = None
            else :
                mean_balance = None
            
            print mean_enroute, mean_balance, mean_balance2
            
        enroute_predict.append( enroute_velocity )
        enroute_compute.append( mean_enroute )
        balance_predict.append( balance_velocity )
        balance_compute.append( mean_balance )
        
        



