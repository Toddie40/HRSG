#import steam_with_reheat
import iapws.iapws97 as steam
import numpy as np
from matplotlib import pyplot as plt

class HeatExchangerError(Exception):
    def __init__(self, message):
        self.message = message

class Economiser:
    def __init__(self, t_h_in, t_c_in, t_c_out, cp_h, cp_c, m_h, m_c):
        self.t = {}
        self.t['h_in'] = t_h_in
        self.t['c_in'] = t_c_in
        self.t['c_out'] = t_c_out
        self.cp = {}
        self.cp['c'] = cp_c
        self.cp['h'] = cp_h
        self.m = {}
        self.m['h'] = m_h
        self.m['c'] = m_c

        print("Initialised Economiser with the following Temperatures")
        for key, value in self.t.items():
            print(key + str(value))

    def evaluate(self):
        self.t['h_out'] = self.t['h_in'] - ( (self.m['c'] * self.cp['c'] * (self.t['c_out'] - self.t['c_in'])) / (self.m['h'] * self.cp['h']) )
        return self


class Evaporator:
    def __init__(self, t_h_in, t_c_in, pressure_c, m_h, m_c, cp_h):
        self.t = {}
        self.t['h_in'] = t_h_in
        self.t['c_in'] = t_c_in
        self.h_c_in = steam._Region4(pressure_c, 0)['h']
        self.h_c_out = steam._Region4(pressure_c, 1)['h']
        self.t['c_out'] = steam._TSat_P(pressure_c) - 273.15
        self.m_h = m_h
        self.m_c = m_c
        self.cp_h = cp_h

        print("Initialised Evaporator with the following Temperatures")
        for key, value in self.t.items():
            print(key + str(value))
    def evaluate(self):
        self.t['h_out'] = self.t['h_in'] - ( (self.m_c * (self.h_c_out - self.h_c_in))/(self.m_h * self.cp_h) )
        return self


class Superheater:
    def __init__(self, t_h_in, t_c_in, t_c_out, cp_h, cp_c, m_h, m_c):
        # sanity checks
        if t_h_in < t_c_in:
            # our heating fluid is colder than our cold fluid
            raise HeatExchangerError('Heating fluid is colder than cold fluid!')


        # variable assignment
        self.t = {}
        self.t['h_in'] = t_h_in
        self.t['c_in'] = t_c_in
        self.t['c_out'] = t_c_out
        self.m = {}
        self.m['h'] = m_h
        self.m['c'] = m_c
        self.cp = {}
        self.cp['h'] = cp_h
        self.cp['c'] = cp_c

        print("Initialised Superheater with the following Temperatures")
        for key, value in self.t.items():
            print(key + str(value))

    def evaluate(self):
        self.t['h_out'] = self.t['h_in'] - ( (self.m['c'] * self.cp['c'] * (self.t['c_out'] - self.t['c_in'])) / (self.m['h'] * self.cp['h']) )
        return self
##############################


pinch_temp = 10  # after economiser
m_gas = 724
cold_input_temp = 15.2

no_of_plots = 5
reheat_temps = np.linspace(100,600,num=5)

def plotTempAgainstMassFlow(max_massflow, reheat_temp,legend_array):
    massflow = np.linspace(0,max_massflow)
    t_h_out = [0] * len(massflow)
    try:
        for i in range(0, len(massflow)):
            x = massflow[i]
            economiser = Economiser(599, cold_input_temp, 349.9, 1.004, 2.1, m_gas, x).evaluate()
            evaporator = Evaporator(economiser.t['h_out'], economiser.t['c_out'] + pinch_temp, 16.5, m_gas, x, 1.004).evaluate()
            superheater1 = Superheater(evaporator.t['h_out'], evaporator.t['c_out'], 565, 1.004, 2.1, m_gas, x).evaluate()
            superheater2 = Superheater(superheater1.t['h_out'], 181.17, reheat_temp, 1.004, 2.1, m_gas, x).evaluate()
            t_h_out[i] = superheater2.t['h_out']
    except HeatExchangerError:
        print("Heat exchanger error!")
        domain = massflow[0:i]
        t_h_out = t_h_out[0:i]
    legend_array.append("reheat temp = "+str(reheat_temp)+" C")
    plt.plot(domain, t_h_out)


legend_array = []

for reheat_temp in reheat_temps:
    plotTempAgainstMassFlow(250, reheat_temp, legend_array)


plt.ylabel("Flue Gas Outlet Temperature [C]")
plt.xlabel("Steam Mass Flow Rate [kg/s]")
plt.title("HRSG Flue Gas Outlet Temperature for Various Reheat Temperatures")
plt.legend(legend_array + ["Theoretical Adiabatic Minimum Reachable Temperature"])
plt.show()
