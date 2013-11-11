
import numpy as np
import networkx as nx

import mass_transport
import roadgeometry.roadmap_basic as ROAD


def sample_rategraph( roadnet, rate='rate', normalize=False ) :
    # make a random rate graph
    rategraph = nx.DiGraph()
    total_rate = 0.
    
    for _,__,road1 in roadnet.edges_iter( keys=True ) :
        for _,__,road2 in roadnet.edges_iter( keys=True ) :
            curr_rate = np.random.exponential()
            total_rate += curr_rate
            
            attr_dict = { rate : curr_rate }
            rategraph.add_edge( road1, road2, attr_dict=attr_dict )
            
    if normalize :
        for u, v, data in rategraph.edges_iter( data=True ) :
            data[ rate ] /= total_rate
        
    return rategraph




def samplepair( roadnet, distr1, distr2=None, length_attr='length' ) :
    """ assume distr sums to one; if not, no guaranteed behavior """
    if distr2 is not None : raise 'not implemented yet'
    
    # choose appropriately, randomly... can probably do better
    x = np.random.rand()
    X = 0.
    for (road1,road2), prob in distr1.iteritems() :
        X += prob
        if X >= x : break
        
    _, data1 = ROAD.obtain_edge( roadnet, road1, data_flag=True )
    _, data2 = ROAD.obtain_edge( roadnet, road2, data_flag=True )
    roadlen1 = data1.get( 'length' )
    roadlen2 = data2.get( 'length' )
    
    x = roadlen1 * np.random.rand()
    y = roadlen2 * np.random.rand()
    p = ROAD.RoadAddress( road1, x )
    q = ROAD.RoadAddress( road2, y )
    
    return p, q




