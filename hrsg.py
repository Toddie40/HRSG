import iapws.iapws97 as steam
import steam_3_pressure_with_reheat as cycle
import numpy as np
import collections
from matplotlib import pyplot as plt
import gas_turbine as gt
import csv


class HeatExchanger:
    def __init__(self, t_h_in, t_c_in, t_c_out, m_h_in, m_c_in, c_condition, operating_pressure, quality_in=0, quality_out=1):
        self.t = {
            'hot in': t_h_in,
            'cold in': t_c_in,
            'cold out': t_c_out
        }
        self.m = {
            'hot': m_h_in,
            'cold': m_c_in
        }
        self.cp = {
            'hot': 1.004,
            'cold': 2.1
        }
        self.h = {}
        self.operating_pressure = operating_pressure

        if c_condition == 'l':
            self.cp['cold'] = 4.2
            self.h['cold in'] = steam._Region1(self.t['cold in'], self.operating_pressure)['h']
            self.h['cold out'] = steam._Region1(self.t['cold out'], self.operating_pressure)['h']
            self.t['hot out'] = self.t['hot in'] - ((self.m['cold']) / (self.m['hot'] * self.cp['hot'])) * (self.h['cold out'] - self.h['cold in'])
        elif c_condition == 'g':
            self.cp['cold'] = 2.1
            self.h['cold in'] = steam._Region2(self.t['cold in'], self.operating_pressure)['h']
            self.h['cold out'] = steam._Region2(self.t['cold out'], self.operating_pressure)['h']
            self.t['hot out'] = self.t['hot in'] - ((self.m['cold']) / (self.m['hot'] * self.cp['hot'])) * (self.h['cold out'] - self.h['cold in'])
        elif c_condition == 'm':  # liquid-vapor mixture then we need to work out enthalpies

            self.h['cold in'] = steam._Region4(operating_pressure, quality_in)['h']
            self.h['cold out'] = steam._Region4(operating_pressure, quality_out)['h']

            self.t['hot out'] = self.t['hot in'] - ((self.m['cold']) / (self.m['hot'] * self.cp['hot'])) * (self.h['cold out'] - self.h['cold in'])
        # heat usage
        self.Q = self.m['cold'] * (self.h['cold out'] - self.h['cold in'])


print("########################################################################################")
print("---HRSG and Steam Cycle Analysis---\n")

# define a new steam cycle with the following conditions

# mass flows kg/s
m1 = 48
m2 = 6
m3 = 54
ma = 39.68  # mass of steam required for CCS

# pressure levels bar
hp = 165
ip = 8
lp = 4


gt_isentropic_turbine_efficiency = .85
gt_isentropic_compressor_efficiency = .85
gt_pressure_ratio = 20.1

steamCycle = cycle.SteamCycle(hp, ip, lp, m1, m2, m3, ma, 565, 15)
steamCycle.SaveResults('steam_data', 'work_data')
gasTurbine = gt.GasTurbine(14.2, 50, 50000, gt_pressure_ratio, gt_isentropic_turbine_efficiency, gt_isentropic_compressor_efficiency)


fluegas_temp_in = gasTurbine.T[4] + 273.15  # K
fluegas_massflow = 724
fluegas_cp = 1.004

print("Temperature of flue gas exiting gas turbine: "+ str(fluegas_temp_in-273.15) +" C")

# sanity check results from cycle

fluegas_temp_out = fluegas_temp_in - (steamCycle.q_in / (fluegas_massflow * fluegas_cp))

print("HRSGS fluegas outlet temperature: "+str(fluegas_temp_out-273.15)+" C")

# Start constructing HRSG by sticking heat exchangers together


# changin to array or heat exchangers to make getting values out easier and as an imporved data structure
# main Superheaters
HRSG = collections.OrderedDict([
    ('HP_superheater', HeatExchanger(fluegas_temp_in, steamCycle.T[13], steamCycle.T[14], fluegas_massflow, steamCycle.superheater_3_mass_flow, 'g', steamCycle.P[13]))
])
HRSG['IP_superheater'] = HeatExchanger(HRSG['HP_superheater'].t['hot out'], steamCycle.T[15], steamCycle.T[10], fluegas_massflow, steamCycle.superheater_2_mass_flow, 'g', steamCycle.P[15])

HRSG['LP_superheater'] = HeatExchanger(HRSG['IP_superheater'].t['hot out'], steamCycle.T[4], steamCycle.T[5], fluegas_massflow, steamCycle.superheater_1_mass_flow, 'g', steamCycle.P[4])

# HP Evaporator
HRSG['HP_evaporator'] = HeatExchanger(HRSG['LP_superheater'].t['hot out'], steamCycle.T[12], steamCycle.T[13], fluegas_massflow, steamCycle.evaporator_3_mass_flow, 'm', operating_pressure=steamCycle.P[12], quality_in=0, quality_out=1)

# Second IP Superheater
HRSG['IP_superheater_2'] = HeatExchanger(HRSG['HP_evaporator'].t['hot out'], steamCycle.T[9], steamCycle.T[15], fluegas_massflow, steamCycle.evaporator_2_mass_flow, 'g', steamCycle.P[9])

# HP Economiser
HRSG['HP_economiser'] = HeatExchanger(HRSG['IP_superheater_2'].t['hot out'], steamCycle.T[11], steamCycle.T[12], fluegas_massflow, steamCycle.economiser_3_mass_flow, 'l', steamCycle.P[11])

# IP Evaporator
HRSG['IP_evaporator'] = HeatExchanger(HRSG['HP_economiser'].t['hot out'], steamCycle.T[8], steamCycle.T[9], fluegas_massflow, steamCycle.evaporator_2_mass_flow, 'm', operating_pressure=steamCycle.P[8], quality_in=0, quality_out=1)

# IP Economiser
HRSG['IP_economiser'] = HeatExchanger(HRSG['IP_evaporator'].t['hot out'], steamCycle.T[7], steamCycle.T[8], fluegas_massflow, steamCycle.economiser_2_mass_flow, 'l', steamCycle.P[7])

# LP Evaporator
HRSG['LP_evaporator'] = HeatExchanger(HRSG['IP_economiser'].t['hot out'], steamCycle.T[3], steamCycle.T[4], fluegas_massflow, steamCycle.evaporator_1_mass_flow, 'm', operating_pressure=steamCycle.P[3], quality_in=0, quality_out=1)

# LP Economiser
HRSG['LP_economiser'] = HeatExchanger(HRSG['LP_evaporator'].t['hot out'], steamCycle.T[2], steamCycle.T[3], fluegas_massflow, steamCycle.economiser_1_mass_flow, 'l', steamCycle.P[2])


def SaveResults(hrsg_filename):
    # generate HRSG table
    # HE, FGin, FGout, STEAMin, STEAM,out, Heat Duty
    hrsgsOutputTableRows = [0]*(len(HRSG)+1)
    hrsgsOutputTableRows[0] = ["Heat Exchanger Surface", "Flue Gas In [K]", "Flue Gas Out [K]", "Water/Steam In [K]", "Water/Steam Out [K]", "Heat Duty [kW]"]

    for index, entry in enumerate(HRSG):
        name = entry
        exchanger = HRSG[entry]
        hrsgsOutputTableRows[index+1] = [name, exchanger.t['hot in'], exchanger.t['hot out'], exchanger.t['cold in'], exchanger.t['cold out'], exchanger.Q]
    try:
        with open(hrsg_filename+".csv", 'w') as csvfile:
            writer = csv.writer(csvfile)

            writer.writerows(hrsgsOutputTableRows)
            return True
    except IOError:
        print("I/O error")
        return False


def PlotPinchgraph(array_of_exchangers, axes, padding=5, title="pinch plot", difference_threshold=50):
    # create x axis
    array_of_exchangers = list(array_of_exchangers.items())
    no_of_exchangers = len(array_of_exchangers)
    x = np.zeros((no_of_exchangers, 2))  # array to hold heat limits per exchanger
    labels = []
    # populate array by iterating through exchngers and grabbing heat duties

    for i in range(0, no_of_exchangers):
        exchanger = array_of_exchangers[no_of_exchangers - 1 - i]
        data = exchanger[1]
        name = exchanger[0]
        labels.append(name)
        if i > 0:
            x[i][0] = x[i-1][1]
        x[i][1] = (data.Q) / 1000 + x[i][0]  # Convert to MW
        cold_temps = [data.t['cold in'], data.t['cold out']]
        hot_temps = [data.t['hot out'], data.t['hot in']]
        diff_1 = np.round(hot_temps[0] - cold_temps[0])
        diff_2 = np.round(hot_temps[1] - cold_temps[1])
        if diff_1 < difference_threshold:  # only plot difference on graph if less that 50 K
            axes.text(x[i][0], cold_temps[0] + padding, str(diff_1))
        if diff_2 < difference_threshold:
            axes.text(x[i][1], cold_temps[1] + padding, str(diff_2))
        axes.plot(x[i], cold_temps)

    # add flue gas temperature
    x = [0, steamCycle.q_in / 1000]  # convert to MW
    T_fg = [array_of_exchangers[no_of_exchangers-1][1].t['hot out'], array_of_exchangers[0][1].t['hot in']]

    axes.plot(x, T_fg, linestyle="dashed", color='r')
    labels.append("Fluegas Temperature")
    axes.legend(labels)
    axes.set_xlabel("Heat Consumption [MW]")
    axes.set_ylabel("Temperature [K]")
    axes.set_title(title)


overallEfficiency = (steamCycle.efficiency + gasTurbine.efficiency) - (steamCycle.efficiency * gasTurbine.efficiency)

print("---------------------------------------\nEfficiency:")
print("\n\tSteam Cycle Efficieny: "+str(np.round(100 * steamCycle.efficiency, 1))+"%")
print("\n\tGas Turbine Efficieny: "+str(np.round(100 * gasTurbine.efficiency, 1))+"%")
print("\n\tTotal plant efficiency: " + str(np.round(100 * overallEfficiency, 1))+"%")

# plotting graphs

# create new figure and axes object
cycle_figures, (gas_ax, steam_ax) = plt.subplots(2, 1)
hrsg_figure, hrsg_ax = plt.subplots(1, 1)

SaveResults("hrsg")
gasTurbine.SaveResults("gas_turbine")
PlotPinchgraph(HRSG, hrsg_ax, title="Heat Consumption versus Temperature diagram for the HRSG", difference_threshold=50)
gasTurbine.PlotResults(gas_ax)
steamCycle.PlotResults(steam_ax, annotated=True, lines=True, linestyle="solid")
plt.show()
