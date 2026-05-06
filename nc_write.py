from netCDF4 import Dataset # Note: python is case-sensitive!
import numpy as np
def initiate(path, data, Dims, GlobParams):
    """
    Basic function for saving data in netCDF format.

    :param path: string containing the path and file name.
    :type path: str       
    :param data: dictonary containing all of the variables and their associated attributes and dimensions.
    :type: numpy dictionary
    :param Dims: dictonary containing all of the dimensional data associated with the data dictionary.
    :type: numpy dictionary
    :param GlobParams: dictonary containing all of the gobal data parameters associated with the data dictionary.
    :type: numpy dictionary   
    """  

    #Opening a file, creating a new Dataset 
    try: ncfile.close()  # just to be safe, make sure dataset is not already open.
    except: pass
    ncfile = Dataset(path,mode='w',format=GlobParams['format']) 
    #print(ncfile)   

    #Creating dimensions 
    #dim = np.zeros(len(Dims))
    for dim_key in Dims:    
        a_dim = ncfile.createDimension(dim_key, Dims[dim_key])

    #time_dim = ncfile.createDimension('time', Dims['time'])     # latitude axis
    for dimensions in ncfile.dimensions.items():
        print(dimensions)  

    #Creating attributes 
    ncfile.setncatts(GlobParams)

    #print(ncfile.title)

    for key, values in data.items():
        if isinstance(values,dict):
            for k_dicts in values:
                #print(k_dicts)
                if k_dicts == 'GlobalAttributes':
                    ncfile.setncatts(values[k_dicts])
        elif isinstance(values,str):
            values
        else:   
            #print(key)
                    var_dirname = key
                    shap_keys = data['Dims'][key]      
                    if values.dtype=='float64':
                        a = ncfile.createVariable(var_dirname, 'f4', shap_keys,zlib=True,complevel=9)
                    elif values.dtype=='int64':
                        a = ncfile.createVariable(var_dirname, 'i4', shap_keys,zlib=True,complevel=9)
                    else:
                        a = ncfile.createVariable(var_dirname,  values.dtype, shap_keys,zlib=True,complevel=9)      
                    for key3 in data['VariableAttributes'][key]:
                        if data['VariableAttributes'][key][key3] == 'unitless':
                            data['VariableAttributes'][key][key3] = '1'      
                        a.UnusedNameAttribute = data['VariableAttributes'][key][key3]      
                        a.renameAttribute("UnusedNameAttribute", key3)
                    #a.missing_value = 'NaN'
                    if len(data[key].shape)==1: 
                        a[:] = values
                    elif len(data[key].shape)==2:   
                        a[:,:] = values
                    elif len(data[key].shape)==3:   
                        a[:,:,:] = values
    # first print the Dataset object to see what we've got
    print(ncfile)
    # close the Dataset.
    ncfile.close(); print('Dataset is closed!')


def append(path, data):

    with Dataset(path,mode='a') as ds:
        current_len = len(ds.dimensions['time'])
        for key, values in data.items():

            if len(data[key].shape)==1: 
                ds.variables[key][current_len:] = values
            elif len(data[key].shape)==2:   
                ds.variables[key][current_len:,:] = values
            elif len(data[key].shape)==3:   
                ds.variables[key][current_len:,:,:] = values
        print(ds)