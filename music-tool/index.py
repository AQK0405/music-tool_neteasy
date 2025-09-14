import json
import execjs
import requests

type = {
        # params.length = 236
        'getLink': {
            'url': 'https://music.163.com/weapi/song/enhance/player/url/v1?csrf_token=6405ca0b9a9939b23f9fc79182969ac8',
            'i2x': {"ids":"<keyword>","level":"exhigh","encodeType":"aac","csrf_token":"6405ca0b9a9939b23f9fc79182969ac8"}
        },
        # params.length = 408     y:320
        'search': {
            'url': 'https://music.163.com/weapi/cloudsearch/get/web?csrf_token=6405ca0b9a9939b23f9fc79182969ac8',
            'i2x': {"hlpretag":"<span class=\"s-fc7\">","hlposttag":"</span>","s":"<keyword>","type":"1","offset":"0","total":"true","limit":"100","csrf_token":"6405ca0b9a9939b23f9fc79182969ac8"}
        }
    }

def getbVB1x(i2x):
    with open('temp.js', mode='r') as f:
        a = execjs.compile(f.read())
        res = a.call('main', i2x)
        return  res



def main(keyword, flag):
    cookie = ''
    with open('cookie.txt', mode='r') as f:
        cookie = f.read()
    header = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36 Edg/139.0.0.0',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': cookie
    }
    url = type[flag]['url']
    i2x = str(type[flag]['i2x']).replace('<keyword>', str(keyword))
    bVB1x = getbVB1x(i2x)
    data = {
        'params': bVB1x.get('encText'),
        'encSecKey': bVB1x.get('encSecKey')
    }
    return requests.post(url, headers=header, data=data)

def getAr(ars):
    ar_arr = []
    for ar in ars:
        ar_arr.append(ar.get('name'))
    return '/'.join(ar_arr)

def addLink(data, songList):
    for song in songList:
        for i in data:
            if i.get('id') == song.get('id'):
                song['url'] = i.get('url')

def search(keyword):
    songList = []
    songID = []
    searchRes = json.loads(main(keyword=keyword, flag='search').text)
    for song in searchRes.get('result').get('songs'):
        id = song.get('id')
        name = song.get('name')
        ar = getAr(song.get('ar'))
        songID.append(int(id))
        temp = {'id': id, 'name': name, 'ar': ar}
        songList.append(temp)
    addLink(json.loads(main(keyword=songID, flag='getLink').text).get('data'), songList)
    return songList


# if __name__ == '__main__':
#     print(search('今天你就要嫁给我'))