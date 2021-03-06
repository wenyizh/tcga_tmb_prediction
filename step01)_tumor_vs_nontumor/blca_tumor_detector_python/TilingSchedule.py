import collections
import numpy as np
import openslide


def TilingSchedule(File, Magnification, Tile, tol=0.002):
    """Generates parameters needed to tile a whole-slide-image using OpenSlide
    for a given resolution `Magnification` and tilesize `Tile`.

    Parameters
    ----------
    File : str
       path and filename of slide.
    Magnification : double
       desired magnification.
    Tile : int
       tilesize at desired magnification.
    tol: double
       acceptable mismatch percentage for desired magnification

    Returns
    -------
    Level : int
        pyramid level for use with OpenSlide's 'read_region'.
    Scale : double
        ratio of `Magnification` and native scanning magnification.
    Tout : int
        tilesize at magnification used for reading, for use with OpenSlide's
        ``read_region``.
    Factor : double
        scaling factor needed for resizing output tiles from 'read_region'.
        used when desired magnification is not available and downsampling of
        higher magnification is necessary.
    Magnification : double
        magnification of tiling schedule.
    File : str
        filename and path of slide that schedule corresponds to.
    X : array_like
        horizontal coordinates for each tile used in calls to 'read_region'.
    Y : array_like
        vertical coordinates for each tile used in calls to 'read_region'.
    dX : array_like
        horizontal coordinates at desired magnification. Used for display of
        boundaries and navigation.
    dY : array_like
        vertical coordinates at desired magnification. Used for display of
        boundaries and navigation.

    Notes
    -----
    Return values are return as a namedtuple

    See Also
    --------
    histomicstk.utils.ConvertSchedule
    """

    # check if slide can be opened
    try:
        Slide = openslide.OpenSlide(File)
    except openslide.OpenSlideError:
        print("Cannot find file '" + File + "'")
        return
    except openslide.OpenSlideUnsupportedFormatError:
        print("Slide format not supported. Consult OpenSlide documentation")
        return

    #xr=Slide.properties['openslide.mpp-x']
    #yr=Slide.properties['openslide.mpp-y']


    # get slide dimensions, zoom levels, and objective information
    Dims = Slide.level_dimensions
    Factors = Slide.level_downsamples
    Objective = float(Slide.properties[
                          openslide.PROPERTY_NAME_OBJECTIVE_POWER])

    # calculate magnifications
    Available = tuple(Objective / x for x in Factors)

    # find highest magnification greater than or equal to 'Desired'
    Mismatch = tuple(x - Magnification for x in Available)
    AbsMismatch = tuple(abs(x) for x in Mismatch)
    if min(AbsMismatch) <= tol:
        Level = int(AbsMismatch.index(min(AbsMismatch)))
        Factor = 1
    else:  # pick next highest level, downsample
        Level = int(max([i for (i, val) in enumerate(Mismatch) if val > 0]))
        Factor = Magnification / Available[Level]

    # adjust tilesize based on resizing factor
    Tout = int(round(Tile / Factor))

    # generate X, Y coordinates for tiling
    Stride = Tout * Available[0] / Available[Level]
    X = np.arange(0, Dims[0][0]+1, Stride)
    Y = np.arange(0, Dims[0][1]+1, Stride)
    X, Y = np.meshgrid(X, Y)
    dX = X / (Available[0] / Magnification)
    dY = Y / (Available[0] / Magnification)

    # calculate scale difference between base and desired magnifications
    Scale = Magnification / Objective

    # collect outputs in container
    TilingSchedule = collections.namedtuple('TilingSchedule',
                                            ['Level', 'Scale',
                                             'Tout', 'Factor',
                                             'Magnification', 'File', 'X', 'Y',
                                             'dX', 'dY'])
    Schedule = TilingSchedule(Level, Scale, Tout, Factor,
                              Magnification, File, X, Y, dX, dY)

    return Schedule