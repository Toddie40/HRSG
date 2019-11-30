import hrsg as HRSG
import steam_3_pressure_with_reheat as steam
import gas_turbine as gt
import numpy as np
from matplotlib import pyplot as plt


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

steamCycle = steam.SteamCycle(hp, ip, lp, m1, m2, m3, ma, 565, 15)
gasTurbine = gt.GasTurbine(14.2, 50, 50000, gt_pressure_ratio, gt_isentropic_turbine_efficiency, gt_isentropic_compressor_efficiency)

fluegas_temp_in = gasTurbine.T[4] + 273.15  # K
fluegas_massflow = 724
fluegas_cp = 1.004

print("Temperature of flue gas exiting gas turbine: " + str(fluegas_temp_in-273.15) + " C")

# sanity check results from cycle

fluegas_temp_out = fluegas_temp_in - (steamCycle.q_in / (fluegas_massflow * fluegas_cp))

print("HRSGS fluegas outlet temperature: "+str(fluegas_temp_out-273.15)+" C")

hrsg = HRSG.HRSG(inlet_temp=fluegas_temp_in)


# create superheater and add it to the hrsg

exchangers = []
hpsuperheater = HRSG.HeatExchanger(steamCycle.T[13], steamCycle.T[14], fluegas_massflow, steamCycle.superheater_3_mass_flow, 'superheater', steamCycle.P[13])
hpsuperheater.set_name("HP Superheater")
hrsg.AddExchanger(hpsuperheater)

ipsuperheater = HRSG.HeatExchanger(steamCycle.T[15], steamCycle.T[10], fluegas_massflow, steamCycle.superheater_2_mass_flow, 'superheater', steamCycle.P[15])
ipsuperheater.set_name("IP Superheater")
hrsg.AddExchanger(ipsuperheater)

lpsuperheater = HRSG.HeatExchanger(steamCycle.T[4], steamCycle.T[5], fluegas_massflow, steamCycle.superheater_1_mass_flow, 'superheater', steamCycle.P[4])
lpsuperheater.set_name("LP Superheater")
hrsg.AddExchanger(lpsuperheater)

hrsg.Calculate()


'''
# HP Evaporator
HRSG['HP_evaporator'] = HeatExchanger(HRSG['LP_superheater'].t['hot out'], steamCycle.T[12], steamCycle.T[13], fluegas_massflow, steamCycle.evaporator_3_mass_flow, 'm', operating_pressure=steamCycle.P[12], quality_in=0, quality_out=1)

# Second IP Superheater
#HRSG['IP_superheater_2'] = HeatExchanger(HRSG['HP_evaporator'].t['hot out'], steamCycle.T[9], steamCycle.T[15], fluegas_massflow, steamCycle.evaporator_2_mass_flow, 'g', steamCycle.P[9])

# HP Economiser
HRSG['HP_economiser'] = HeatExchanger(HRSG['HP_evaporator'].t['hot out'], steamCycle.T[11], steamCycle.T[12], fluegas_massflow, steamCycle.economiser_3_mass_flow, 'l', steamCycle.P[11])

# IP Evaporator
HRSG['IP_evaporator'] = HeatExchanger(HRSG['HP_economiser'].t['hot out'], steamCycle.T[8], steamCycle.T[9], fluegas_massflow, steamCycle.evaporator_2_mass_flow, 'm', operating_pressure=steamCycle.P[8], quality_in=0, quality_out=1)

# IP Economiser
HRSG['IP_economiser'] = HeatExchanger(HRSG['IP_evaporator'].t['hot out'], steamCycle.T[7], steamCycle.T[8], fluegas_massflow, steamCycle.economiser_2_mass_flow, 'l', steamCycle.P[7])

# LP Evaporator
HRSG['LP_evaporator'] = HeatExchanger(HRSG['IP_economiser'].t['hot out'], steamCycle.T[3], steamCycle.T[4], fluegas_massflow, steamCycle.evaporator_1_mass_flow, 'm', operating_pressure=steamCycle.P[3], quality_in=0, quality_out=1)

# LP Economiser
HRSG['LP_economiser'] = HeatExchanger(HRSG['LP_evaporator'].t['hot out'], steamCycle.T[2], steamCycle.T[3], fluegas_massflow, steamCycle.economiser_1_mass_flow, 'l', steamCycle.P[2])
'''

overallEfficiency = (steamCycle.efficiency + gasTurbine.efficiency) - (steamCycle.efficiency * gasTurbine.efficiency)

print("---------------------------------------\nEfficiency:")
print("\n\tSteam Cycle Efficieny: "+str(np.round(100 * steamCycle.efficiency, 1))+"%")
print("\n\tGas Turbine Efficieny: "+str(np.round(100 * gasTurbine.efficiency, 1))+"%")
print("\n\tTotal plant efficiency: " + str(np.round(100 * overallEfficiency, 1))+"%")
print("\n\tPlant Net Work: " + str(np.round(gasTurbine.work['Net Work'] + steamCycle.w_net)) + "kW")


hrsg.SaveResults("hrsg")
gasTurbine.SaveResults("gas_turbine")
steamCycle.SaveResults('steam_data', 'work_data')

# create new figure and axes object
gas_ts, gas_ax = plt.subplots(1, 1)
steam_ts, steam_ax = plt.subplots(1, 1)
hrsg_figure, hrsg_ax = plt.subplots(1, 1)

hrsg.PlotPinchgraph(hrsg_ax, title="Heat Consumption versus Temperature diagram for the HRSG", difference_threshold=50)
gasTurbine.PlotResults(gas_ax, type='hs')
steamCycle.PlotResults(steam_ax, type='ts', annotated=True, lines=True, linestyle="solid")

plt.show()
