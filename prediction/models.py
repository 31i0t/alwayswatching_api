from alwayswatching_project.views import posts
from operator import pos
from django.db import models
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

import numpy as np

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense

from tensorflow.keras.callbacks import EarlyStopping

import random

class NewPostsManager():
    postTagsDf = pd.read_csv(r'alwayswatching_project/post_tags.csv')

    def contentBasedRecommender(self, userInterestTags, recentPostIds):
        userInterestsDf = pd.DataFrame(n * 10 for n in userInterestTags).values
        userInterestsDf = userInterestsDf.reshape(1, -1)

        for i in range(len(recentPostIds)):
            recentPostIds[i] = recentPostIds[i] - 1

        postTagsDf = self.postTagsDf.copy()

        postTagsDf.drop(recentPostIds, 0, inplace=True)

        postInterestsSimilarities = cosine_similarity(userInterestsDf, postTagsDf)

        postInterestsSimilaritiesDf = pd.DataFrame(postInterestsSimilarities.T, index=postTagsDf.index, columns=["similarity"])
        sortedSimilarityDf = postInterestsSimilaritiesDf.sort_values(by="similarity", ascending=False)

        postIds = []
        firstTier = random.sample(range(20), 4)
        secondTier = random.sample(range(20, 600), 6)
        thirdTier = random.sample(range(600, len(sortedSimilarityDf)), 1)

        postIndicies = firstTier + secondTier + thirdTier

        for postIdx in postIndicies:
            postIds.append(int(sortedSimilarityDf.index[postIdx]) + 1)

        random.shuffle(postIds)

        return postIds

    def predictionsRegressor(self, timeSpentPerPost, listOfPostTags, newInput):
        enoughDataToSplit = len(timeSpentPerPost) >= 100

        newInput = np.array(newInput)

        predictors = np.array(listOfPostTags)
        targets = np.array(timeSpentPerPost)

        early_stopping_monitor = EarlyStopping(patience=2)

        n_cols = predictors.shape[1]

        model = Sequential()
        model.add(Dense(250, activation='relu', input_shape = (n_cols,)))
        model.add(Dense(250, activation='relu'))
        model.add(Dense(1))

        model.compile(optimizer='adam', loss='mean_squared_error', metrics=['accuracy'] if enoughDataToSplit else None)
        model.fit(predictors, targets, validation_split=0.3 if enoughDataToSplit else 0, epochs=50, callbacks=[early_stopping_monitor] if enoughDataToSplit else None, verbose=0)

        return model.predict(newInput)



class ParsedPredictionDataManager():
    def parseInputData(self, postsArray):
        parsedDataObj = {}
        timeSpentPerPost = []
        listOfPostTags = []
        engagementHistory = [0] * 10

        for post in postsArray:
            if post['timeSpent'] == 0: continue
            timeSpentOnPost = round(post['timeSpent'], 1)
            timeSpentPerPost.append(timeSpentOnPost)
            listOfPostTags.append(post['tags'])

            for i in range(len(post['tags'])):
                engagementHistory[i] += post['tags'][i] * post['timeSpent']
        
        engagementSum = sum(engagementHistory)

        for i, tagSum in enumerate(engagementHistory):
            engagementHistory[i] = round(tagSum / engagementSum, 5)
        
        parsedDataObj['timeSpentPerPost'] = timeSpentPerPost
        parsedDataObj['listOfPostTags'] = listOfPostTags
        parsedDataObj['engagementHistory'] = engagementHistory

        return parsedDataObj
    
    def getViewedPostsData(self, postsArray):
        viewedPostsData = {}
        tagsToPredict = []

        viewedPosts = len(postsArray)
        i = len(postsArray) - 1
        while i > 0 and postsArray[i]['prediction'] == "?" and postsArray[i]['timeSpent'] == 0:
            i -= 1
            viewedPosts -= 1
            tagsToPredict.append(postsArray[i]['tags'])

        viewedPostsData['count'] = viewedPosts
        viewedPostsData['tagsToPredict'] = tagsToPredict

        return viewedPostsData
