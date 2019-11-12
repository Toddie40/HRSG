import iapws.iapws97 as steam
import steam_3_pressure_with_reheat as cycle

class HeatExchanger:
    def __init__(self, t_h_in, t_c_in, t_c_out, m_h_in, m_c_in, c_condition, operating_pressure=1, quality_in=0, quality_out=1):
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
        if c_condition == 'l':
            self.cp['cold'] = 4.2
            self.t['hot out'] = self.t['hot in'] - ( (self.m['cold'] * self.cp['cold']) / (self.m['hot'] * self.cp['hot']) ) * (self.t['cold out'] - self.t['cold in'])
        elif c_condition =='g':
            self.cp['cold'] = 2.1
            self.t['hot out'] = self.t['hot in'] - ( (self.m['cold'] * self.cp['cold']) / (self.m['hot'] * self.cp['hot']) ) * (self.t['cold out'] - self.t['cold in'])
        elif c_condition == 'm':  # liquid-vapor mixture then we need to work out enthalpies
            self.h = {
                'cold in': steam._Region4(operating_pressure, quality_in),
                'cold out': steam._Region4(operating_pressure, quality_out)
            }
            self.t['hot out'] = self.t['hot in'] - ( (self.m['cold']) / (self.m['hot'] * self.cp['hot']) ) * (self.h['cold out'] - self.h['cold in'])



print("########################################################################################")
print("---HRSG and Steam Cycle Analysis---\n")

#define a new steam cycle with the following conditions

steamCycle = cycle.SteamCycle(165,10,4,35,10,60,5,565,15)



fluegas_temp_in = 599
fluegas_massflow = 724
fluegas_cp = 1.004

# sanity check results from cycle

fluegas_temp_out = fluegas_temp_in - ( steamCycle.q_in / (fluegas_massflow * fluegas_cp) )

print("HRSGS fluegas outlet temperature: "+str(fluegas_temp_out))

HP_superheater = HeatExchanger(fluegas_temp_in, steamCycle.T[13], steamCycle.T[14], fluegas_massflow, steamCycle.superheater_3_mass_flow, 'g')
print("\n\tHP Superheater Output temperature: "+str(HP_superheater.t['hot out']))
