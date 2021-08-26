from django.views.decorators.csrf import csrf_exempt
from django.http.response import JsonResponse
from django.core import serializers

import json
import random

from prediction.models import NewPostsManager, ParsedPredictionDataManager

from alwayswatching_project.models.models import DefaultPostsRequest, PostsRequestManager, ParsedPostDataManager, postTags

newPostsManager = NewPostsManager()
parsedPredictionDataManager = ParsedPredictionDataManager()

defaultRequestManager = DefaultPostsRequest()
postsRequestManager = PostsRequestManager()
parsedDataManager = ParsedPostDataManager()


@csrf_exempt
def prediction(request):
    response = {}

    if(request.method == 'GET'):
        posts = defaultRequestManager.getRandom()
        tags = defaultRequestManager.getTags(posts)
        response['posts'] = [vars(post) for post in postsRequestManager.addPosts(posts, tags, {})]
        random.shuffle(response['posts'])

        return JsonResponse(response)

    elif request.method == 'POST':
        inputData = json.loads(request.body)
        viewedPostsData = parsedPredictionDataManager.getViewedPostsData(inputData['posts'])
        parsedData = parsedDataManager.parseInputData(inputData['posts'])
        parsedPredictionData = parsedPredictionDataManager.parseInputData(inputData['posts'][:viewedPostsData['count']])
        posts = newPostsManager.contentBasedRecommender(parsedPredictionData['engagementHistory'], parsedData['ids'][-75:])
        tags = defaultRequestManager.getTags(posts)
        tags.extend(viewedPostsData['tagsToPredict'])

        predictions = newPostsManager.predictionsRegressor(parsedPredictionData['timeSpentPerPost'], parsedPredictionData['listOfPostTags'], tags)
        predictions = [str(round(max(0.1, prediction[0]), 1)) for prediction in predictions]

        postObjects = [vars(post) for post in postsRequestManager.addPosts(posts, tags, {})]

        if len(viewedPostsData['tagsToPredict']):
            overlappedPredictions = []
            predictionsToPop = len(viewedPostsData['tagsToPredict'])
            i = len(predictions) - 1
            while predictionsToPop > 0:
                overlappedPredictions.append(predictions.pop())
                predictionsToPop -= 1
            response['overlappedPredictions'] = overlappedPredictions

        for i, post in enumerate(postObjects):
            post['prediction'] = predictions[i]

        response['posts'] = postObjects

        return JsonResponse(response)
