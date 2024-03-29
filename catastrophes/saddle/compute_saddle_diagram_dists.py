import numpy as np
import matplotlib.pyplot as plt
import sys

# local stuff
from pyTopTools.catastrophes import saddle_node as S
from pyTopTools import timeseries

if len( sys.argv ) < 2:
    print "Meant to be used in batch format, must provide a 'run number'"
    sys.exit(1)

run = int( sys.argv[1] )
window_size = int( sys.argv[2] )
print "run:", run
print "window:", window_size


#=======================
# Equation 2.2 (double-well potential with noise)
#=======================
f = lambda x, lam : lam + x - 0.005*x**3
g = lambda x, sigma : sigma # * x (spatial variability)
h = lambda x, lam : 0.001  #* x 

#=======================
# Fix some constants
#=======================
tmax = 11000
xinit = -2
dt = 0.01
sigma = 0.2
lam0 = -4

# data path
vrdata = '/sciclone/scr20/jberwald/saddle_'
prefix = '/sciclone/data10/jberwald/climate_attractors/saddle_node/saddle_'
#vrfile = '/sciclone/scr02/jberwald/saddle_' #'./data/sadde_'

#vrfile = './data/saddle_'

# set up number of realizations
#realizations = 2

# set of range of window sizes
#window_sizes = range( 10, 60, 10 )  # 20-->80, by 10

for step_size in window_sizes:
    # all distances at this window size
    all_distances = []

    tvec, xvec, lamvec = S.sde_integrator( f, g, h, 
                                           tmax, xinit, dt, 
                                           sigma, lam0 )
        
    # for each realization, move the (non-overlapping) window
    # along the time series
    w0 = int( 0.1 * tmax )
    w1 = int( 0.9 * tmax )  
    previous_window = None
    distances = []
    nx = []
    while w0 < w1:
        #print "w0:", w0
        left = int( w0 / dt )
        right = int( (w0+step_size)/ dt )
        window = np.array( xvec[ left : right ] )
        window -= window.mean() # detrend

        # compute persistence diagrams
        current_window = timeseries.Window( window )

        w = int( left * dt )
        nx.append( w )
        persin = vrdata + 't'+ str( w ) + '_window'+\
                 str( window_size ) + '_trial'+ str( run ) + '.txt'
        
        current_window.convert2perseus( persin, 
                                        stepsize=0.0005, nsteps=50 )
        # make the diagram
        current_window.compute_persistence( persin )

        # if not the first window, compute d(D1,D2)
        if previous_window is not None:
            dist = current_window.compute_wasserstein_distance( previous_window.perspath )
            distances.append( float(dist) )

        # update
        previous_window = current_window
        w0 += step_size

    all_distances.append( distances )
    
    # now average the distances over the realizations at this window
    # size. make (n realizations) x (windows) array 
    distarr = np.asarray( all_distances )
    
    # save an array of  distances for this step_size
    np.savetxt( prefix + 'distances_step'+str( window_size ) +'_trial'+str( run )+'.txt', distarr )

    # mean_dist = distarr.mean( axis=0 )
    # np.savetxt( prefix + 'mean_distances_step'+str( step_size ) + '.txt', mean_dist )



