import modeling_functions as mod_fun
import pandas as pd
import openseespy.opensees as ops
import pytest

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


wf_sects = pd.read_csv('aisc_w_sections.csv')
wf_sects = wf_sects.set_index(['AISC_Manual_Label'])




fc = -4
Kfc = 1.3
Fy = 60*ksi
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

IDconcCore = 1 #Confined concrete mat tag
IDconcCover = 2 #Unconfined concrete mat tag
IDreinf = 3 #Reinforcement mat tag
IDsteel = 4


ops.wipe()
ops.model('basic','-ndm',3,'-ndf',6)
# print(IDconcCore,fc1C,eps1C,fc2C,eps2C,Lambda,ftC,Ets)

ops.uniaxialMaterial('Concrete02',IDconcCore,fc1C,eps1C,fc2C,eps2C,Lambda,ftC,Ets)
ops.uniaxialMaterial('Concrete02',IDconcCover,fc1U,eps1U,fc2U,eps2U,Lambda,ftU,Ets)
ops.uniaxialMaterial('Steel02',IDreinf,Fy,Es,Bs,R0,cR1,cR2)
ops.uniaxialMaterial('Steel02',IDsteel,Fy,Es,Bs,R0,cR1,cR2)


def test_create_composite_column():
    assert mod_fun.create_composite_column(1,36,36,2,8,1,'W14X22',wf_sects,IDconcCore,IDsteel,IDconcCover,IDreinf) == None


test_create_composite_column()
        

def test_create_rc_beam():
    assert mod_fun.create_rc_beam(2,24,18,2,6,1,IDconcCore,IDconcCover,IDreinf) == None

test_create_rc_beam()