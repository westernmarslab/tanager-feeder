import numpy as np
import matplotlib.pyplot as plt
import os

def main():
    print(os.getcwd())
    filename='../data/20200313_mastcamz_spectralon.csv'
    converted=convert_data(filename)
    
def convert_data(filename):
    print('convert')
    data=np.genfromtxt(filename, dtype=float, delimiter=',',names=True)
    num_geoms=len(data['incidence']) #could be emission or azimuth or any of the columns since each row represents a different geometry.
    sample_name_string='Sample Name'
    converted_data={}
    for i in data['counter']:
        i=int(i)
        incidence=data['incidence'][i]
        emission=data['emission'][i]
        azimuth=data['azimuth'][i]
        geom=(incidence, emission, azimuth)
        if geom not in converted_data:
            sample_name_string+=', Spectralon'
            
            converted_data[geom]={}
            converted_data[geom]['wavelengths']=[data['bandpass_central'][i]]
            converted_data[geom]['reflectance']=[data['reflectance_factor'][i]]
        else:
            converted_data[geom]['wavelengths'].append(data['bandpass_central'][i])
            converted_data[geom]['reflectance'].append(data['reflectance_factor'][i])

    geom_string='Viewing geometry'
    cols=[]
    for geom in converted_data:
        if len(cols)==0:
            cols.append(converted_data[geom]['wavelengths'])
        cols.append(converted_data[geom]['reflectance'])
        incidence=str(geom[0])
        emission=str(geom[1])
        azimuth=str(geom[2])
        geom_string+=f', i={incidence} e={emission} az={azimuth}'
    
    rows=zip(*cols) 
        
    with open('../data/spectralon.csv', 'w+') as f:
        f.write('Database of origin, Antoine Pommerol\n')
        f.write(sample_name_string+'\n')
        f.write(geom_string+'\n')
        f.write('\n')
        f.write('Wavelength\n')
        i=0
        for row in rows:
            print(len(row))
            print(str(row).strip(')').strip('('))
            f.write(str(row).strip(')').strip('(')+'\n')
            i+=1
            if i>10: break
    
    print('loaded')

    
if __name__=='__main__':
    main()