import matplotlib .pyplot as plt
import numpy as np

def main():
    plt.close('all')
    
    correction_coefficients=[]

    x,y,p=get_data('AutoSpec/autospec/spec_correction_i0.csv')
    x1,y1,p1=get_data('AutoSpec/autospec/spec_correction_i0_off_plane.csv')
    x2,y2,p2=get_data('AutoSpec/autospec/spec_correction_i0_405nm.csv')
    fit=fit_data(x, p)
    correction_coefficients.append({0:p})
    ax=plot_data(x,y,fit,'i=0','Emission (degrees)','Reflectance')

    

    x,y,p=get_data('AutoSpec/autospec/spec_correction_i30.csv')
    fit=fit_data(x, p)
    correction_coefficients.append({-30:p})
    #plot_data(x,y,fit,'i=-30','Emission (degrees)','Reflectance')
    ax.plot(x,fit,label='incidence=-30 degrees')
    

    
    x,y,p=get_data('AutoSpec/autospec/spec_correction_i45.csv')
    fit=fit_data(x, p)
    correction_coefficients.append({-45:p})
    #plot_data(x,y,fit,'i=-45','Emission (degrees)','Reflectance')
    ax.plot(x,fit,label='incidence=-45 degrees')
    

    
    
    x,y,p=get_data('AutoSpec/autospec/spec_correction_i60.csv')
    x1,y1,p1=get_data('AutoSpec/autospec/spec_correction_i60_off_plane.csv')
    x2,y2,p2=get_data('AutoSpec/autospec/spec_correction_i60_405nm.csv')
    fit=fit_data(x, p)
    correction_coefficients.append({-60:p})
    #plot_data(x,y,fit,'i=-60','Emission (degrees)','Reflectance', image='AutoSpec/autospec/ineg_60.png')
    ax.plot(x,fit,label='incidence=-60 degrees')
    ax.legend()
    # 
    # plt.figure()
    # ax=plt.axes()
    # ax.plot(x,y,label='680 nm')
    # ax.plot(x1,y1,label='680 nm off-plane')
    # ax.plot(x2,y2,label='405 nm off-plane')
    # ax.grid()
    # ax.set_title('i=60')
    # ax.legend()
    #plt.show()
    
    #return
    file='/home/khoza/Spectroscopy/data/DF_overview.csv'
    file2='/home/khoza/Spectroscopy/data/DF_overview_corrected.csv'
    wavelengths, reflectance, labels=load_csv(file)
    
    corrected_data=[]
    corrected_data.append(wavelengths)
    j=0
    k=0
    
    while k<len(labels):
        if 'White Reference' in labels[k] and 'Uncorrected' not in labels[k]:
            corrected_data.insert(j+1,reflectance[k])
            labels.insert(j+1,'Uncorrected WR ('+labels[k].split('(')[1])
            reflectance.insert(j,reflectance[k])
            k=k+1
            j=j+1
        k=k+1
    for k in range(len(labels)):
        if 'Uncorrected' in labels[k]:
            continue
        e,i,g=get_e_i_g(labels[k])
        # print('e='+str(e))
        # print('i='+str(i))
        closest_incidence=0
        closest_incidence_index=0
        for n, dict in enumerate(correction_coefficients):
            for incidence in dict: #there is only one.
                if np.abs(-1*np.abs(i)-incidence)<np.abs(-1*np.abs(i)-closest_incidence):
                    closest_incidence=incidence
                    closest_incidence_index=n
        # print('correction incidence = '+str(closest_incidence))
        if np.abs(i)-np.abs(closest_incidence)==0:
            left=closest_incidence
            left_index=closest_incidence_index
            right=closest_incidence
            right_index=closest_incidence_index
        elif np.abs(i)>np.abs(closest_incidence) and closest_incidence_index<len(correction_coefficients)-1:
    #If the incidence angle for the data at is less than the incidence angle in our correction coefficient dict, and there is another incidence angle in the correction coefficient dict on the other side, then we'll use that to interpolate.
            left=closest_incidence
            left_index=closest_incidence_index
            for incidence in correction_coefficients[closest_incidence_index+1]: #there is only one.
                right=incidence
                right_index=closest_incidence_index+1
        elif np.abs(i)<np.abs(closest_incidence) and closest_incidence_index>0:
            right=closest_incidence
            right_index=closest_incidence_index
            for incidence in correction_coefficients[closest_incidence_index-1]: #there is only one.
                left=incidence
                left_index=closest_incidence_index-1
        # elif closest_incidence_index==0:
        #     for incidence in correction_coefficients[0]: #there is only one.
        #         left=incidence
        #         left_index=closest_incidence_index
        #         right=incidence
        #         right_index=closest_incidence_index
        # print(left)
        # print(right)
        if i<0:
            left_correction=fit_data(e,correction_coefficients[left_index][left])
            right_correction=fit_data(e,correction_coefficients[right_index][right])
        else:
            left_correction=fit_data(-1*e,correction_coefficients[left_index][left])
            right_correction=fit_data(-1*e,correction_coefficients[right_index][right])
        # print(left_correction)
        # print(right_correction)
        if right!=left:
            slope=(right_correction-left_correction)/(np.abs(right)-np.abs(left))
            #print(slope)
            correction=left_correction+(np.abs(i)-np.abs(left))*slope
        else:
            correction=left_correction
        corrected_data.append(np.array(reflectance[k])*correction)
        
        # print('correction factor = '+str(correction))
        # plot_data(wavelengths, reflectance[k], np.array(reflectance[k])*correction, 'i='+str(i)+' e='+str(e),'Wavelength (nm)','Reflectance')

    corrected_data_zip=zip(*corrected_data)
    corrected_data=np.array(list(corrected_data_zip))
    # for k, line in enumerate(corrected_data):
    #     if k<10: print(line)
    write_corrected_data(file,file2,corrected_data,labels)
    #plt.show()

def get_e_i_g(label): #Extract e, i, and g from a label.
    try:
        i=int(label.split('i=')[1].split(' ')[0])
        e=int(label.split('e=')[1].strip(')'))
    except:
        print('Could not load geometry information for:')
        print(label)
        return
    if i<=0:
        g=e-i
    else:
        g=-1*(e-i)
    return e, i, g
    
def write_corrected_data(file1,file2,corrected_data,labels):
    headers=[]
    with open(file1,'r') as f:
        line=f.readline()
        headers.append(line)
        while line.split(',')[0].lower()!='wavelength' and line !='' and line.lower()!='wavelength\n':
            line=f.readline()
            headers.append(line)
    k=0
    n=1
    uncorrected_names=[]
    while k<len(labels):
        if 'Uncorrected' in labels[k]:
            print(labels[k])
            e,i,g=get_e_i_g(labels[k])
            for j, line in enumerate(headers):
                line=line.split(',')
                if line[0]=='Viewing Geometry':
                    line.insert(n,'i='+str(i)+' e='+str(e))
                elif line[0]=='Sample Name':
                    line.insert(n,labels[k].split(' (')[0])
                headers[j]=','.join(line)
            n+=1
        k+=1
    with open(file2,'w+') as f:
        for line in headers:
            f.write(line)
        for line in corrected_data:
            f.write(','.join(str(n) for n in line)+'\n')
        
    
def load_csv(file):
    skip_header=1
    with open(file,'r') as file2:
        line=file2.readline()
        i=0
        while line.split(',')[0].lower()!='wavelength' and line !='' and line.lower()!='wavelength\n': #Formatting can change slightly if you edit your .csv in libreoffice or some other editor, this captures different options. line will be '' only at the end of the file (it is \n for empty lines)
            i+=1
            if line[0:11]=='Sample Name':
                labels=line.split(',')[1:]
                labels[-1]=labels[-1].strip('\n')
                labels_found=True #
            elif line[0:16]=='Viewing Geometry':
                for i, geom in enumerate(line.split(',')[1:]):
                    geom=geom.strip('\n')
                    labels[i]+=' ('+geom+')'
            skip_header+=1
            line=file2.readline()
    data = np.genfromtxt(file, skip_header=skip_header, dtype=float,delimiter=',',encoding=None,deletechars='')
    data=zip(*data)
    wavelengths=[]
    reflectance=[]
    
    for i, d in enumerate(data):
        if i==0: wavelengths=d #the first column in my .csv (now first row) was wavelength in nm. Exclude the first 100 values because they are typically very noisy.
        else: #the other columns are all reflectance values
            d=np.array(d)
            reflectance.append(d)
            #d2=d/np.max(d) #d2 is normalized reflectance
            #reflectance[0].append(d)
            #reflectance[1].append(d2)
            
    return wavelengths, reflectance, labels
    
def plot_data(x,y,y2, title,xlabel,ylabel,image=None):
    fig=plt.figure(figsize=(5,3))
    ax=plt.axes()
    # if image!=None:
    #     im = plt.imread(image)
    #     ax.imshow(im,extent=[-60,60,-60,60])
    #ax.plot(x,y)
    ax.plot(x,y2,label='incidence=0 degrees')
    ax.grid()
    ax.set_title(title,fontsize=14)
    ax.set_ylabel(ylabel,fontsize=12)
    ax.set_xlabel(xlabel,fontsize=12)
    return ax
    plt.tight_layout()
    #fig.savefig('AutoSpec/autospec/'+title+'.png', transparent=True)
    

    
def get_data(file):
    data=np.genfromtxt(file,delimiter=',')
    data=zip(*data)
    for i, d in enumerate(data):
        if i==0:
            x=np.array(d)
        else:
            y=np.array(d)/0.16
    
    p=np.polyfit(x,y,10)
    
    return x,y,p

def fit_data(x, p):
    fit=p[10]+p[9]*x+p[8]*x**2+p[7]*x**3+p[6]*x**4+p[5]*x**5+p[4]*x**6+p[3]*x**7+p[2]*x**8+p[1]*x**9+p[0]*x**10
    return fit
if __name__=='__main__':
    main()