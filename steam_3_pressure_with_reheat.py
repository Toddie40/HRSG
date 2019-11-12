import iapws.iapws97 as steam
import numpy as np
from matplotlib import pyplot as plt
import csv

###############################################################Utility Functions

def MPToBar(pressure):
    return pressure*10

def ToKelvin(temp):
    return temp+273.15
def ToCelcius(temp):
    return temp - 273.15

def BarToMP(pressure):
    return pressure/10

def PFromTS(t,s,p0,precision,maxNoOfIters):
    print("finding pressure at\nEntropy: "+str(s)+"\nTemperature: "+str(t))
    p = p0
    i = 0
    currentConditions = steam._Region2(t,p)
    print("Entropy at starting position: "+str(currentConditions['s']))
    while currentConditions['s'] < s:
        print("iteration: "+str(i))
        print("CurrentEntropy: "+str(currentConditions['s']))
        print("current pressure: "+str(p))
        if i >= maxNoOfIters:
            print("Ran out of iterations! Got to P="+str(p))
            return p
        p-=precision
        currentConditions = steam._Region2(t,p)
        i+=1
    print("Conditions at T="+str(t)+" and s="+str(s))
    print("Found pressure P="+str(p))
    return p

k = 273.15

###############################################################################

class SteamCycle:

    def __init__(self,hp,ip,lp, m1, m2, m3, ma, steam_high_temp, water_low_temp):
        # Input Parameters
        self.HP = hp  # Bar
        self.IP = ip   # Bar
        self.LP = lp    # Bar

        mass_flow_1 = m1
        mass_flow_2 = m2
        mass_flow_3 = m3
        mass_flow_amine = ma

        massflows = {
            'mass flow 1' : mass_flow_1,
            'mass flow 2' : mass_flow_2,
            'mass flow 3' : mass_flow_3,
            'mass flow to amine' : mass_flow_amine
        }


        # total mass flow
        total_mass_flow = mass_flow_1 + mass_flow_2 + mass_flow_3

        # Turbine Mass Flows
        HPT_mass_flow = mass_flow_3
        IPT_mass_flow = HPT_mass_flow + mass_flow_2
        LPT_mass_flow = IPT_mass_flow + mass_flow_1 - mass_flow_amine

        # Pump Mass Flows
        HPP_mass_flow = mass_flow_3
        IPP_mass_flow = mass_flow_2
        LPP_mass_flow = IPP_mass_flow + HPP_mass_flow + mass_flow_1

        #HRSG Mass Flows
        self.economiser_1_mass_flow = total_mass_flow
        self.economiser_2_mass_flow = mass_flow_2
        self.economiser_3_mass_flow = mass_flow_3

        self.evaporator_1_mass_flow = mass_flow_1
        self.evaporator_2_mass_flow = mass_flow_2
        self.evaporator_3_mass_flow = mass_flow_3

        self.superheater_1_mass_flow = mass_flow_1
        self.superheater_2_mass_flow = mass_flow_2 + mass_flow_3
        self.superheater_3_mass_flow = mass_flow_3


        self.SteamHighTemp = steam_high_temp  # Celcius
        ReheatTemp = 565
        WaterLowTemp = water_low_temp  # Celcius


        precision = 0.01  # for iterative calculations
        quality = 0.9  # at turbine outlet


        self.T = [0]*16

        self.T[1] = ToKelvin(WaterLowTemp)

        # Pressures
        self.P = [0]*16
        self.P[1] = steam._PSat_T(self.T[1])

        # low pressure
        self.P[2] = BarToMP(self.LP)  # bar
        self.P[3] = self.P[2]
        self.P[4] = self.P[2]
        self.P[5] = self.P[2]

        # intermediate pressure
        self.P[7] = BarToMP(self.IP)  # bar
        self.P[8] = self.P[7]
        self.P[9] = self.P[8]
        self.P[10] = self.P[9]
        self.P[15] = self.P[9]

        # High Pressure
        self.P[11] = BarToMP(self.HP)  # bar
        self.P[12] = self.P[11]
        self.P[13] = self.P[12]
        self.P[14] = self.P[13]

        # Temperatures in kelvin


        self.T[3] = steam._TSat_P(self.P[3])
        self.T[4] = self.T[3]

        self.T[6] = self.T[1]

        self.T[8] = steam._TSat_P(self.P[8])
        self.T[9] = self.T[8]


        self.T[12] = steam._TSat_P(self.P[12])
        self.T[13] = self.T[12]
        self.T[14] = ToKelvin(self.SteamHighTemp)



        # Begin going around cycle working out available values
        self.SpecificValues = [0] * 16

        self.SpecificValues[1] = steam._Region1(self.T[1], self.P[1])

        self.T[2] = steam._Backward1_T_Ps(self.P[2], self.SpecificValues[1]['s'])
        self.SpecificValues[2] = steam._Region1(self.T[2], self.P[2])

        self.SpecificValues[3] = steam._Region4(self.P[3], 0)
        self.SpecificValues[4] = steam._Region4(self.P[3], 1)

        self.SpecificValues[6] = steam._Region4(self.P[1], quality)
        self.T[5] = steam._Backward2_T_Ps(self.P[5], self.SpecificValues[6]['s'])
        self.SpecificValues[5] = steam._Region2(self.T[5], self.P[5])

        self.T[7] = steam._Backward1_T_Ps(self.P[7], self.SpecificValues[3]['s'])
        self.SpecificValues[7] = steam._Region1(self.T[7], self.P[7])
        self.SpecificValues[8] = steam._Region4(self.P[8], 0 )
        self.SpecificValues[9] = steam._Region4(self.P[8], 1 )
        self.T[10] = steam._Backward2_T_Ps(self.P[10], self.SpecificValues[5]['s'])
        self.SpecificValues[10] = steam._Region2(self.T[10], self.P[10])
        self.T[11] = steam._Backward1_T_Ps(self.P[11], self.SpecificValues[3]['s'])
        self.SpecificValues[11] = steam._Region1(self.T[11], self.P[11])
        self.SpecificValues[12] = steam._Region4(self.P[12], 0)
        self.SpecificValues[13] = steam._Region4(self.P[13], 1)
        self.SpecificValues[14] = steam._Region2(self.T[14], self.P[14])
        self.T[15] = steam._Backward2_T_Ps(self.P[15], self.SpecificValues[14]['s'])
        self.SpecificValues[15] = steam._Region2(self.T[15], self.P[15])


        self.s = [0] * 16
        self.h = [0] * 16

        for i in range(0, len(self.SpecificValues)):
            if i == 0:
                continue
            self.s[i] = self.SpecificValues[i]['s']
            self.h[i] = self.SpecificValues[i]['h']


        #Printing T-P conditions at each point
        print("-------------------------------------------------------")
        print("\nCycle Conditions:")
        for i in range(1,16):
            print("\n\tT"+str(+i)+" = "+str(ToCelcius(self.T[i]))+" C")
            print("\tP"+str(+i)+" = "+str(MPToBar(self.P[i]))+" bar")

        #Finding specific work of turbines and pump
        self.total_works = {
        'Work Type' : 'Work [kW]',
        'LP Pump work' : LPP_mass_flow * (self.h[2] - self.h[1]),
        'IP Pump work' : IPP_mass_flow * (self.h[7] - self.h[3]),
        'HP Pump work' : HPP_mass_flow * (self.h[11] - self.h[3]),
        'HP Turbine work' : HPT_mass_flow * (self.h[14] - self.h[15]),
        'IP Turbine work' : IPT_mass_flow * (self.h[10] - self.h[5]),
        'LP Turbine work' : LPT_mass_flow * (self.h[5] - self.h[6]),
        'LP Heat Input' : self.superheater_1_mass_flow * (self.h[5] - self.h[4]) + self.evaporator_1_mass_flow * (self.h[4] - self.h[3]) + self.economiser_1_mass_flow * (self.h[3] - self.h[2]),
        'IP Heat Input' : self.superheater_2_mass_flow * (self.h[10] - self.h[9]) + self.evaporator_2_mass_flow * (self.h[9] - self.h[8]) + self.economiser_2_mass_flow * (self.h[8] - self.h[7]),
        'HP Heat Input' : self.superheater_3_mass_flow * (self.h[14] - self.h[13]) + self.evaporator_3_mass_flow * (self.h[13] - self.h[12]) + self.economiser_3_mass_flow * (self.h[12] - self.h[11])
        }


        print("\nCycle Specific Works:")
        for work, value in self.total_works.items():
            print("\n\t"+work+" = "+str(value))

        #Finding Total Heat into Cycle from HRSG
        self.q_in = self.total_works['LP Heat Input'] + self.total_works['IP Heat Input'] + self.total_works['HP Heat Input']

        #FInding Net Work
        self.w_net = self.total_works['HP Turbine work'] + self.total_works['IP Turbine work'] + self.total_works['LP Turbine work'] - self.total_works['HP Pump work'] - self.total_works['IP Pump work'] - self.total_works['LP Pump work']

        #Finding Thermal Efficiency fo Steam Cycle
        self.efficiency = self.w_net / self.q_in

        print("\nCycle Efficiency:")
        print("\n\tefficiency = "+str(self.efficiency*100)+"%")
        print("\n\tWith a Net Work of : "+str(np.round(self.w_net))+"kW")
        print("\n\tand a Total Heat Input of: "+str(np.round(self.q_in))+"kW\n")

    def PlotResults(self):
        plt.plot(self.s[1:],np.subtract(self.T[1:],273.15),'r+',markersize=10)
        plt.xlabel("Specific Entropy [kJ/kgK]")
        plt.ylabel("Temperature [C]")
        #add labels to points
        for i in range(1,len(self.s)):
            plt.annotate(str(i),
                            (self.s[i],self.T[i]-273.15),
                            textcoords="offset points",
                            xytext=(0,10),
                            ha='center')
        plt.show()

    def SaveResults(self,conditions_file_name: str, energies_file_name: str):

        # save temperatuyres pressures enthalpies and entropies to csv
        conditions_array = np.vstack([self.T, self.P, self.h, self.s])
        conditions_array = np.transpose(conditions_array)
        np.savetxt(conditions_file_name+".csv", conditions_array, delimiter=',')
        print(["Temp K","Pressure [MPa]", "Enthalpy [kJ/kg]", "Entropy [kJ/kgK]"])
        print(conditions_array)

        # save energies dictionary to csv
        try:
            with open(energies_file_name+".csv", 'w') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerows(self.total_works.items())
                writer.writerow(["Mass Flow Rates"])
                writer.writerows(self.massflows.items())
        except IOError:
            print("I/O error")
