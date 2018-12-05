import requests
import re
from bs4 import BeautifulSoup
from pytube import YouTube
import os
import pickle


DOWNLOAD_DIR = None
UTUBE_DIR = None


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def connection_check():
    # internet connection check!
    try:
        google = requests.get("https://www.google.com/", timeout=5, **{})
        if google.status_code != 200:
            return False
    except:
        print("--> Check Your Connection")
        return False
    # checking proxy
    try:
        utube = requests.get("https://www.youtube.com/", timeout=5)
        if utube.status_code != 200:
            return False
    except:
        print("--> Check Your Proxy")
        return False
    return True


def initialize():
    global DOWNLOAD_DIR
    DOWNLOAD_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'Downloads')
    if not os.path.exists(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)
    global UTUBE_DIR
    UTUBE_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.tube')
    if not os.path.exists(UTUBE_DIR):
        os.mkdir(UTUBE_DIR)


def get_play_list_id(Url):
    # extract playlist id from link
    if re.search(r'list=\S+', Url):
        urlCore = Url.split("/")[-1]
        urlList = urlCore.split("&")
        for item in urlList:
             if 'list=' in item:
                urlCore = item
        ind = urlCore.index("=") + 1
        urlCore = urlCore[ind:]
        return urlCore
    else:
        print("This Url doesn't contain list")
        return None


def final_video_urls(Urls):
    # generates valid video urls
    finals = []
    for url in Urls:
        ind = url.index("&")
        furl = 'http://www.youtube.com/' + url[:ind]
        finals.append(furl)
    finals = list(set(finals))
    return finals, len(finals)


def set_files_generator(playlist_id, videos):
    global UTUBE_DIR
    play_list_dir = os.path.join(UTUBE_DIR, playlist_id)
    if not os.path.exists(play_list_dir):
        os.mkdir(play_list_dir)
    with open(os.path.join(play_list_dir, '.utt'), "wb") as file:
        pickle.dump(videos, file)


def get_video_urls (playlist_id):
    # extracts playlist links with given id
    rawhtml = requests.get("https://www.youtube.com/playlist?list={}".format(playlist_id)).text
    patern = re.compile(r'watch\?v=\S+?list=' + playlist_id)
    matches = list(re.findall(patern, rawhtml))
    videos, num = final_video_urls(matches)
    set_files_generator(playlist_id, videos)
    return videos, num


def title_for_url(Url):
    res = requests.get(Url).text
    soup = BeautifulSoup(res, "lxml")
    title = soup.find('span', class_="watch-title").text\
    .replace("\n",'').strip()
    return title


def video_streams(Url):
    yt = YouTube(Url).streams.all()
    streams = []
    for i in yt:
        item = str(i)
        itag = re.search(r'itag=\S+',item)
        itag_number = item[itag.span()[0]+6:itag.span()[1]-1]
        typepat = re.search(r'mime_type=\S+',item)
        typ, frmt = item[typepat.span()[0]+11:typepat.span()[1]-1].split("/")
        try:
            respat=re.search(r'res=\S+', item)
            res = item[respat.span()[0]+5:respat.span()[1]-1]
            streams.append((itag_number, typ, frmt, res))
        except:
            abrpat=re.search(r'abr=\S+',item)
            abr = item[abrpat.span()[0]+5:abrpat.span()[1]-1]
            streams.append((itag_number, typ, frmt, abr))
        # what else?
        else:
            pass
    return streams


def stream_picker(streams, typee, formatt, res):
    gstreams = []

    for item in streams:
        if item[1] == typee and item[2] == formatt and item[3] == res:
            return item[0], res
        elif item[1] == typee and item[2] == formatt:
            gstreams.append(item)
    
    print(gstreams)

    res_group = ['1080p', '720p', '480p', '360p', '240p', '144p']
    if typee == 'video':
        # for videos
        if not (res in res_group):
            print('wrong res!')
            return None
        for item in gstreams:
            for r in res_group:
                if r == res:
                    continue
                elif item[3] == r:
                    return item[0], r
        
        print('match not found')
        return None, 0
        # what are these for ?
        # if typee == 'audio':
        #     #for audio
        #    pass


def video_download(Url, itag, playlist_id):
    YouTube(Url).streams.get_by_itag(itag).download('/home/mahdi/Downloads/utube/'+playlist_id)


def single_video_downloader(Url, typee, formatt, res, playlist_id):
    streams = video_streams(Url)
    itag, resol = stream_picker(streams, typee, formatt, res)
    video_download(Url, itag, playlist_id)
    return resol


def list_Terminator(Url, Sub):
    pi = get_play_list_id(Url)
    videos, number = get_video_urls(pi)
    print("there are {} videos in this playlist".format(number))
    for i in range(len(videos)):
        print(str(i+1) + "-"+ title_for_url(videos[i]))
    select = input("Enter Number of videos you want with '-' between:")

    global UTUBE_DIR
    if not os.path.exists(UTUBE_DIR):
        os.mkdir(UTUBE_DIR)
    if not os.path.exists(os.path.join(UTUBE_DIR, 'pi')):
        os.mkdir(os.path.join(UTUBE_DIR, 'pi'))

    if (not Sub) and (select == '0'):
        # just download all list without sub
        formatt = input("what format do you want:")
        ress = input("what resolotion do you want:")
        for i in range(len(videos)):
            try:
                resol = single_video_downloader(videos[i], 'video', formatt, ress, pi)
                print('{}-link:{}-done!'.format(i+1, videos[i]))
                print('res=' + resol)
                print("########################")
            except Exception as err:
                print(bcolors.FAIL + '{}-link:{}-error!'.format(i+1, videos[i]))
                print(bcolors.FAIL+str(err))
                print(bcolors.FAIL+"########################")

    elif (not Sub) and (select != '0'):
        # downloading choosen items without sub
        pass

    elif (Sub) and (select == '0'):
        # download all list with sub
        pass

    elif (Sub) and (select != '0'):
        # downloading choosen items with sub
        pass
        
    else:
        print("the value of sub parameter or the numbers of videos is invalid")


def Terminator():
    initialize()
    if connection_check():
        url = input("Enter Youtube Url:")
        options = input("for downloading a list Enter (L/l) and for Single viedo Enter (S/s):")
        sub = input("do you want subtitle(y/Y) for yes and (n/N) for no:")
        
        if options.lower() == 'l' and sub.lower() == 'n':
            list_Terminator(url, False)
        elif options.lower() == 'l' and sub.lower() == 'y':
            pass
        elif options.lower() == 's' and sub.lower() == 'n':
            pass
        elif options.lower() == 's' and sub.lower() == 'y':
            pass
        else:
            print("is it a list or a single video?")


if __name__ == "__main__":
    Terminator()