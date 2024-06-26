# -*- coding: utf-8 -*-
"""fake_job_postings.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1WfMpMH_rc1KO4_wgp8srI_E_hGTvNO3c
"""



!pip install pyspark

from pyspark.ml.feature import *
from pyspark.sql.functions import *
from pyspark.sql.types import *
from pyspark.ml.classification import *
from pyspark.ml.evaluation import *
from pyspark.ml.tuning import *
from pyspark.ml import Pipeline

from pyspark.sql import SparkSession

# Create a SparkSession
spark = SparkSession.builder.getOrCreate()

from IPython.display import display, HTML
display(HTML("<style>pre { white-space: pre !important; }</style>"))

"""# read data"""

df = spark.read.option("header", "true").csv("fake_job_postings.csv")

df.cache()

df.printSchema()

df = df.drop('job_id')

print((df.count(), len(df.columns)))

def null_value_calc(df):
    null_columns_counts = []
    numRows = df.count()
    for k in df.columns:
        nullRows = df.where(col(k).isNull()).count()
        if(nullRows > 0):
            temp = k,nullRows,(nullRows/numRows)*100
            null_columns_counts.append(temp)
    return(null_columns_counts)

null_columns_calc_list = null_value_calc(df)
spark.createDataFrame(null_columns_calc_list, ['Column_Name', 'Null_Values_Count','Null_Value_Percent']).show()

"""#Drop any row that's not classified fraud or not (0,1)

"""

df2 = df.filter("fraudulent IN('0','1')")
# Make sure it worked
df2.groupBy("fraudulent").count().orderBy(col("count").desc()).show(truncate=False)

df3 = df2.sampleBy("fraudulent", fractions={"0": 0.4, "1": 1.0}, seed=10)
# QA again
df3.groupBy("fraudulent").count().show(truncate=False)

from pyspark.sql.functions import *

def null_value_calc(df):
    null_columns_counts = []
    numRows = df.count()
    for k in df.columns:
        nullRows = df.where(col(k).isNull()).count()
        if(nullRows > 0):
            temp = k,nullRows,(nullRows/numRows)*100
            null_columns_counts.append(temp)
    return(null_columns_counts)

null_columns_calc_list = null_value_calc(df3)
spark.createDataFrame(null_columns_calc_list, ['Column_Name', 'Null_Values_Count','Null_Value_Percent']).show()



"""Fraudulent: The Target


#Since the percentage of nulls might seem alot more to be dropped, we may ignore the unnecessary columns and only consider the important ones only


Include only:

*   Location: Frauds may be associated with some locations over others
*   Description: Contains the actual text of the job.
* Fraudulent: The Target





"""

# remove unwanted columns
# How about by subset by just the vars we need for now.
filtered = df3.na.drop(subset=["Location", "description", "fraudulent"])
print((filtered.count(), len(filtered.columns)))

# now change the data type to be integer after cleaning the misleading data in those columns
filter2 = filtered.withColumn("fraudulent", df["fraudulent"].cast(IntegerType())) \
        .withColumn("has_questions", df["has_questions"].cast(IntegerType())) \
        .withColumn("has_company_logo",df.has_company_logo.cast(IntegerType())) \
        .withColumn("telecommuting",df.telecommuting.cast(IntegerType()))



print(filter2.printSchema())

filter2.limit(5).toPandas()



"""#Check class balance
* The data is obviously imbalanced and that may be treated in different ways like:

1. Change the accuracy metric to be able to monitor both false and true positives and negatives
2. K-Fold Cross Validation
3.  Sampling the data (delete some of the data labeled 0 to maintain balance)
"""

filter2.groupBy("fraudulent").count().orderBy(col("count").desc()).show(truncate=False)

tot = filter2.count()
filtered.groupBy("fraudulent").count().withColumnRenamed('count', 'cnt_per_group').withColumn('perc_of_count_total', (col('cnt_per_group') / tot) * 100 ).show(100)

"""#Preprocessing the data, both labels and text"""

selected_df = filter2.select("description", "fraudulent")

selected_df.printSchema()

"""#Apply the text hashing techniques:


*   HashingTF
*   Word2Vec
*   TF-IDF


"""

from pyspark.ml.feature import Tokenizer, StopWordsRemover, CountVectorizer, IDF
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import BinaryClassificationEvaluator
from pyspark.ml.classification import NaiveBayes

selected_df.cache()

# Define tokenizer
tokenizer = Tokenizer(inputCol="description", outputCol="words")

# Define stop words remover
stop_words_remover = StopWordsRemover(inputCol="words", outputCol="filtered_words")

count_vectorizer = CountVectorizer(inputCol="filtered_words", outputCol="raw_features")

idf = IDF(inputCol="raw_features", outputCol="tf_idf_features")

# Define Naive Bayes classifier
nb = NaiveBayes(featuresCol="tf_idf_features", labelCol="fraudulent")

# Split data into training and testing sets
train_data, test_data = selected_df.randomSplit([0.8, 0.2], seed=42)

from pyspark.ml import Pipeline

pipeline = Pipeline(stages=[tokenizer, stop_words_remover, count_vectorizer, idf, nb])

# Train the model
model = pipeline.fit(train_data)

predictions = model.transform(test_data)

evaluator = MulticlassClassificationEvaluator(predictionCol="prediction", labelCol="fraudulent", metricName="f1")
f1_score = evaluator.evaluate(predictions)
print("F1 Score:", f1_score)

# using DL

"""# using DL"""

import torch
from torch.utils.data import DataLoader, TensorDataset
from transformers import BertTokenizer, BertForSequenceClassification
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd
import re

df = pd.read_csv('fake_job_postings.csv')

random_sample = df.sample(n=1000)





df2 = random_sample[['description', 'fraudulent']]

df2.info()

import re
def process_text(text):
    news = re.sub(r'[^a-zA-Z\s]','',text)
    lo_news = news.lower()
    return lo_news

df2['description'] = df2['description'].apply(process_text)

import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.utils import pad_sequences
from tensorflow.keras.layers import LSTM,GRU,Bidirectional,Dense,Embedding
from tensorflow.keras import Sequential

# passing object
tk = Tokenizer()

#fit the text into the tokenizer
tk.fit_on_texts(df2['description'])

#integer encoding
seq = tk.texts_to_sequences(df2['description'])

#padded the vector to equalize the dimenstion
vec = pad_sequences(seq,padding='post',maxlen=50)

# split features and target variable
import numpy as np
x = np.array(vec)
y = np.array(df2['fraudulent'])

from sklearn.model_selection import train_test_split
x_train,x_test,y_train,y_test = train_test_split(x,y,test_size=0.15,random_state=32)

# Building model using sequential API

model = Sequential()
model.add(Embedding(input_dim=len(tk.word_index)+1,output_dim=100,input_length=50))
model.add(Bidirectional(LSTM(units=100)))
model.add(Dense(1,activation='sigmoid'))

model.compile(optimizer='adam',loss='binary_crossentropy',metrics=['accuracy'])

history = model.fit(x_train,y_train,epochs=2,batch_size=32,
                    validation_data=(x_test,y_test))

model.evaluate(x_test,y_test)

