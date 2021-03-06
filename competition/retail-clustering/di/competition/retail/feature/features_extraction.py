'''
Created on Jul 14, 2016

@author: yehia
'''

import numpy as np
import pandas as pd
from _functools import reduce
from sklearn.cluster import KMeans
from sklearn.preprocessing.data import MinMaxScaler
import sys

def isNight(x):
    if (x is not None):
        if x.hour >=18 and x.hour <= 24:
            return 1
    return 0

#01-12-2010 8:26
dateparse = lambda x: pd.datetime.strptime(x, '%d-%m-%Y %H:%M')

if (len(sys.argv)!=3):
    print('You should provide the input retail dataset (UCI) path (e.g. ~/retail-clustering/dataset/sample.csv) and the centroids output path')
    sys.exit()

retail_ds_file_path = sys.argv[1]
centroids_output = sys.argv[2]

df = pd.read_csv(retail_ds_file_path , parse_dates=['InvoiceDate'],date_parser=dateparse) #parsing the transaction date
retail_ds_file_path
df['trans_value'] = df.apply(lambda row: row['Quantity'] * row['UnitPrice'] , axis = 1)
countries_cat_to_bin_df = pd.get_dummies(df['Country']) #as Country is categorical feature, it should be transformed to binary
distinct_countries = countries_cat_to_bin_df.to_dict().keys()


df = pd.concat([df,countries_cat_to_bin_df], axis=1)

invoice_dates = pd.DatetimeIndex(df['InvoiceDate'])

df['weekday'] = invoice_dates.weekday
df['isWeekEnd'] = df['weekday'].apply(lambda x : 1 if (x == 6 or x==5) else 0) #Sunday or Saturday


invoice_hours = df['InvoiceDate'].apply(lambda x : isNight(x))
df['isNight'] = invoice_hours

customer_dataframes = []

df_by_customer = df.groupby(['CustomerID'],as_index=False)

df_med_basket_size = df_by_customer['Quantity'].median() #median to exclude the outlier shoppers (e.g. group purchase,etc ...)
customer_dataframes.append(df_med_basket_size)

#print (df_med_basket_size)

df_med_trans_value = df_by_customer['trans_value'].median() 
customer_dataframes.append(df_med_trans_value)


for country in distinct_countries:
    customer_dataframes.append(df_by_customer[country].mean())

customer_dataframes.append(df_by_customer["StockCode"].count())
customer_dataframes.append(df_by_customer["isNight"].mean())
customer_dataframes.append(df_by_customer["isWeekEnd"].mean())

#merging all the customers features
customer_final_df = reduce(lambda left,right: pd.merge(left,right,on='CustomerID'), customer_dataframes)

np_dataset_array = customer_final_df.values
cust_original_space = [x for x in np_dataset_array]
features_values = np.array([x[1:] for x in np_dataset_array])
features_values = MinMaxScaler().fit_transform(features_values) #normalizing the data as KMeans is distance based sensitive (i.e. one un-normalized fetaure can dominate the distance function)
cluster_model = KMeans(n_clusters=5)
cluster_model.fit(features_values)
closest_centroids = cluster_model.predict(features_values) #assigning each customer to the closest centroid

#printing the clustering output
f = open(centroids_output,'w')
f.write("Cluster_ID," + (",".join(customer_final_df.columns.values))) #writing header
f.write("\n")
for cust_index in range(0,len(cust_original_space)):
    f.write(str(closest_centroids[cust_index]))
    f.write(",")
    f.write(",".join(map(str,cust_original_space[cust_index])))
    f.write("\n")
f.close()

