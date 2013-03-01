import subprocess, os
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import numpy# as np
import re
import cPickle as pkl
try:
    import pp
except ImportError:
    print "No parallel python install"
    print "We'll try to continue..."
import time
from collections import deque
#from scipy.stats import linregress
# Python image libary
try:
    from PIL import Image  
except ImportError:
    print "Python Image Library not installed"
    raise

slash = '/'

def natural_key(string_):
    """
    Use with frames.sort(key=natural_key)
    """
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', string_)]

def run_chomp( fname, savename ):
    """
    Call chomp to compute the betti numbers of the image in file fname.

    See http://chomp.rutgers.edu
    """
    cmd = ['chomp', fname]
    try:
        with open( savename, 'w' ) as fh:
            p = subprocess.call( cmd, stdout=fh )
    except:
        print "subprocess returned with code", p

def hom_time_gaps( files, dim=0 ):
    """
    Compute the time intervals between successive changes in the
    number of homology generators.

    Imput
    -----

    files : path to a directory containing files recording the
    generators per frames. Or, a single file containing this
    information in a numpy array.
    """
    if os.path.isdir( files ):
        fdir = files + '/'
        dlist = os.listdir( fdir )
        dlist.sort( key=R.natural_key )
        data = []        
        for f in dlist:
            if f.endswith('npy') and not os.path.isdir( fdir+f ):
                data.append( numpy.load( fdir + f ) )
            elif f.endswith('betti') and not os.path.isdir( fdir+f ):
                data.append( numpy.loadtxt( fdir + f ) )
        data = numpy.asarray( data )
    else:
        try:
            data = numpy.load( files )
        except IOError:
            raise
    gens = data[:,dim,-1]
    # find jumps in homology
    dg = numpy.diff( gens )
    # time at which a jump occurs
    w = numpy.where( dg != 0 )[0]
    # return time gaps
    return numpy.diff( w )

def bmp2array( fname, val=0 ):
    """
    Binary images only.
    
    Load BMP using PIL. Assume 'fname' contains binary data. Extract
    data array, shape correctly (will be funky bands otherwise). Use
    array2chomp() to write PIL image data to disk.

    fname -- location of BMP file

    outname -- full path to output file in CHomP-readable format (see
    array2chomp). The extension '.cub' is the one usually used for
    cubical files readable by CHomP.

    val -- 'on' value of binary image.
    """
    im = Image.open( fname )
    s = im.size
    data = numpy.array( im.getdata() )
    data.resize( ( s[1], s[0] ) )
    w = numpy.where( data == val )
    arr = numpy.array( zip( w[0], w[1] ) )
    return arr

def bmp2chomp( fname, outname, val=0 ):
    arr = bmp2array( fname, val )    
    array2chomp( arr, outname )
   

def png2chomp( fname ):
    """
    Convert a numpy array to a text file with lines ( , , ) format for
    chomp. Note: suffix for chomp-readable file must be 'cub' (for
    cubicle complex).
    """
    # open PNG with python image library
    im = Image.open( fname )
    arr = numpy.asarray( im )

    print arr.shape
    # Find where pixels are black. 255 == white. 
    w = numpy.where( arr != 255 )
    del arr
    # filter the rgb format
    w2 = numpy.where( w[2] == 0 )[0]
    newarr = numpy.vstack( ( w[0][w2], w[1][w2] ) ).T
    chfile = fname.strip('png') + 'cub'
    # array2chomp( newarr, chfile )
            
def array2chomp( arr, savename ):
    """
    Convert an array to chomp format, ( , , ). Write the resulting
    column of numbers to disk.
    """
    rows = map( lambda x: str(x)+'\n', map( tuple, iter( arr ) ) ) 
    with open( savename, 'w' ) as fh:
        fh.writelines( rows )

def PIL2array(img):
    return numpy.array(img.getdata(),
                       numpy.uint8).reshape(img.size[1], img.size[0], 3)

def array2PIL(arr, size):
    mode = 'RGBA'
    arr = arr.reshape(arr.shape[0]*arr.shape[1], arr.shape[2])
    if len(arr[0]) == 3:
        arr = numpy.c_[arr, 255*numpy.ones((len(arr),1), numpy.uint8)]
    return Image.frombuffer(mode, size, arr.tostring(), 'raw', mode, 0, 1)

def pix2array( fname, dim=2 ):
    """
    Convert a PIX file with entries ( , , ) to an array.
    """
    rows = []
    with open( fname ) as fh:
        if dim == 2:
            for line in fh.readlines():
                x = line.strip().split( ',' )
                rows.append( [int( x[0][1:] ), int( x[1][:-1] )] )
        elif dim == 3:
            for line in fh.readlines():
                x = line.strip().split( ',' )
                rows.append( [int( x[0][1:] ), int( x[1] ), int( x[2][:-1] )] )
    return numpy.array( rows, dtype=numpy.int )

def stack_images( list_of_frames, height, val=0 ):
    """
    PIL tries to guess the file type from the extension.

    list_of_frame : List of paths to images to stack 'vertically'.
     The (first) bottom image has 1 appended to all coordinates, the next has
     2 appened, etc.

    val : (optional) Value to treat as the 'on' for chomp in binary
    image.

    Returns numpy array of stacked images.
    """
    # read in the frames
    frames = []
    for i, f in enumerate( list_of_frames ): 
        arr = bmp2array( f, val=0 )
        segment = numpy.empty( (arr.shape[0], 3), dtype=numpy.uint )
        segment[:,:-1] = arr
        segment[:,-1].fill( i )
        frames.append( segment )

    return numpy.vstack( frames )
                    
def extract_betti( fname, betti_file=None ):
    """
    Read the betti numbers from the 'fname' containing the output from
    chomp. Save raw Betti numbers
    """
    # open and read chomp-produced data file
    with open( fname, 'r' ) as fh:
        lines = fh.readlines()
    # grab the line with the Betti numbers
    if len( lines ) > 1:
        for line in lines:
            if line.startswith( 'Betti' ):
                # keep only the numbers
                betti_numbers = line.strip().split()[2:]
    # chomp output single line of betti number (Shaun Harker's "other"
    # chomp version...)
    else:
        betti_numbers = lines[0].strip().split()
    max_dim = len( betti_numbers )
    # open betti file and save generators. write the same format for
    # both chomp outputs to keep things consistent
    if not betti_file:
        betti_file = fname[:-3] + 'betti'
    with open( betti_file, 'w' ) as fh:
        for i, b in enumerate( betti_numbers ):
            line = str(i) + ' ' + betti_numbers[i] +'\n'
            fh.write( line )

def read_betti_dir( fdir, suffix='.hom' ):
    """
    Read all .betti files in a directory and organize them for analysis.
    """
    dlist = os.listdir( fdir )
    betti_list = [ f for f in dlist if f.endswith( suffix ) ]
    betti_list.sort(key=natural_key)

    print "chomp output list", betti_list
    
    # keep the frame numbers organized in a dict ?
    #betti = {}
    # nah, just list them
    betti_arr = []
    for b in betti_list:
        bnums = numpy.loadtxt( fdir+b, dtype=numpy.uint8 )
        betti_arr.append( bnums )
    betti_arr = numpy.asarray( betti_arr )
    return betti_arr.T
    
def plot_betti( barr, cell=1, savedir=None, dim=0, fig=None,
               total_cells=2, color='b' ):
    """
    Plot betti numbers for each frame for a cell. Obtain a time series
    (time=frame number)
    """
    if fig is None:
        fig = plt.figure()
    ax = fig.gca()
    #ax = fig.add_subplot(total_cells, 1, cell_num+1)
    data = barr[:,dim,:]
    ax.plot( data[1], 'o-', color=color, lw=1.5, ms=2 )
    # record title and some stats
    ax.set_title(  'Betti numbers for cell '+str(cell)+\
                 ' (mean='+str( round(data[1].mean()) )+')' )
    ax.set_xlabel( 'Frame' )
    ax.set_ylabel( r'$H_{'+str(dim)+'}$' )
    if savedir == None:
        fname = './figures_raw/betti_frames_H'+str(dim)+'_cell'+str(cell)+'.png'
    else:
        fname = savedir + '/betti_frames_H'+str(dim)+'_cell'+str(cell)+'.png'
    fig.savefig( fname )

def plot_hist( data, cell_num=1 ):

    fig = plt.figure()
    ax = fig.add_subplot(111)
    dmean = round( data.mean(), 1 )
    dvar = round( data.var(), 1 )
    n, bins, patches = ax.hist( data, 10, normed=1, facecolor='green',
                                alpha=0.75,  label=r"Mean="+str(dmean)+"\nVar="+str(dvar) )
    
    ## # add a 'best fit' line
    ## y = mlab.normpdf( bins, mu, sigma)
    ## l = plt.plot(bins, y, 'r--', linewidth=1)

    xmin = data.min()
    xmax = data.max()
    ax.set_xlabel(r'$H_1$ generators')
    ax.set_ylabel('Probability')
    ax.set_title(r"Distribution of $H_1$ Generators, Cell "+str(cell_num) )
    ax.axis([xmin-5, xmax+5, 0, 0.1])
    ax.grid(True)
    ax.legend()
    return fig

def plot_spectrum( data ):
    """
    Plot the power spectrum of the data.
    """
    d = data[1]
    # rfft gives positive frequecies. Square to get power spectrum.
    fp = numpy.absolute( numpy.fft.rfft( d ) )**2
    freq = numpy.fft.fftfreq( d.shape[-1] )
    n = len(fp)

    # reshape stuff a bit. keep only positive freqs.
    fp = fp[1:-1]
    freq = freq[1:n-1]
    lrslope = linregress( numpy.log(freq[30:]), numpy.log(fp[30:]) )[0]
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.loglog( freq, fp, label="Lin. reg.="+str(round( lrslope,1 )) )
    ax.legend( loc='lower left' )
    return fig

###
# parallel functions
###
def chomp_stack( low, high, height, path, chomp_path, prefix ):

    for base in range( low,  high, height ):
        frames = []
        # list of frames to stack
        for x in range( height ):
            num = base + x
            frames.append( path + prefix + str( num ) + '.bmp' )
        stack = stack_images( frames, height )
        cubfile = chomp_path + prefix[:-1] + \
            '_b' + str( base ) + \
            '_h' + str( height ) 
        
        # Convert bmp files to array, stack them, write them to
        # chomp-readable format.
        array2chomp( stack, cubfile + '.cub' )
        
        # Now compute homology for each block
        run_chomp( cubfile + '.cub', cubfile + '.hom'  )
 
if __name__ == "__main__":

    import pp
    import time

    start = time.time()

    stack_height = [10, 20]#, 30]

    path = '/data/CT_Firn_Sample/output23-10-3/'
    chomp_path = '/data/CT_Firn_Sample/chomp_files/'
    prefix = 'K09b-23-10-'
    
    # chomp_path = '/sciclone/data10/jberwald/CT_Firn_Samples/chomp_files/'
    # path = '/sciclone/data10/jberwald/CT_Firn_Samples/output23-10-3/'
    # prefix = 'K09b-23-10-'
    
    ## Write Chomp-readable files for 3D blocks

    #parallelize this stuff
    ncpus = len( stack_height )
    job_server = pp.Server( ncpus, ppservers=() )   
    pool = []

    bottom = 3200
    top = 3220
    
    
    if 0:
        for height in stack_height:

            # pool.append( job_server.submit( chomp_stack,
            #                                 ( bottom,
            #                                   top,
            #                                   height,
            #                                   path,
            #                                   chomp_path,
            #                                   prefix ),
            #                                 depfuncs = ( stack_images, array2chomp,
            #                                              run_chomp )
            #                                 ) )





            print "Stack height:", height
            for base in [3310, 3320]:#range( 3200,  3400, height ):
                frames = []
                # list of frames to stack
                for x in range( height ):
                    num = base + x
                    frames.append( path + prefix + str( num ) + '.bmp' )

                print "    Stacking from base:", base
                stack = stack_images( frames, height )
                cubfile = chomp_path + prefix[:-1] + \
                    '_b' + str( base ) + \
                    '_h' + str( height ) 

                # Convert bmp files to array, stack them, write them to
                # chomp-readable format.
                array2chomp( stack, cubfile + '.cub' )

                # Now compute homology for each block
                run_chomp( cubfile + '.cub', cubfile + '.hom'  )
                extract_betti( cubfile + '.hom' )
            print ""

        print "Time:", time.time() - start

    if 1:
        
        #for height in stack_height:
        height = 10
        dim = 1
        bettis = []
        for base in range( 3310,  3330, height ):
            betti_file = chomp_path + prefix[:-1] + \
                '_b' + str( base ) + \
                '_h' + str( height ) + \
                '.betti'
            print betti_file
            bnums = numpy.loadtxt( betti_file, dtype=numpy.uint8 )
            print bnums
            bettis.append( bnums[dim][1] )

        fig = plt.figure()
        ax = fig.gca()
        ax.plot( bettis, 'bo' )
        ax.set_xlabel( "Block number (height="+str(height)+")" )
        ax.set_ylabel( r"$\beta_{"+str( dim )+"}$" )
        ax.set_xlim( -1, len(bettis) )
        ax.set_ylim( min(bettis)-1, max(bettis)+1 )
        plt.show()
