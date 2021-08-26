from alwayswatching_project.models.rawPostData import rawPostData
from alwayswatching_project.models.rawContentData import rawContentData

import random
import csv

with open(r'alwayswatching_project/post_tags.csv') as tagsArr:
    postTagsCsv = csv.reader(tagsArr, delimiter=',')
    postTags = []
    for i, row in enumerate(tagsArr):
        row = row.strip()
        if i == 0: 
            postTags.append(list(row.split(',')))
            continue
        postTags.append(list(map(int, row.split(','))))


class PostItem():
    """Post item object"""
    def __init__(self, id, tags):
        self.id = id
        self.tags = tags
        self.timeSpent = 0
        self.prediction = '?'
        self.profile = None
        self.username = None
        self.likedByName = None
        self.likes = None
        self.caption = None
        self.comments = None
        self.commentsData = None
        self.dynamicContent = {}
    
    
class PostItemsData():
    """Stores data necessary for generating posts"""
    fields = [
        'profile', 
        'username', 
        'likedByName', 
        'likes', 
        'caption', 
        'comments', 
        'commentsData'
    ]

    postData = rawPostData


class DynamicContentManager():
    """Manages use of dynamic content for populating post objects"""
    def __init__(self, percentage):
        self.cooldown = percentage

    dynamicData = rawContentData

    def populateField(self, contentId, postObj, field, contentHistory):
        previousField = field
        #convert postObj fields into dynamicContent fields
        if field == 'likes' or field == 'comments':
            previousField = field
            field = 'likesAndComments'
        if field == 'commentsData':
            field = 'comments'

        if contentId not in contentHistory:
            contentHistory[contentId] = {}
        if field not in contentHistory[contentId]:
            contentHistory[contentId][field] = []
            if field == 'comments':
                contentHistory[contentId]['commentsData'] = []

        nOptions = len(self.dynamicData[contentId][field])

        fieldHistory = contentHistory[contentId][field]

        #enables postObj:likes/comments to read from the same dynamicContent:likesAndComments
        optionAlreadyChosen = 'likesAndComments' in postObj.dynamicContent and (previousField == 'likes' or previousField == 'comments')

        if optionAlreadyChosen:
            chosenOption = postObj.dynamicContent['likesAndComments']
        else:
            chosenOption = self.cooldownOption(nOptions, self.cooldown, fieldHistory)
            contentHistory[contentId][field].append(chosenOption)
        
        if field != 'comments':
            postObj.dynamicContent[field] = chosenOption

        dataToReturn = self.dynamicData[contentId][field][chosenOption]

        if field == 'likesAndComments':
            if previousField == 'likes':
                dataToReturn = random.randint(dataToReturn[0][0], dataToReturn[0][1])
            elif previousField == 'comments':
                dataToReturn = random.randint(dataToReturn[1][0], dataToReturn[1][1])

        #populate postObj:commentsData from dynamicContent:commentsData/comments
        elif field == 'comments':
            postObj.dynamicContent['commentsData'] = []
            commentsData = self.dynamicData[contentId]['commentsData']
            commentsChosen = []
            for _ in range(dataToReturn):
                commentChosen = self.cooldownOption(len(commentsData), self.cooldown, contentHistory[contentId]['commentsData'])

                postObj.dynamicContent['commentsData'].append(commentChosen)
                commentsChosen.append(commentsData[commentChosen])
                contentHistory[contentId]['commentsData'].append(commentChosen)
            dataToReturn = commentsChosen
        
        if field == 'profile':
            dataToReturn = 'https://cdn.alwayswatching.io/profiles/' + contentId + '/' + str(dataToReturn) + '.jpeg'
    
        return dataToReturn

    def cooldownOption(self, nOptions, cooldown, history, rangeStart=0):
        if not nOptions: return

        options = [i for i in range(rangeStart, rangeStart + nOptions)]
        cooldownPartition = int(round(cooldown * nOptions))

        if cooldownPartition >= nOptions:
            cooldownPartition = nOptions - 1
        
        for i in range(max(0, len(history) - cooldownPartition), len(history)):
            options[history[i] - rangeStart] = -1
        
        options = list(filter(lambda x: False if x < 0 else True, options))
        chosenOption = random.choice(options)

        return chosenOption

    def splitCaptionAndHashtag(self, caption):
        if '#' in caption:
            tagsStart = caption.index('#')
            if tagsStart == 0:
                return ['', caption]
            elif tagsStart > 0:
                return [caption[:tagsStart], caption[tagsStart:len(caption)]]
        
        return [caption, '']


class PostsRequestManager():
    """Creates post objects"""
    PostDataObj = PostItemsData()

    @property
    def postData(self):
        return self.PostDataObj.postData

    @property
    def fields(self):
        return self.PostDataObj.fields

    contentManager = DynamicContentManager(0.8)

    def addPosts(self, newPostIds, newPostTags, contentHistory):
        newPostInstances = []
        numNewPosts = len(newPostIds)

        for i in range(numNewPosts):
            postId = newPostIds[i]
            postIdx = postId - 1
            post = PostItem(postId, newPostTags[i])

            for field in self.fields:
                if field in self.postData[postIdx]:
                    if field == 'profile':
                        setattr(post, field, 'https://cdn.alwayswatching.io/profiles/defined/' + str(postId) + '.jpeg')
                        continue
                    setattr(post, field, self.postData[postIdx][field])
                else:
                    selectedValue = self.contentManager.populateField(
                                        self.postData[postIdx]['contentId'],
                                        post,
                                        field, 
                                        contentHistory
                                    )
                    setattr(post, field, selectedValue)

            post.dynamicContent['id'] = self.postData[postIdx]['contentId']

            #separate hashtags from caption
            caption, hashtags = self.contentManager.splitCaptionAndHashtag(post.caption)
            setattr(post, 'caption', caption)
            setattr(post, 'hashtags', hashtags)

            newPostInstances.append(post)

        return newPostInstances


class DefaultPostsRequest():
    """Generates post ids and fetches posts"""

    contentManager = DynamicContentManager(0.8)

    def getRandom(self, idHistory=None):
        posts = []
        if not idHistory:
            for i in range(1, 11):
                posts.append(random.randint(((i-1) * 100) + 1, i*100))
            return posts

        historyRange = [[] for _ in range(10)]
        for post in idHistory:
            rangePlacement = post//100 if post % 100 != 0 else post//100 - 1
            historyRange[rangePlacement].append(post)

        for i in range(10):
            chosenOption = self.contentManager.cooldownOption(100, self.contentManager.cooldown, historyRange[i], (i * 100) + 1)
            posts.append(chosenOption)
        
        return posts

    def getTags(self, postIds):
        tags = []
        for id in postIds:
            tags.append(postTags[id])
        return tags
    

class ParsedPostDataManager():
    def parseInputData(self, input):
        parsedDataObj = {}
        ids = []
        dynamicContent = {}

        for post in input:
            ids.append(post['id'])
        
            dynamicContentId = post['dynamicContent']['id']
            if dynamicContentId not in dynamicContent:
                dynamicContent[dynamicContentId] = {}

            for field, value in post['dynamicContent'].items():
                if field == 'id':
                    continue
                if field not in dynamicContent[dynamicContentId]:
                    dynamicContent[dynamicContentId][field] = []
                if field == 'commentsData':
                    dynamicContent[dynamicContentId][field].extend(value)
                    continue
                dynamicContent[dynamicContentId][field].append(value)

        parsedDataObj['ids'] = ids
        parsedDataObj['dynamicContent'] = dynamicContent

        return parsedDataObj
