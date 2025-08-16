import decaylanguage as dl

from particle.pdgid import is_baryon, is_lepton, is_quark, is_diquark
from particle.converters.bimap import DirectionalMaps
EvtGen2PDGID, _ = DirectionalMaps("EvtGenName", "PDGID")
_EvtGen2LatexNameMap, _Latex2EvtGenNameMap = DirectionalMaps("EvtGenName", "LaTexName")

from particle import Particle

import pandas as pd
pd.set_option('display.max_colwidth', None)
pd.set_option('display.float_format', '{:.2f}'.format)

def get_stable(parser, additional_stable):
    list_of_lists = parser.list_decay_modes('B+')
    flattened_set = set([val for sublist in list_of_lists for val in sublist])

    consider_as_stable = []

    print('\n')

    for i in flattened_set:
        try:
            if is_baryon(EvtGen2PDGID[i]):
                consider_as_stable.append(i)
            elif is_lepton(EvtGen2PDGID[i]):
                consider_as_stable.append(i)
            elif is_quark(EvtGen2PDGID[i]):
                consider_as_stable.append(i)
            elif is_diquark(EvtGen2PDGID[i]):
                consider_as_stable.append(i)
        except:
            print(f'Not sure about {i}, not considering as stable.')
            continue
            
    for i in additional_stable:
        consider_as_stable.append(i)
        
    consider_as_stable = tuple(consider_as_stable)

    print('\n')

    return consider_as_stable

fei_modes = {
    1: {'fsp': ['anti-D0', 'pi+'], 'file_name': 'D_pi'},
    2: {'fsp': ['anti-D0', 'pi+', 'pi0'], 'file_name': 'D_pi_pi0'},
    3: {'fsp': ['anti-D0', 'pi+', 'pi0', 'pi0'], 'file_name': 'D_pi_2pi0'},
    4: {'fsp': ['anti-D0', 'pi+', 'pi+', 'pi-'], 'file_name': 'D_3pi'},
    5: {'fsp': ['anti-D0', 'pi+', 'pi+', 'pi-', 'pi0'], 'file_name': 'D_3pi_pi0'},
    6: {'fsp': ['anti-D*0', 'pi+'], 'file_name': 'Dst_pi'},
    7: {'fsp': ['anti-D*0', 'pi+', 'pi0'], 'file_name': 'Dst_pi_pi0'},
    8: {'fsp': ['anti-D*0', 'pi+', 'pi0', 'pi0'], 'file_name': 'Dst_pi_2pi0'},
    9: {'fsp': ['anti-D*0', 'pi+', 'pi+', 'pi-'], 'file_name': 'Dst_3pi'},
    10: {'fsp': ['anti-D*0', 'pi+', 'pi+', 'pi-', 'pi0'], 'file_name': 'Dst_3pi_pi0'},
    11: {'fsp': ['D-', 'pi+', 'pi+'], 'file_name': 'Dm_2pi'},
    12: {'fsp': ['D-', 'pi+', 'pi+', 'pi0'], 'file_name': 'Dm_2pi_pi0'},
    13: {'fsp': ['D*-', 'pi+', 'pi+'], 'file_name': 'Dstm_2pi'},
    14: {'fsp': ['D*-', 'pi+', 'pi+', 'pi0'], 'file_name': 'Dstm_2pi_pi0'},
}

additional_stable = ['pi+', 'pi-', 'pi0', 'K+', 'gamma']

b_parser = dl.DecFileParser('DECAY.DEC')
b2_parser = dl.DecFileParser('DECAY_BELLE2.DEC')

b_parser.parse()
b2_parser.parse()

b_consider_as_stable = get_stable(parser=b_parser, additional_stable=additional_stable)
b2_consider_as_stable = get_stable(parser=b2_parser, additional_stable=additional_stable)

def convert_str_to_latex(string):
    daughters = string.split()
    daughters_latex = []
    for i in daughters:
        if i == '-->':
            daughters_latex.append('\\rightarrow')
        elif i == ';':
            daughters_latex.append('$; $')
        elif i == 'gammaF':
            daughters_latex.append('\\gamma^{F}')
        elif i == 'f_0(600)':
            daughters_latex.append('f_0 (600)')
        else:
            try:
                daughters_latex.append(_EvtGen2LatexNameMap[i])
            except:
                print(f'Not found: {i}')
                daughters_latex.append(i)

    return('$' + ' '.join(daughters_latex) + '$')

mode = 10

b_test = b_parser.build_decay_chains_to_specific_fsp_new('B+', stable_particles=b_consider_as_stable,
                                                        fsp=fei_modes[mode]['fsp'])
b2_test = b2_parser.build_decay_chains_to_specific_fsp_new('B+', stable_particles=b2_consider_as_stable,
                                                        fsp=fei_modes[mode]['fsp'])
b_df = dl.DecayChainToTable(b_test).table.sort_values(by='BF', ascending=False, ignore_index=True)
b2_df = dl.DecayChainToTable(b2_test).table.sort_values(by='BF', ascending=False, ignore_index=True)

b_df['BF'] = b_df['BF'] * 1e2
b2_df['BF'] = b2_df['BF'] * 1e2

b_df.columns = b_df.columns.str.replace('BF', 'Belle BF')
b2_df.columns = b2_df.columns.str.replace('BF', 'Belle II BF')

df = b_df.merge(b2_df, on='Decay', how='outer')
df['Decay'] = df.apply(lambda x: convert_str_to_latex(x.Decay), axis=1)
df['Belle_con'] = df.apply(lambda x: x['Belle BF']/df['Belle BF'].sum(), axis=1)
df['Belle_II_con'] = df.apply(lambda x: x['Belle II BF']/df['Belle BF'].sum(), axis=1)

df_latex = df.query('(Belle_con > 0.01) or (Belle_II_con) > 0.01')[['Decay', 'Belle BF', 'Belle II BF']]
df_latex = df_latex.append({'Decay': 'Rest', 
                            'Belle BF': df.query('(Belle_con < 0.01) or (Belle_II_con) < 0.01')['Belle BF'].sum(), 
                            'Belle II BF': df.query('(Belle_con < 0.01) or (Belle_II_con) < 0.01')['Belle II BF'].sum()}, ignore_index=True)
df_latex = df_latex.append({'Decay': 'Sum', 'Belle BF':df['Belle BF'].sum(), 'Belle II BF':df['Belle II BF'].sum()}, ignore_index=True)

print(df_latex.to_latex(index=False, escape=False))
