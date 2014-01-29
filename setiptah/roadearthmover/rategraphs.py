
"""
a rate graph is simple a digraph with some non-negative "intensity" or "rate" attribute

rate graphs can be used to describe joint distributions (or mixed, homogenous Poisson processes) on discrete sets,
or else segment-pair-wise, uniform joint distributions (or mixed, etc...) on roadmaps

for prob. distributions, the intensities should sum to 1.
""" 

import networkx as nx


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















