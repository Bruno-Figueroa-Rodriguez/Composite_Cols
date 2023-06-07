import streamlit as st
import openseespy.opensees as ops
import opsvis as opsvis
from typing import Optional

import os #import operating system to create folder and such
import vfo.vfo as vfo
import matplotlib.pyplot as plt
import numpy as numpy
import pandas as pd

inch = 1.
kip = 1.
sec = 1.
ft = 12*inch
lb = kip/1000.
ksi = 1*kip/((1*inch)**2)
psi = 1*lb/((1*inch)**2)
pcf = 1*lb/((1*ft)**3)
psf = 1*lb/((1*ft)**2)
in2 = inch**2
in4 = inch**4
g = 32.2*ft/sec**2

def create_composite_column(colsecTag,colsecH,colsecB,colcover,colnumBarsSec,colbarAreaSec,encased,wf_sects,IDconcCore,IDsteel,IDconcCover,IDreinf):

    colcoverY = colsecH/2
    colcoverZ = colsecB/2
    colcoreY = colsecH/2-colcover
    colcoreZ = colsecB/2-colcover

    w_A = wf_sects.loc[encased]['A']*inch**2
    w_d = wf_sects.loc[encased]['d']*inch
    w_web_t = wf_sects.loc[encased]['tw']*inch
    w_flange_b = wf_sects.loc[encased]['bf']*inch
    w_flange_t = wf_sects.loc[encased]['tf']*inch
    w_Ixx = wf_sects.loc[encased]['Ix']*inch**4
    w_Iyy = wf_sects.loc[encased]['Iy']*inch**4

    colA = colsecH*colsecB
    colIz = 1/12*colsecB*colsecH**3

    col_fib_sec = [['section','Fiber',colsecTag,'-GJ',1.e6],
                ['patch','quad',IDconcCore,4,4,*[-1*colcoreY],*[colcoreZ,-1*colcoreY],*[-1*colcoreZ,0.],*[-1*colcoreZ,0,colcoreZ]],
                ['patch','quad',IDconcCore,4,4,0.,colcoreZ,0,-1*colcoreZ,colcoreY,-1*colcoreZ,colcoreY,colcoreZ],
                ['patch','quad',IDsteel,4,2,*[-1*w_d/2,w_flange_b/2],*[-1*w_d/2,-1*w_flange_b/2],*[-1*w_d/2+w_flange_t,-1*w_flange_b/2],*[-1*w_d/2+w_flange_t,w_flange_b/2]], #Bot flange
                ['patch','quad',IDsteel,2,4,*[-1*w_d/2+w_flange_t,w_web_t/2],*[-1*w_d/2+w_flange_t,-1*w_web_t/2],*[w_d/2-w_flange_t,-1*w_web_t/2],*[w_d/2-w_flange_t,w_web_t/2]], #Web
                ['patch','quad',IDsteel,4,2,*[w_d/2-w_flange_t,w_flange_b/2],*[w_d/2-w_flange_t,-1*w_flange_b/2],*[w_d/2,-1*w_flange_b/2],*[w_d/2,w_flange_b/2]], #Top flange
                ['patch','quad',IDconcCover,4,2,-1*colcoverY,colcoverZ,-1*colcoverY,-1*colcoverZ,-1*colcoreY,-1*colcoreZ,-1*colcoreY,colcoreZ],
                ['patch','quad',IDconcCover,2,4,-1*colcoreY,-1*colcoreZ,-1*colcoverY,-1*colcoverZ,colcoverY,-1*colcoverZ,colcoreY,-1*colcoreZ],
                ['patch','quad',IDconcCover,4,2,colcoreY,colcoreZ,colcoreY,-1*colcoreZ,colcoverY,-1*colcoverZ,colcoverY,colcoverZ],
                ['patch','quad',IDconcCover,2,4,-1*colcoverY,colcoverZ,-1*colcoreY,colcoreZ,colcoreY,colcoreZ,colcoverY,colcoverZ],
                ['layer','straight',IDreinf,colnumBarsSec,colbarAreaSec,colcoreY,colcoreZ,colcoreY,-1*colcoreZ],
                ['layer','straight',IDreinf,colnumBarsSec,colbarAreaSec,-1*colcoreY,colcoreZ,-1*colcoreY,-1*colcoreZ]]
    

    if colnumBarsSec%2 == 0:
        for i in range(1,int(colnumBarsSec/2)):
            col_fib_sec.append(['layer','straight',IDreinf,2,colbarAreaSec,i/(colnumBarsSec/2)*colcoreY,colcoreZ,i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ])
            col_fib_sec.append(['layer','straight',IDreinf,2,colbarAreaSec,-i/(colnumBarsSec/2)*colcoreY,colcoreZ,-i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ])

    else:
        for i in range(int(colnumBarsSec/2)):
            col_fib_sec.append(['layer','straight',IDreinf,2,colbarAreaSec,i/(colnumBarsSec/2)*colcoreY,colcoreZ,i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ])
            col_fib_sec.append(['layer','straight',IDreinf,2,colbarAreaSec,-i/(colnumBarsSec/2)*colcoreY,colcoreZ,-i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ])


    matcolor = ['c', 'lightgrey', 'b', 'y', 'g', 'w']
    col_fig = opsvis.plot_fiber_section(col_fib_sec, matcolor=matcolor)
    plt.axis('equal')


    ops.section('Fiber',colsecTag,'-GJ',1.e6)

    #Core patch
    ops.patch('quad',IDconcCore,4,8,-1*colcoreY,colcoreZ,-1*colcoreY,-1*colcoreZ,colcoreY,-1*colcoreZ,colcoreY,colcoreZ)
    #Cover patches, one for each side
    #BOTTOM COVER
    ops.patch('quad',IDconcCover,4,2,*[-1*colcoverY,colcoverZ],*[-1*colcoverY,-1*colcoverZ],*[-1*colcoreY,-1*colcoreZ],*[-1*colcoreY,colcoreZ])
    #RIGHT COVER
    ops.patch('quad',IDconcCover,2,4,-1*colcoreY,-1*colcoreZ,-1*colcoverY,-1*colcoverZ,colcoverY,-1*colcoverZ,colcoreY,-1*colcoreZ)
    #TOP COVER
    ops.patch('quad',IDconcCover,4,2,colcoreY,colcoreZ,colcoreY,-1*colcoreZ,colcoverY,-1*colcoverZ,colcoverY,colcoverZ)
    #LEFT COVER
    ops.patch('quad',IDconcCover,2,4,-1*colcoverY,colcoverZ,-1*colcoreY,colcoreZ,colcoreY,colcoreZ,colcoverY,colcoverZ)


    #Defining steel encased wide flange layer

    ops.patch('quad',IDsteel,4,2,*[-1*w_d/2,w_flange_b/2],*[-1*w_d/2,-1*w_flange_b/2],*[-1*w_d/2+w_flange_t,-1*w_flange_b/2],*[-1*w_d/2+w_flange_t,w_flange_b/2]) #Bot flange
    ops.patch('quad',IDsteel,2,4,*[-1*w_d/2+w_flange_t,w_web_t/2],*[-1*w_d/2+w_flange_t,-1*w_web_t/2],*[w_d/2-w_flange_t,-1*w_web_t/2],*[w_d/2-w_flange_t,w_web_t/2]) #Web
    ops.patch('quad',IDsteel,4,2,*[w_d/2-w_flange_t,w_flange_b/2],*[w_d/2-w_flange_t,-1*w_flange_b/2],*[w_d/2,-1*w_flange_b/2],*[w_d/2,w_flange_b/2]) #Bottom flange


    #Defining reinforcement layers
    #TOP REINFORCEMENT
    ops.layer('straight',IDreinf,colnumBarsSec,colbarAreaSec,colcoreY,colcoreZ,colcoreY,-1*colcoreZ)
    #BOTTOM REINFORCEMENT
    ops.layer('straight',IDreinf,colnumBarsSec,colbarAreaSec,-1*colcoreY,colcoreZ,-1*colcoreY,-1*colcoreZ)

    #Side reinforcement for columns
    if colnumBarsSec%2 == 0:
        for i in range(1,int(colnumBarsSec/2)):
            ops.layer('straight',IDreinf,2,colbarAreaSec,i/(colnumBarsSec/2)*colcoreY,colcoreZ,i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ)
            ops.layer('straight',IDreinf,2,colbarAreaSec,-i/(colnumBarsSec/2)*colcoreY,colcoreZ,-i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ)
        
    else:
        for i in range(int(colnumBarsSec/2)):
        
            ops.layer('straight',IDreinf,2,colbarAreaSec,i/(colnumBarsSec/2)*colcoreY,colcoreZ,i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ)
            ops.layer('straight',IDreinf,2,colbarAreaSec,-i/(colnumBarsSec/2)*colcoreY,colcoreZ,-i/(colnumBarsSec/2)*colcoreY,-1*colcoreZ)



    return col_fig
    


def create_rc_beam(beamsecTag,beamsecH,beamsecB,beamcover,beamnumBarsSec,beambarAreaSec,IDconcCore,IDconcCover,IDreinf,color='g'):
    
    beamcoverY = beamsecH/2
    beamcoverZ = beamsecB/2
    beamcoreY = beamsecH/2-beamcover
    beamcoreZ = beamsecB/2-beamcover

    beam_fib_sec = [['section','Fiber',beamsecTag,'-GJ',1.e6],
                ['patch','quad',IDconcCore,4,8,-1*beamcoreY,beamcoreZ,-1*beamcoreY,-1*beamcoreZ,beamcoreY,-1*beamcoreZ,beamcoreY,beamcoreZ],
                ['patch','quad',IDconcCover,4,2,-1*beamcoverY,beamcoverZ,-1*beamcoverY,-1*beamcoverZ,-1*beamcoreY,-1*beamcoreZ,-1*beamcoreY,beamcoreZ],
                ['patch','quad',IDconcCover,2,4,-1*beamcoreY,-1*beamcoreZ,-1*beamcoverY,-1*beamcoverZ,beamcoverY,-1*beamcoverZ,beamcoreY,-1*beamcoreZ],
                ['patch','quad',IDconcCover,4,2,beamcoreY,beamcoreZ,beamcoreY,-1*beamcoreZ,beamcoverY,-1*beamcoverZ,beamcoverY,beamcoverZ],
                ['patch','quad',IDconcCover,2,4,-1*beamcoverY,beamcoverZ,-1*beamcoreY,beamcoreZ,beamcoreY,beamcoreZ,beamcoverY,beamcoverZ],
                ['layer','straight',IDreinf,beamnumBarsSec,beambarAreaSec,beamcoreY,beamcoreZ,beamcoreY,-1*beamcoreZ],
                ['layer','straight',IDreinf,beamnumBarsSec,beambarAreaSec,-1*beamcoreY,beamcoreZ,-1*beamcoreY,-1*beamcoreZ]]

    matcolor = [color, 'lightgrey', 'gold', 'w', 'w', 'w']
    
    beam_fig = opsvis.plot_fiber_section(beam_fib_sec, matcolor=matcolor)
    plt.axis('equal')


    ops.section('Fiber',beamsecTag,'-GJ',1.e6)

    #Core patch
    ops.patch('quad',IDconcCore,4,8,-1*beamcoreY,beamcoreZ,-1*beamcoreY,-1*beamcoreZ,beamcoreY,-1*beamcoreZ,beamcoreY,beamcoreZ)

    #Cover patches, one for each side
    #BOTTOM COVER
    ops.patch('quad',IDconcCover,4,2,-1*beamcoverY,beamcoverZ,-1*beamcoverY,-1*beamcoverZ,-1*beamcoreY,-1*beamcoreZ,-1*beamcoreY,beamcoreZ)

    #RIGHT COVER
    ops.patch('quad',IDconcCover,2,4,-1*beamcoreY,-1*beamcoreZ,-1*beamcoverY,-1*beamcoverZ,beamcoverY,-1*beamcoverZ,beamcoreY,-1*beamcoreZ)

    #TOP COVER
    ops.patch('quad',IDconcCover,4,2,beamcoreY,beamcoreZ,beamcoreY,-1*beamcoreZ,beamcoverY,-1*beamcoverZ,beamcoverY,beamcoverZ)

    #LEFT COVER
    ops.patch('quad',IDconcCover,2,4,-1*beamcoverY,beamcoverZ,-1*beamcoreY,beamcoreZ,beamcoreY,beamcoreZ,beamcoverY,beamcoverZ)


    #Defining reinforcement layers
    #TOP REINFORCEMENT
    ops.layer('straight',IDreinf,beamnumBarsSec,beambarAreaSec,beamcoreY,beamcoreZ,beamcoreY,-1*beamcoreZ)
    #BOTTOM REINFORCEMENT
    ops.layer('straight',IDreinf,beamnumBarsSec,beambarAreaSec,-1*beamcoreY,beamcoreZ,-1*beamcoreY,-1*beamcoreZ)

    return beam_fig



    



