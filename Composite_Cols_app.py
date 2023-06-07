import streamlit as st
import openseespy.opensees as ops
import opsvis as opsvis
from typing import Optional

import os #import operating system to create folder and such
import vfo.vfo as vfo
import matplotlib.pyplot as plt
import numpy as numpy
import pandas as pd


st.title('Natural Period of RC vs Composite RC columns')
st.set_option('deprecation.showPyplotGlobalUse', False)

wf_sects = pd.read_csv('aisc_w_sections.csv')


# st.write(wf_sects.tail())

in_data = st.sidebar

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

cover = 2*inch

with in_data:
    encased = st.selectbox('Encased Wide Flange',wf_sects['AISC_Manual_Label'])
    Lbeam = st.number_input('Length of X beam (ft)',value = 12)*ft
    Lcol = st.number_input('Length of Column (ft)',value = 18)*ft
    Lgird = st.number_input('Length of Y beam (ft)',value = 15)*ft
    columns = st.number_input('Number of Stories', value = 5)
    beams = st.number_input('Number of X bays', value = 2)
    girders = st.number_input('Number of Y bays', value = 3)

    fc = -1*st.number_input('Concrete Compressive Strength KSI (Unconfined)',value = 4.0)
    Kfc = st.number_input('Ratio of Confined to unconfined Concrete Strength',value = 1.3)
    
    Fy = st.number_input('Steel Yield Strength (ksi)',value = 60)*ksi
Ec = 57000*(-fc/psi)**0.5*psi

#Confined Concrete Parameters
fc1C = fc*Kfc
eps1C = 2.*fc1C/Ec
fc2C = 0.2*fc1C
eps2C = 5*eps1C

#Unconfined Concrete Parameters
fc1U = fc
eps1U = -0.003
fc2U = 0.2*fc1U
eps2U = -0.01
Lambda = 0.1

#Concrete Tensile-strength properties
ftC = -0.14*fc1C
ftU = -0.14*fc1U
Ets = ftU/0.002

#Steel yield stress

Es = 29000*ksi
Bs = 0.01
R0 = 18
cR1 = 0.925
cR2 = 0.15

scalegraph = 1  #0 for no scaling, 1 for scaling
plotparam = 1.25*max(Lbeam*beams,Lcol*columns,Lgird*girders)

IDconcCore = 1 #Confined concrete mat tag
IDconcCover = 2 #Unconfined concrete mat tag
IDreinf = 3 #Reinforcement mat tag
IDsteel = 4
IDconcCore5 = 5 #testing

ops.wipe()
ops.model('basic','-ndm',3,'-ndf',6)
RigidDiaphragm = 'ON'

ops.uniaxialMaterial('Concrete02',IDconcCore,fc1C,eps1C,fc2C,eps2C,Lambda,ftC,Ets)
ops.uniaxialMaterial('Concrete02',IDconcCore5,fc1C,eps1C,fc2C,eps2C,Lambda,ftC,Ets)
ops.uniaxialMaterial('Concrete02',IDconcCover,fc1U,eps1U,fc2U,eps2U,Lambda,ftU,Ets)
ops.uniaxialMaterial('Steel02',IDreinf,Fy,Es,Bs,R0,cR1,cR2)
ops.uniaxialMaterial('Steel02',IDsteel,Fy,Es,Bs,R0,cR1,cR2)

rebars = {'#3':{'diam':0.375,'area':0.11},
              '#4':{'diam':0.5,'area':0.2},
              '#5':{'diam':0.625,'area':0.31},
              '#6':{'diam':0.75,'area':0.44},
              '#7':{'diam':0.875,'area':0.6},
              '#8':{'diam':1,'area':0.79},
              '#9':{'diam':1.128,'area':1},
              '#10':{'diam':1.27,'area':1.27},
              '#11':{'diam':1.41,'area':1.56}}


st.header("RC Column")
colsecTag = 1
colsecH = st.number_input('Column Depth',value=20)*inch #COL HEIGHT
colsecB = st.number_input('Column Width',value=20)*inch #COL WIDTH
colcover = st.number_input('Column Concrete Cover',value=2)*inch

colcoverY = colsecH/2
colcoverZ = colsecB/2
colcoreY = colsecH/2-colcover
colcoreZ = colsecB/2-colcover

colnumBarsTop = 4
colnumBarsBot = 4
colnumBarsInt = 2
colnumBarsSec = st.number_input('Column Bars Per Layer',value = 8) #Change this to change amount of rebar per layer
colbarAreaSec = rebars[st.selectbox('Col Rebar Size',['#3','#4','#5','#6','#7','#8','#9','#10','#11'])]['area']*inch**2




wf_sects = wf_sects.set_index(['AISC_Manual_Label'])



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
opsvis.plot_fiber_section(col_fib_sec, matcolor=matcolor)
plt.axis('equal')
st.pyplot()



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




    

st.header("RC X beam")
beamsecTag = 2
beamsecH = st.number_input('X Beam Depth',value=30)*inch #BEAM HEIGHT
beamsecB = st.number_input('X Beam Width',value=18)*inch #BEAM WIDTH
beamcover = st.number_input('X Beam Concrete Cover',value=2)*inch

beamcoverY = beamsecH/2
beamcoverZ = beamsecB/2
beamcoreY = beamsecH/2-beamcover
beamcoreZ = beamsecB/2-beamcover
beamnumBarsTop = 4
beamnumBarsBot = 4
beamnumBarsInt = 2
beamnumBarsSec = st.number_input('X Beam Bars Per Layer',value = 5) #Change this to change amount of rebar per layer
beambarAreaSec = rebars[st.selectbox('X Beam Rebar Size',['#3','#4','#5','#6','#7','#8','#9','#10','#11'])]['area']*inch**2


beam_fib_sec = [['section','Fiber',beamsecTag,'-GJ',1.e6],
              ['patch','quad',IDconcCore,4,8,-1*beamcoreY,beamcoreZ,-1*beamcoreY,-1*beamcoreZ,beamcoreY,-1*beamcoreZ,beamcoreY,beamcoreZ],
              ['patch','quad',IDconcCover,4,2,-1*beamcoverY,beamcoverZ,-1*beamcoverY,-1*beamcoverZ,-1*beamcoreY,-1*beamcoreZ,-1*beamcoreY,beamcoreZ],
              ['patch','quad',IDconcCover,2,4,-1*beamcoreY,-1*beamcoreZ,-1*beamcoverY,-1*beamcoverZ,beamcoverY,-1*beamcoverZ,beamcoreY,-1*beamcoreZ],
              ['patch','quad',IDconcCover,4,2,beamcoreY,beamcoreZ,beamcoreY,-1*beamcoreZ,beamcoverY,-1*beamcoverZ,beamcoverY,beamcoverZ],
              ['patch','quad',IDconcCover,2,4,-1*beamcoverY,beamcoverZ,-1*beamcoreY,beamcoreZ,beamcoreY,beamcoreZ,beamcoverY,beamcoverZ],
              ['layer','straight',IDreinf,beamnumBarsSec,beambarAreaSec,beamcoreY,beamcoreZ,beamcoreY,-1*beamcoreZ],
              ['layer','straight',IDreinf,beamnumBarsSec,beambarAreaSec,-1*beamcoreY,beamcoreZ,-1*beamcoreY,-1*beamcoreZ]]

matcolor = ['g', 'lightgrey', 'gold', 'w', 'w', 'w']
opsvis.plot_fiber_section(beam_fib_sec, matcolor=matcolor)
plt.axis('equal')
st.pyplot()



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





    
st.header("RC Y beam")
girdsecTag = 3
girdsecH = st.number_input('Y Beam Depth',value=36)*inch #GIRDER HEIGHT
girdsecB = st.number_input('Y Beam Width',value=24)*inch #GIRDER WIDTH
girdcover = st.number_input('Y Beam Concrete Cover',value=2)*inch

girdcoverY = girdsecH/2
girdcoverZ = girdsecB/2
girdcoreY = girdsecH/2-girdcover
girdcoreZ = girdsecB/2-girdcover
girdnumBarsTop = 4
girdnumBarsBot = 4
girdnumBarsInt = 2
girdnumBarsSec = st.number_input('Y Beam Bars Per Layer',value = 8) #Change this to change amount of rebar per layer
girdbarAreaSec = rebars[st.selectbox('Y Beam Rebar Size',['#3','#4','#5','#6','#7','#8','#9','#10','#11'])]['area']*inch**2


    

gird_fib_sec = [['section','Fiber',girdsecTag,'-GJ',1.e6],
              ['patch','quad',IDconcCore,4,8,-1*girdcoreY,girdcoreZ,-1*girdcoreY,-1*girdcoreZ,girdcoreY,-1*girdcoreZ,girdcoreY,girdcoreZ],
              ['patch','quad',IDconcCover,4,2,-1*girdcoverY,girdcoverZ,-1*girdcoverY,-1*girdcoverZ,-1*girdcoreY,-1*girdcoreZ,-1*girdcoreY,girdcoreZ],
              ['patch','quad',IDconcCover,2,4,-1*girdcoreY,-1*girdcoreZ,-1*girdcoverY,-1*girdcoverZ,girdcoverY,-1*girdcoverZ,girdcoreY,-1*girdcoreZ],
              ['patch','quad',IDconcCover,4,2,girdcoreY,girdcoreZ,girdcoreY,-1*girdcoreZ,girdcoverY,-1*girdcoverZ,girdcoverY,girdcoverZ],
              ['patch','quad',IDconcCover,2,4,-1*girdcoverY,girdcoverZ,-1*girdcoreY,girdcoreZ,girdcoreY,girdcoreZ,girdcoverY,girdcoverZ],
              ['layer','straight',IDreinf,colnumBarsSec,girdbarAreaSec,girdcoreY,girdcoreZ,girdcoreY,-1*girdcoreZ],
              ['layer','straight',IDreinf,colnumBarsSec,girdbarAreaSec,-1*girdcoreY,girdcoreZ,-1*girdcoreY,-1*girdcoreZ]]



matcolor = ['b', 'lightgrey', 'gold', 'w', 'w', 'w']
opsvis.plot_fiber_section(gird_fib_sec, matcolor=matcolor)
plt.axis('equal')
st.pyplot()


ops.section('Fiber',girdsecTag,'-GJ',1.e6)

#Core patch
ops.patch('quad',IDconcCore,4,8,-1*girdcoreY,girdcoreZ,-1*girdcoreY,-1*girdcoreZ,girdcoreY,-1*girdcoreZ,girdcoreY,girdcoreZ)

#Cover patches, one for each side
#BOTTOM COVER
ops.patch('quad',IDconcCover,4,2,-1*girdcoverY,girdcoverZ,-1*girdcoverY,-1*girdcoverZ,-1*girdcoreY,-1*girdcoreZ,-1*girdcoreY,girdcoreZ)

#RIGHT COVER
ops.patch('quad',IDconcCover,2,4,-1*girdcoreY,-1*girdcoreZ,-1*girdcoverY,-1*girdcoverZ,girdcoverY,-1*girdcoverZ,girdcoreY,-1*girdcoreZ)

#TOP COVER
ops.patch('quad',IDconcCover,4,2,girdcoreY,girdcoreZ,girdcoreY,-1*girdcoreZ,girdcoverY,-1*girdcoverZ,girdcoverY,girdcoverZ)

#LEFT COVER
ops.patch('quad',IDconcCover,2,4,-1*girdcoverY,girdcoverZ,-1*girdcoreY,girdcoreZ,girdcoreY,girdcoreZ,girdcoverY,girdcoverZ)


#Defining reinforcement layers
#TOP REINFORCEMENT
ops.layer('straight',IDreinf,colnumBarsSec,girdbarAreaSec,girdcoreY,girdcoreZ,girdcoreY,-1*girdcoreZ)
#BOTTOM REINFORCEMENT
ops.layer('straight',IDreinf,colnumBarsSec,girdbarAreaSec,-1*girdcoreY,girdcoreZ,-1*girdcoreY,-1*girdcoreZ)



node_counter = 0


for z in range(0,columns+1):
    #print("level " + str(z))
    for y in range(0,girders+1):
        for x in range(0,beams+1):
            node_counter += 1
            ops.node(node_counter,x*Lbeam,y*Lgird,z*Lcol)         
            #print("Node number {} created".format(node_counter))

st.write("last node number {} ".format(node_counter))

Diap = []

for diap_counter in range(columns):
    Diap.append([1000.+diap_counter, Lbeam*beams/2, Lgird*girders/2, Lcol*(diap_counter+1)])

NodesDi = [] #List of nodes organized by level

for Ni in range(columns+1):
    NodesDi.append([*range(1+(Ni*(beams+1)*(girders+1)),1+(beams+1)*(girders+1)+(Ni*(beams+1)*(girders+1)))])


if RigidDiaphragm == 'ON':
    dirDia = 3 #Zaxis perpendicular to diaphragm plane
    for Nd in Diap:
        ops.node(int(Nd[0]),*Nd[1:4])
        ops.fix(int(Nd[0]),*[0,0,1,1,1,0])
        
    
    for level_nodes in range(columns):
        ops.rigidDiaphragm(dirDia,int(Diap[level_nodes][0]),*(NodesDi[level_nodes+1]))



fix_node_counter = 0            

for y in range(0,girders+1):
    for x in range(0,beams+1):
        fix_node_counter += 1
        ops.fix(fix_node_counter,1,1,1,1,1,1)
        print("node fixed {} ".format(fix_node_counter))
        
        

colTransfTag = 1
beamTransfTag = 2
girdTransfTag = 3

colTransf = 'PDelta'
beamTransf = 'Linear'
girdTransf = 'Linear'


#ops.geomTransf(colTransf,colTransfTag,1.,0.,0.) #WIDE FLANGE WEAK AXIS BENDING
ops.geomTransf(colTransf,colTransfTag,0.,1.,0.) #WIDE FLANGE STRONG AXIS BENDING
ops.geomTransf(beamTransf,beamTransfTag,0.,-1.,0)
ops.geomTransf(girdTransf,girdTransfTag,1.,0.,0.)

np = 4 #Number of integration points

##############################################################CREATION OF COLUMN ELEMENTS    
n=0 #counter for columns parallel to Z

for z in range(0,columns):
    for y in range(0,girders+1):
        for x in range(0,beams+1):
            n=n+1
            ops.element('nonlinearBeamColumn',n,n,n+(((beams+1)*(girders+1))),np,colsecTag,colTransfTag)

print("last column is {}".format(n))
opsvis.plot_model()
if scalegraph:
    plt.axis([0,plotparam,0,plotparam])
    #st.pyplot()

num_cols = n #Variable used to assign shapes to elements (Columns)

##############################################################CREATION OF BEAM ELEMENTS (X-dir)
m=0 #counter for beams parallel to X

for z in range(1,columns+1):
    for y in range(0,girders+1):
        for x in range(0,beams):
            n += 1
            m += 1
            ops.element('nonlinearBeamColumn',n,m+((beams+1)*(girders+1)),m+((beams+1)*(girders+1))+1,np,beamsecTag,beamTransfTag)
        m += 1 
            
print("the last X-dir beam tag is " + str(n))

num_beams = n-num_cols #Variable used to assign shapes to elements (Beams in X direction)

opsvis.plot_model()
if scalegraph:
    plt.axis([0,plotparam,0,plotparam])
    #st.pyplot()

##############################################################CREATION OF BEAM ELEMENTS (Y-dir)
p=0 #counter for girders parallel to y

for z in range(1,columns+1):
    for y in range(0,girders):
        for x in range(0,beams+1):
            n += 1
            p += 1
            ops.element('nonlinearBeamColumn',n,p+((beams+1)*(girders+1)),p+((beams+1)*(girders+1))+(beams+1),np,girdsecTag,girdTransfTag)
    p += beams+1

print("the last Y-dir beam tag is " + str(n))

num_girds = n-num_cols-num_beams #Variable used to assign shapes to elements (Beams in Y direction)

opsvis.plot_model()
if scalegraph:
    plt.axis([0,plotparam,0,plotparam])
    #st.pyplot()


#___________________________DEFINING GRAVITY LOADS, WEIGHTS AND MASSES
GammaConcrete = 150*lb/ft**3 #PERIODS LOOK MORE REASONABLE USING 15pcf
Tslab = 6*inch
Lslab = Lgird/2 #Simplification to compute weight
DLfactor = 1.0
Qslab = GammaConcrete*Tslab*Lslab*DLfactor
QBeam = GammaConcrete*beamsecH*beamsecB
QGird = GammaConcrete*girdsecH*girdsecB
QdlCol = GammaConcrete*colsecH*colsecB
QdlBeam = Qslab + QBeam
QdlGird = QGird

weight_col = QdlCol*Lcol
weight_beam = QdlBeam*Lbeam
weight_gird = QdlGird*Lgird
weight_total = (weight_col*num_cols+weight_beam*num_beams+weight_gird*num_girds)


st.write('mass on each node will be: {}'.format(weight_total/(node_counter-((beams+1)*(girders+1)))))
for Ni in range(1+((beams+1)*(girders+1)),1+node_counter):
    ops.mass(Ni,weight_total/g/(node_counter-((beams+1)*(girders+1)))/columns,weight_total/g/(node_counter-((beams+1)*(girders+1)))/columns,0.0)


Nmodes = 3*columns

vals = ops.eigen('-fullGenLapack',Nmodes)
st.write('vals will be')
st.write(vals)
Tmodes = numpy.zeros(len(vals))
for i in range(Nmodes):
    Tmodes[i] = 2*numpy.pi/vals[i]**0.5
    st.write("T[%i]: %.5f" % (i+1, Tmodes[i]))


ele_shapes ={}

ColShape = ['rect',[colsecB,colsecH]]
BeamShape = ['rect',[beamsecB,beamsecH]]  
GirdShape = ['rect',[girdsecB,girdsecH]]


for i in range(1,num_cols+1):
    ele_shapes[i]=ColShape

for ii in range(num_cols+1,num_cols+num_beams+1):
    ele_shapes[ii]=BeamShape
    
for iii in range(num_cols+num_beams+1,num_cols+num_beams+num_girds+1):
    ele_shapes[iii]=GirdShape
    

opsvis.plot_extruded_shapes_3d(ele_shapes)
if scalegraph:
    plt.axis([0,plotparam,0,plotparam])
    st.pyplot()

st.write('OK')