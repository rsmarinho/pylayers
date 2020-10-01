from __future__ import print_function
import pdb
import doctest
from pylayers.antprop.spharm import *
#from sphere import spherepack, Wrapec, mathtogeo
import numpy as np
import doctest
import os
import glob
"""
.. currentmodule:: pylayers.antprop.antvsh

.. autosummary::
    :members:

"""

def vsh(A, dsf=1):
    """
    Parameters
    ----------

    A
    dsf : in
        downsamplig factor

    Notes
    -----

    This function calculates the Vector Spherical Harmonics coefficients
    It makes use of the spherepack function vha

        m : phi    longitude
        n : theta  latitude

    Antenna pattern are stored       (f theta phi)
    Coeff are stored with this order (f , n , m )

    The vsh coefficient are organized differently
    should be better for compression along frequency axis

    Parameters
    ----------

    A   :  antenna
    dsf :  int
        down sampling factor  'default 1'


    """

    th = A.theta[::dsf]
    ph = A.phi[::dsf]

    #th = A.theta[::dsf,0]
    #ph = A.phi[0,::dsf]

    nth = len(th)
    nph = len(ph)

    nf = A.nf

    if (nph % 2) == 1:
        mdab = min(nth, (nph + 1) / 2)
    else:
        mdab = min(nth, nph / 2)

    ndab = nth

    Br = 1j * np.zeros((nf, ndab, mdab))
    Bi = 1j * np.zeros((nf, ndab, mdab))
    Cr = 1j * np.zeros((nf, ndab, mdab))
    Ci = 1j * np.zeros((nf, ndab, mdab))

    gridComp = Wrapec()
    wvha, lvha = gridComp.vhai(nth, nph)

    for k in range(nf):
        #
        # Real part
        #
        Ftr = A.Ft[::dsf, ::dsf,k].real
        Fpr = A.Fp[::dsf, ::dsf,k].real
        #
        # Ftr  Ntheta,Nphi
        # Fpr  Ntheta,Nphi
        #
        if Ftr.shape!=(nth,nph):
            Ftr=Ftr*np.ones((nth,nph))
        if Fpr.shape!=(nth,nph):
            Fpr=Fpr*np.ones((nth,nph))

        brr, bir, crr, cir = gridComp.vha(nth, nph, 1,
                                          lvha, wvha,
                                          np.transpose(Fpr),
                                          np.transpose(Ftr))
        #
        # Imaginary part
        #
        Fti = A.Ft[::dsf, ::dsf,k].imag
        Fpi = A.Fp[::dsf, ::dsf,k].imag

        if Fti.shape!=(nth,nph):
            Fti=Fti*np.ones((nth,nph))
        if Fpi.shape!=(nth,nph):
            Fpi=Fpi*np.ones((nth,nph))

        bri, bii, cri, cii = gridComp.vha(nth, nph, 1,
                                          lvha, wvha,
                                          np.transpose(Fpi),
                                          np.transpose(Fti))

        Br[k, :, :] = brr + 1j * bri
        Bi[k, :, :] = bir + 1j * bii
        Cr[k, :, :] = crr + 1j * cri
        Ci[k, :, :] = cir + 1j * cii

    #
    # m=0 row is multiplied by 0.5
    #

    Br[:, :, 0] = 0.5 * Br[:, :, 0]
    Bi[:, :, 0] = 0.5 * Bi[:, :, 0]
    Cr[:, :, 0] = 0.5 * Cr[:, :, 0]
    Ci[:, :, 0] = 0.5 * Ci[:, :, 0]


    Br = VCoeff(typ='s1', fmin=A.fGHz[0], fmax=A.fGHz[-1], data=Br)
    Bi = VCoeff(typ='s1', fmin=A.fGHz[0], fmax=A.fGHz[-1], data=Bi)
    Cr = VCoeff(typ='s1', fmin=A.fGHz[0], fmax=A.fGHz[-1], data=Cr)
    Ci = VCoeff(typ='s1', fmin=A.fGHz[0], fmax=A.fGHz[-1], data=Ci)
    A.C = VSHCoeff(Br, Bi, Cr, Ci)
    return(A)

if (__name__ == "__main__"):
    doctest.testmod()

