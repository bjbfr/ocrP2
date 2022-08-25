import pandas as pd

def merge_rows(row,rows):
    """
    merge rows into row
    """
    # select na_columns in row
    na_columns = [col for (i,col) in enumerate(row.columns.values) if pd.isna(row.iloc[0,i])]
    # write in na_columns the non-na values from other rows 
    changed_cols = []
    for col in na_columns: 
         tmp = list(filter(lambda x: not(pd.isna(x)),rows[col].unique()))
         if len(tmp) > 0:
            row[col] = tmp[0]
            changed_cols.append(col)
            
    return (row,changed_cols)
    
def remove_duplicate(df,kcol,merge=True):
    """ 
        -Remove duplicate rows in 'df' based on identifier contained in 'kcol' 
        -The row that is kept is the one with most non-NA columns.
        -If 'merge' is True, we try to replace some of the missing values (in row that is kept) 
         with values coming from the removed rows.
    """
    duplicate = df.groupby(kcol).filter(lambda x: len(x) > 1).groupby(kcol)
    ret = []
    keys = duplicate.groups.keys() 
    for k in keys:
        grp    = duplicate.get_group(k)
        counts = grp.apply(pd.Series.count,axis=1)
        m = counts.max()
        best_rows = counts[counts == m]
        # rid: row index to be kept
        # tbr: row indexes to be removed
        if len(best_rows) == 1:
             rid = best_rows.index 
             tbr = counts[counts < m].index
        else: 
             rid = best_rows.index.take([0])
             tbr = counts[counts < m].index.union(best_rows.index.delete(0))

        row  = df.loc[rid]
        rows = df.loc[tbr]
        if merge:
            (merged_row,changed_cols)  = merge_rows(row,rows) 
            df.loc[rid] = merged_row
            ret.append((merged_row,changed_cols,row,rows))
        else:
            ret.append((row,rows))
        df.drop(tbr,inplace=True)
    return (ret,keys)

def df_shape(df):
    (nb_rows,nb_columns) = df.shape
    print(f'number of rows: {nb_rows} - number of columns: {nb_columns}')
    return (nb_rows,nb_columns)
