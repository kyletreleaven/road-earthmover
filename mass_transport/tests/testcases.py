
import networkx as nx



class RoadnetExamples :
    @classmethod
    def get(cls, key ) :
        roadnet = nx.MultiDiGraph()
        
        if key == 'nesw' :
            #roadnet.add_edge( 0, 1, 'N', length=1., weight2=3. )
            #roadnet.add_edge( 1, 2, 'E', length=2., weight1=1000., oneway=True )
            #roadnet.add_edge( 2, 3, 'S', length=1., weight1=1. )
            #roadnet.add_edge( 3, 0, 'W', length=1., weight2=1. )
            roadnet.add_edge( 0, 1, 'N', length=1. )
            roadnet.add_edge( 1, 2, 'E', length=2. )
            roadnet.add_edge( 2, 3, 'S', length=1. )
            roadnet.add_edge( 3, 0, 'W', length=1. )
            
        return roadnet
