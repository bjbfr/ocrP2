import math
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import missingno as msno

def col_completeness(df,filter,p,wstat,digit):
    """ 
    df: dataframe : the input dataframe
    filter: 'top' (at least) | 'bottom' (at most) | 'slice' (between)
    p: number if filter is 'top'or 'bottom') |  (number,number) if filter is 'slice'  
    wstat: None | 'Count' | 'Percent'
    digit: None | int
    """
    #
    assert filter in ['top','bottom','slice']
    assert wstat is None or wstat in ['Count','Percent']
    #
    nb_rows = len(df)
    s = df.count(axis=0)
    # tbr is the rows of the serie to be removed
    if filter == 'top' or filter == 'bottom':
        b = p*nb_rows
        if filter == 'top':
            tbr = s[s < b].index 
        else:
            tbr = s[s > b].index
    else:
        (pa,pb) = p
        a = pa*nb_rows 
        b = pb*nb_rows
        tbr = s[(s < a) | (s > b)].index 

    s.drop(index=tbr,inplace=True)
    
    if wstat is None:
        return s.index.values
    elif wstat == 'Count':
        return s
    else:
        if digit is None:
            return (s/nb_rows)
        else:
            return s.apply(lambda x: round(x/nb_rows,digit))

def col_filled_at_least(df,p):
    return col_completeness(df,filter='top',p=p,wstat=None,digit=None)

def col_filled_at_most(df,p):
    return col_completeness(df,filter='bottom',p=p,wstat=None,digit=None)

def full_columns(df):
    return col_filled_at_least(df,p=1)

def empty_columns(df):
    return col_filled_at_most(df,p=0)

def col_filled_between(df,p):
    return col_completeness(df,filter='slice',p=p,wstat=None,digit=None)

def col_hist(df):
    axe = sns.histplot(
            data = df.count(axis=0),
            bins = 10,
            stat = 'percent'
    )
    axe.set_title("Columns' fill rate")
    r = np.arange(0,1.1,0.1)*len(df)     
    axe.set_xticks(r)
    axe.set_xticklabels(['0%', '10%', '20%', '30%', '40%', '50%', '60%', '70%', '80%', '90%', '100%'])
    return axe


MAX_SAMPLE=5000
MAX_BARS=50
def msno_bars_matrix(df,bars_matrix,nb_bars=50,sample_size=None,opt_nbbars=True,opt_sample=True,sort=None):    
    (nb_rows,nb_columns) = df.shape

    if opt_sample:
        # if no sample_size given choose 1% of rows size
        sample_size = int(nb_rows*0.01) if sample_size is None else sample_size
    
        # always the sample size to MAX_SAMPLE
        #sample_size = sample_size if sample_size <= MAX_SAMPLE else MAX_SAMPLE
    
    # always limit the number of bars per figure to MAX_BARS
    nb_bars = nb_bars if nb_bars <= MAX_BARS else MAX_BARS
    
    nb_axes = math.ceil(nb_columns/nb_bars)
    
    # optimize the number of bars per axes if allowed
    if opt_nbbars & (nb_columns > nb_bars):
        nb_bars = math.ceil(nb_columns/nb_axes)
    
    # create iteration range z
    x = list(range(0,nb_columns,nb_bars))
    y = list(range(nb_bars-1,nb_columns,nb_bars))
  
    if nb_columns%nb_bars != 0:
           y.append(nb_columns)
        
    z = zip(x,y)

    df = df if sort is None else msno.nullity_sort(df,sort=sort,axis='rows') 
    df = df.sample(sample_size) if opt_sample == True else df 
        
    def display(a,b):
        fig,axe = plt.subplots()
        fig.set_size_inches(20, 12)
        
        if opt_sample is True:
            axe.set_title(f'Hist of non-null values per column (sample size: {sample_size}; columns: {a}-{b-1}) ',fontsize=16)
        else:
            axe.set_title(f'Hist of non-null values per column (columns: {a}-{b-1}) ',fontsize=16)
  
        if bars_matrix == 'bars':
            _ = msno.bar(df.iloc[:,a:b],ax=axe)
        elif bars_matrix == 'matrix':
            _ = msno.matrix(df.iloc[:,a:b],ax=axe)

    for (a,b) in z:
        display(a,b)
        
