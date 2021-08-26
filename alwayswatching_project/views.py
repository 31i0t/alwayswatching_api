from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.http.response import JsonResponse

import json
import random

from alwayswatching_project.models.models import DefaultPostsRequest, PostsRequestManager, ParsedPostDataManager

defaultRequestManager = DefaultPostsRequest()
postsRequestManager = PostsRequestManager()
parsedDataManager = ParsedPostDataManager()

@csrf_exempt
def posts(request):
  response = {}

  if(request.method == 'GET'):
    posts = defaultRequestManager.getRandom()
    tags = defaultRequestManager.getTags(posts)
    response['posts'] = [vars(post) for post in postsRequestManager.
      addPosts(posts, tags, {})]

    random.shuffle(response['posts'])
    return JsonResponse(response)

  elif(request.method == 'POST'):
    inputData = json.loads(request.body)
    parsedData = parsedDataManager.parseInputData(inputData['posts'])
    posts = defaultRequestManager.getRandom(parsedData['ids'])
    tags = defaultRequestManager.getTags(posts)
    response['posts'] = [vars(post) for post in postsRequestManager.
      addPosts(posts, tags, parsedData['dynamicContent'])]

    random.shuffle(response['posts'])
    return JsonResponse(response)


