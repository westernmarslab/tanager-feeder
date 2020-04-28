import os
os.chdir('/home/khoza/plots_data/')
data=[]
metadata=['Database of origin:,Western Washington University Planetary Spectroscopy Lab','Sample Name','Viewing Geometry']
with open('basalt_weathered_pyroxene.tsv','r') as file:
    for i, line in enumerate(file.readlines()):
        if i==0:
            headers=line.split('\t')
            headers[-1]=headers[-1].strip('\n')
            for i, header in enumerate(headers):
                if i==0:
                    print(header)
                    continue
                sample_name=header.split('(')[0]
                # i=header.split('i=')[1].split(' ')[0]
                # e=header.split('e=')[1].split(')')[0]
                geom=header.split('(')[1].strip(')')
                metadata[1]+=','+sample_name
                metadata[2]+=','+geom

            metadata.append('')
            metadata.append('Wavelength')

        else:
            data.append(line.replace('\t',','))
            
with open('data_1_10.csv','w+') as file:
    for line in metadata:
        print(line)
        file.write(line)
        file.write('\n')
    for line in data:
        file.write(line)


            

    