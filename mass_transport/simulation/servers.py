

from signaling import Signal, Message

DEBUG = False



class Vehicle :
    def __init__(self) :
        self.ready = Signal()
        self.odometer = 0.
        self.odometer_full = 0.
        self.odometer_empty = 0.
        
        self.mylog = []
        self.notches = 0
        
    def set_environment(self, f_dist ) :
        self.f_dist = f_dist
        
    def set_speed(self, speed ) :
        self.speed = speed
        
    def set_location(self, location ) :
        self.location = location
        
    def join_sim(self, sim ) :
        self.sim = sim
        self.sim.schedule( self.ready_at )
        
    def log_timefull( self, time ) :
        self.odometer_full += time
        self.odometer += time
        
    def log_timeempty( self, time ) :
        self.odometer_empty += time
        self.odometer += time

        
    """ signaloid """
    def ready_at(self) : self.ready( self.location )
    
    """ slot """
    def receive_demand(self, demand ) :
        self.mylog.append( demand )
        
        p, q = demand
        time = self.sim.get_time()
        if True : 
            print '%s, got demand at %f: (%s, %s)' % ( repr( self ), time, repr(p), repr(q) )
        
        self.pick = p ; self.delv = q
        
        dist_curr_to_pick = self.f_dist( self.location, p )
        time_curr_to_pick = dist_curr_to_pick / self.speed
        if DEBUG : print 'moving to pickup, there in %f' % time_curr_to_pick
        
        self.next_dist = dist_curr_to_pick
        self.sim.schedule( self.arrived_at_pickup, time_curr_to_pick )
        
    """ auto slot """
    def arrived_at_pickup(self) :
        time = self.sim.get_time()
        self.log_timeempty( self.next_dist )
        self.location = self.pick
        if DEBUG : print 'arrived to pickup at %f' % time
        
        q = self.delv
        dist_pick_to_delv = self.f_dist( self.location, q )
        time_pick_to_delv = dist_pick_to_delv / self.speed
        if DEBUG : print 'moving to delivery, there in %f' % time_pick_to_delv
        
        self.next_dist = dist_pick_to_delv
        self.sim.schedule( self.delivered, time_pick_to_delv )
        
    """ auto slot """
    def delivered(self) :
        time = self.sim.get_time()
        self.log_timefull( self.next_dist )
        self.location = self.delv
        time = self.sim.get_time()
        if DEBUG : print 'delivered at %f' % time
        
        self.notches = self.notches + 1
        
        self.ready_at()







