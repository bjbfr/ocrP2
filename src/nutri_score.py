import operator
import numpy as np
from numpy.core.numerictypes import sctype2char
import pandas as pd

class NutriScore:
    # list of components used in nutri-score
    _N_components = ['energy','sugars','saturated-fat','salt']
    _P_components = ['fiber','proteins','fruits-vegetables-nuts']
    
    # columns of the dataset to be considered (generated from the components)
    #columns = { component:component+'_100g' for component in components }
    
    # food categories
    _food_categories = ['solid','beverage','cheese','added_fats']
    
    _edges = {
        'solid':{
            'energy'                 : [335,670,1005,1340,1675,2010,2345,2680,3015,3350],
            'sugars'                 : [4.5,9,13.5,18,22.5,27,31,36,40,45],
            'saturated-fat'          : [1,2,3,4,5,6,7,8,9,10], 
            'salt'                   : ([90,180,270,360,450,540,630,720,810,900],{'m':1.0/1000}),
            'fiber'                  : [0.9,1.9,2.8 ,3.7,4.7],
            'proteins'               : [1.6,3.2,4.8,6.4,8.0],
            'fruits-vegetables-nuts' : [40,40,60,-1,-1,80]
        },
        'beverage':{
            'energy'                 : [0,30,60,90,120,150,180,210,240,270],
            'sugars'                 : [0 ,1.5,3 ,4.5,6 ,7.5,9,10.5,12,13.5],
            'fruits-vegetables-nuts' : [40,-1,60,-1,80,-1,-1,-1,-1,-1,-1]
        },
        'added_fats':{
            'saturated-fat': ([10,16,22,28,34,40,46,52,58,64],{'op':'<'})
        }
    }
   
    _df_columns = {
        'energy':'energy_100g',                 
        'sugars':'sugars_100g',                 
        'saturated-fat':'saturated-fat_100g',          
        'salt':'sodium_100g',                   
        'fiber':'fiber_100g',                  
        'proteins':'proteins_100g',               
        'fruits-vegetables-nuts':'fruits-vegetables-nuts_100g',     
        'added_fats':{       
            'saturated-fat':['saturated-fat_100g','monounsaturated-fat_100g','polyunsaturated-fat_100g'] 
         }
        }
    
    _bins = {}

    @staticmethod
    def _make_bins(edges):
        def gen_bins(edges,**kwargs):
            op = kwargs.get('op','<=')
            m  = kwargs.get('m',1.0) 
            ret = [(i,m*v) for (i,v) in enumerate(edges) ]
            return (op,ret)

        ret = {
            cat: {
                component:(
                    gen_bins(edges) if type(edges) is list
                    else gen_bins(edges[0],**(edges[1]))
                )
                for (component,edges) in values.items() 
            }
           for (cat,values) in edges.items()
        }
        return ret
    
    @classmethod
    def initialize(cls):
        cls._bins = NutriScore._make_bins(cls._edges)

    @classmethod
    def _component_bins(cls,component,category):
        cat_bins = cls._bins.get(category,None)
        bins = None
        if cat_bins is not None:
            bins = cat_bins.get(component,None)
        if bins is None:
            cat_bins = cls._bins.get('solid',None)
            bins = cat_bins.get(component,None)
        return bins

    @classmethod
    def _component_score(cls,value,component,category):
        bins = cls._component_bins(component,category)
        op_str, values = bins
        #print(f'values: {values}')
        op = operator.le
        if op_str == '<':
            op = operator.lt
        for (score,edge) in values:
            if edge != -1.0:
                if op(value,edge):
                    return score
        return len(values)

    @classmethod
    def _get_category(cls,row):
        if pd.isna(row['pnns_groups_2']):
            return None
        if  row['pnns_groups_2'].find('beverage') != -1 or\
            row['pnns_groups_2'] == 'Fruit nectars':
            return "beverage"
        elif row['pnns_groups_2'] == 'Cheese':
            return 'cheese'
        elif row['pnns_groups_2'] == 'Fats': 
            return 'added_fats'
        return 'solid'
   
    @classmethod
    def _get_df_column(cls,component,category):
        cat_columns = cls._df_columns.get(category)
        if cat_columns is None:
            return cls._df_columns.get(component)
        else:
            df_column = cat_columns.get(component)
            if df_column is None:
                return cls._df_columns.get(component)
            else:
                return df_column

    @classmethod
    def _get_value(cls,row,component,category):
        col = cls._get_df_column(component,category)
        if type(col) == list:
            return row[col].sum()
        else:
            v = row[col]
            if np.isnan(v):
                return 0.0
            else:
                return v

    @classmethod
    def _compute_score(cls,row,category):
        if category is None:
            category = cls._get_category(row)
            if category is None:
                return np.nan
        #computation of score
        f = lambda c: cls._component_score(cls._get_value(row,c,category),c,category)
        #N points
        debug1 =list(map(f,cls._N_components))
        #print(f'N points: {debug1}')
        N_points = sum(debug1)
        #print(f'N point: {N_points}')
        # fruit vegetable points
        fruit_vegetable = f('fruits-vegetables-nuts')
        # choose P components
        P_components = cls._P_components
        threshold = 10 if category == 'beverage' else 5
        if N_points >= 11 and fruit_vegetable < threshold:
            P_components = list(filter(lambda x: x not in ['proteins'],cls._P_components))
       
        debug2 = list(map(f,P_components))
        #print(f'P points: {debug2}')
        P_points = sum(debug2)
        #print(f'P point: {P_points}')
        return N_points - P_points 


    @classmethod 
    def compute(cls,df,res_column='NutriScore',category=None):
        if res_column is None: 
            return df.apply(lambda r: cls._compute_score(r,category),axis=1)
        else:
            df[res_column] = df.apply(lambda r: cls._compute_score(r,category),axis=1)


class NutriGrade:
    @classmethod
    def _get_category(cls,row):
        if pd.isna(row['pnns_groups_2']):
            return None
        if  row['pnns_groups_2'].find('beverage') != -1 or\
            row['pnns_groups_2'] == 'Fruit nectars':
            return "beverage"
        return 'non-beverage'
    
    @classmethod
    def _compute_grade(cls,row,score_col,category):
        if category is None:
            category = cls._get_category(row)
        score = row[score_col]
        if category is None or category == 'beverage' or pd.isna(score):
            return np.nan
        else:
            if score <= -1 and score >= -15:
                return 'a'
            elif score <= -2:
                return 'b'
            elif score <= 10:
                return 'c'
            elif score <= 18:
                return 'd'
            elif score <= 40:
                return 'e'
            else: 
                return np.nan

    @classmethod
    def compute(cls,df,score_col,res_column='NutriGrade',category=None):
        if res_column is None: 
            return df.apply(lambda r: cls._compute_grade(r,score_col,category),axis=1)
        else:
            df[res_column] = df.apply(lambda r: cls._compute_grade(r,score_col,category),axis=1)
