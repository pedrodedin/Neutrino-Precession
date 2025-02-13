import numpy as np
from scipy.special import gamma
import math 

############# Constants ########################################
G_F=1.1663787*10**(-23) #eV⁻² - Fermi Constant
delta_m2_31=2.5*10**(-3) #eV² - \Delta m²_31
delta_m2_21=7.53*10**(-5); #eV²
theta_31=np.arcsin(math.sqrt(2.18*10**-2)) #\theta_31
theta_21=np.arcsin(math.sqrt(0.307));
N_A=6.02*10**(23) #Avogadro constant

h_slash=6.582119569*10**-16# eV⋅s
c_const=2.99792458*10**8# m/s
from_eV_to_1_over_m=1/(h_slash*c_const)
from_eV_to_1_over_km=from_eV_to_1_over_m*10**(3)
from_1_over_cm3_to_eV3=(1.973*10**(-5))**3
erg_to_MeV=6.2415*10**5

############### Matter Effects (2 Families) ########################
#Calculate the effective mass squared difference in matter
def delta_m2_eff(delta_m2,theta,Acc):
  delta = math.sqrt((delta_m2*np.cos(2*theta)-Acc)**2+(delta_m2*np.sin(2*theta))**2)
  return delta

#Calculate the effective mixing angle in matter
def theta_eff(delta_m2,theta,Acc):
  theta_eff=(1/2)*math.atan2(1,1/((math.tan(2*theta))/(1-(Acc/(delta_m2*np.cos(2*theta))))))
  return theta_eff

#Calculate the matter "Potential" - Acc=2EV_cc
def Acc(N_e,E):
  A = 2*math.sqrt(2)*E*G_F*N_e
  return A

# L vector
def L_vec(n_dim):
	if n_dim==3:
		return 0,0,1
	else:
	   	print("Dimension not defined")
        
# B vector
def B_vec(n_dim,theta):
	if n_dim==3:
		B1=-1*np.sin(2*theta)
		B2=0
		B3=np.cos(2*theta)
		return B1,B2,B3
	else:
	   	print("Dimension not defined")

############# Supernova Info ############################

def phi(E,E_0,alpha):
  N=((alpha+1)**(alpha+1))/(E_0*gamma(alpha+1))
  R=N*((E/E_0)**alpha)*math.exp((-1)*(alpha+1)*E/E_0)
  return R
phi_vec= np.vectorize(phi)

#Neutrino potential
def mu_supernova(r,mu_opt,mu_0=0): # r in km
    if mu_opt=="SN":
        R_0=40#km
#         r=np.array(r)
#         return np.where(r <=R_0,mu_0,mu_0*(R_0/r)**4)
#         mu=[]
#         for r_i in r: 
#             if r_i<=R_0:
#                 mu.append(mu_0)
#             else:
#                 mu.append(mu_0*(R_0/r_i)**4)
#         return np.array(mu)
        if r<R_0:
            return mu_0
        return mu_0*(R_0/r)**4 #eV
    
    elif mu_opt=="const":
        return mu_0
    
    else:
        print("Not a mu option!")
        return 0     
mu_supernova_vec=np.vectorize(mu_supernova)

def D_geom(r,R_nu):
    #r [km]
    return (1-np.sqrt(1-(R_nu/r)**2))**2

#Matter density profile
def SN_density_profile(r,t):
# r[km],t[s]
#https://arxiv.org/abs/hep-ph/0304056
    r=np.array(r)
    rho_0=10**14*(r**(-2.4)) #g/cm³
    if t <1:
        return rho_0
    
    else:
        epsilon=10
        #r_s=50 #km
        r_s0=-4.6*10**3 #km - Shockwave initial position
        v_s=11.3*10**3 #km/s - Shockwave initial velocity
        a_s=0.2*10**3 #km/s² - Shockwave aceleration
        r_s=r_s0+v_s*t+1/2*a_s*t**2 #Shockwave position
        #print(r_s)
        rho=[]
        for i in range(len(r)):
            if r[i]<=r_s:
                aux=(0.28-0.69*np.log(r[i]))*(np.arcsin(1-r[i]/r_s)**1.1)
                f=np.exp(aux)
                rho.append(epsilon*f*rho_0[i])
            else:
                rho.append(rho_0[i])
        return np.array(rho)

#Electron density profile
def lambda_supernova(r,option,ne=N_A,t=1): # r in km
  Y_e=0.5
  m_n=1.67492749804*10**-24 #g
  ne_aux=0
  if option=="no":
      ne_aux=0
  elif option=="const":
      ne_aux=ne
  elif option=="SN":
      ne_aux=(Y_e/m_n)*SN_density_profile(r,t)
  else:
    print("Not a matter option")
    return 0
  return np.sqrt(2)*G_F*from_1_over_cm3_to_eV3*ne_aux #eV

################## Read Output ##########################
def read_output(psoln,params):
  n_f,n_dim,n_E= params
  num_diff_nu_compnents=2*n_f*n_dim
  nu,nubar=[],[]
  for l in range(n_dim):
    nu.append([])
    nubar.append([])
    for k in range(n_f):
      nu[l].append([])
      nubar[l].append([])
      for j in range(len(psoln)):
        nu[l][k].append([])
        nubar[l][k].append([])
        for i in range(n_E):
          nu[l][k][j].append(psoln[j][(i*num_diff_nu_compnents)+(l)+(k*2*n_dim)])
          nubar[l][k][j].append(psoln[j][(i*num_diff_nu_compnents)+(l+3)+(k*2*n_dim)])

  return nu, nubar #[Pauli Matrix][Nu_type][time][energy]

def read_two_flavor(nu, nubar):
  nu_e_time,nubar_e_time=[],[]
  nu_x_time,nubar_x_time=[],[]

  for l in range(len(nu[0][0])): #time array length
      nu_e_time.append([])
      nubar_e_time.append([])
      nu_x_time.append([])
      nubar_x_time.append([])
      for i in range(len(nu[0][0][0])): 
        #nu
        P3_x,P3_e=0,0
        if nu[2][0][l][i]>0:
          P3_e=P3_e+nu[2][0][l][i]
        else:
          P3_x=P3_x+nu[2][0][l][i]

        if nu[2][1][l][i]>0:
          P3_e=P3_e+nu[2][1][l][i]
        else:
          P3_x=P3_x+nu[2][1][l][i]

        nu_e_time[l].append(P3_e)
        nu_x_time[l].append(-1*P3_x)

        #nubar
        P3_x,P3_e=0,0
        if nubar[2][0][l][i]>0:
          P3_e=P3_e+nubar[2][0][l][i]
        else:
          P3_x=P3_x+nubar[2][0][l][i]

        if nubar[2][1][l][i]>0:
          P3_e=P3_e+nubar[2][1][l][i]
        else:
          P3_x=P3_x+nubar[2][1][l][i]

        nubar_e_time[l].append(P3_e)
        nubar_x_time[l].append(-1*P3_x)

  return   nu_e_time,nubar_e_time, nu_x_time,nubar_x_time

def read_two_flavor_v1(nu, nubar):
  nu_e_time,nubar_e_time=[],[]
  nu_x_time,nubar_x_time=[],[]

  for l in range(len(nu[0][0])): #time array length
      nu_e_time.append([])
      nubar_e_time.append([])
      nu_x_time.append([])
      nubar_x_time.append([])
    
      for i in range(len(nu[0][0][0])): 
        #nu
        Pee=(1/2)*(1+nu[2][0][l][i]/nu[2][0][0][i])
        Pxx=(1/2)*(1+nu[2][1][l][i]/nu[2][1][0][i])

        nu_e_time[l].append(Pee*nu[2][0][0][i]+(1-Pxx)*(-1)*nu[2][1][0][i])
        nu_x_time[l].append(Pxx*(-1)*nu[2][1][0][i]+(1-Pee)*nu[2][0][0][i])

        #nubar
        Pee=(1/2)*(1+nubar[2][0][l][i]/nubar[2][0][0][i])
        Pxx=(1/2)*(1+nubar[2][1][l][i]/nubar[2][1][0][i])

        nubar_e_time[l].append(Pee*nubar[2][0][0][i]+(1-Pxx)*(-1)*nubar[2][1][0][i])
        nubar_x_time[l].append(Pxx*(-1)*nubar[2][1][0][i]+(1-Pee)*nubar[2][0][0][i])

  return   nu_e_time,nubar_e_time, nu_x_time,nubar_x_time

def read_two_flavor_Probability(nu, nubar):
  Pee_time,nubar_e_time=[],[]
  Peebar_time,nubar_x_time=[],[]

  for l in range(len(nu[0][0])): #time array length
      Pee_time.append([])
      Peebar_time.append([])
    
      for i in range(len(nu[0][0][0])): 
        #nu
        Pee=(1/2)*(1+nu[2][0][l][i]/nu[2][0][0][i])
        Pee_time[l].append(Pee)
        #nubar
        Peebar=(1/2)*(1+nubar[2][0][l][i]/nubar[2][0][0][i])
        Peebar_time[l].append(Peebar)


  return   Pee_time,Peebar_time

################### Group ######################
def structure_constant(n_dim,i,j,k):
    if i==j or i==k or j==k:
        return 0
    if n_dim==3:
        i_next=(i+1)%3
        if  i_next == j:
            return 1
        if i_next == k:
            return -1 
    else:
        print("Dimension not defined")

def cross_prod(A,B):
    n_components=len(A)
    C=[]
    for i in range(n_components):
      sum=0
      for j in range(n_components):
          for k in range(n_components):
            sum=sum+structure_constant(n_components,i,j,k)*A[j]*B[k]
      C.append(sum)
    return C
