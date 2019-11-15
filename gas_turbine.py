from CoolProp.CoolProp import PropsSI
from matplotlib import pyplot as plt

T_atm = 8  # Celcius
P_atm = 1  # bar
k = 1.4
cp = 1.004


class GasTurbine:

    def __init__(self, fuel_in, AF, LHV, P_r, n_t=1, n_c=1):
        self.m_air = fuel_in * AF
        self.m_f = fuel_in
        self.m_t = fuel_in * (1 + AF)

        self.T = [0] * 5
        self.T[0] = 'Temperature [C]'

        self.Ts = {}
        self.T[1] = T_atm
        self.Ts['2s'] = isentropic_relation_T(self.T[1], P_r)
        self.T[2] = self.T[1] + (self.Ts['2s']-self.T[1])/n_c
        self.T[3] = ((self.m_f * LHV) / (self.m_t * cp) )+ self.T[2]
        self.Ts['4s'] = isentropic_relation_T(self.T[3], 1/P_r)
        self.T[4] = self.T[3] - n_t * (self.T[3] - self.Ts['4s'])

        self.P = [0] * 5
        self.P[0] = 'Pressure [bar]'
        self.P[1] = P_atm
        self.P[2] = P_r * self.P[1]
        self.P[3] = self.P[2]
        self.P[4] = self.P[1]

        self.s = [0] * 5
        self.s[0] = 'Specific Entropy'
        for index in range(1, len(self.T)):
            self.s[index] = PropsSI('S','P', BarToPa(self.P[index]),'T',ToKelvin(self.T[index]),'Air') /1000  # convert to kJ/kgK


        self.work = {}
        self.work['turbine'] = self.m_t * cp * (self.T[3]-self.T[4])
        self.work['compressor'] = self.m_air * cp * (self.T[2] - self.T[1])
        self.work['heat in'] = self.m_t * cp * (self.T[3] - self.T[2])
        self.work['Net Work'] = ( self.work['turbine'] - self.work['compressor'] )

        self.efficiency = self.work['Net Work'] / self.work['heat in']



    def PlotResults(self, axes,annotated=True):
        axes.plot(self.s[1:],self.T[1:])
        if annotated:

            for i in range(1,len(self.s)):
                axes.annotate(str(i),
                                (self.s[i],self.T[i]),
                                textcoords="offset points",
                                xytext=(0,10),
                                ha='center')
        axes.set_xlabel("Specific Entropy [kJ/kgK]")
        axes.set_ylabel("Temperature [C]")
        axes.set_title("T-S Diagram for Gas Turbine")
        axes.grid()


def BarToPa(p):
        return p * (10 ** 5)

def ToKelvin(t):
        return t + 273.15

def isentropic_relation_T(T_ref, P_ratio):
        return ToKelvin(T_ref) * (P_ratio) ** ((k - 1) / k) - 273.15
