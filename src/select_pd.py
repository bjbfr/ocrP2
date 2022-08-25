def select(x,cols=None,rows=None):
    if x.ndim == 2:    
        return x.loc[
                x.index   if rows is None else rows, 
                x.columns if cols is None else cols
               ]    
    elif x.ndim == 1:
        rows = (rows if rows is not None else cols)
        return x.loc[x.index if rows is None else rows]

def select_i(x,rows=None,cols=None):
    if x.ndim == 2:    
        return x.iloc[
                slice(len(x.index))   if rows is None else rows, 
                slice(len(x.columns)) if cols is None else cols
               ]    
    elif x.ndim == 1:
        rows = (rows if rows is not None else cols)
        return x.iloc[slice(len(x.index)) if rows is None else rows]

