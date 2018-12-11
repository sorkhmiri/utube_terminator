import requests
import re
from bs4 import BeautifulSoup
from pytube import YouTube
import os
import pickle


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def create_dir_in_path(path, dir_name):
    dir_path = os.path.join(path, dir_name)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    # returning the path of the directory which is created.
    return dir_path


class UTUBE:
    def connection_check(self):
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

    def __init__(self):
        # checking if the required directory exists, if not try to create one.
        create_dir_in_path(os.path.expanduser('~'), 'Downloads')
        self.download_dir = create_dir_in_path(os.path.expanduser('~'), 'Downloads/UTUBE')
        self.utub_dir = create_dir_in_path(os.path.expanduser('~'), '.utub')

        # if an internet connection is available and youtube.com is accessible, then start working.
        if self.connection_check():
            self.utub_url = input("Enter List Url: ")
            # getting request.
            options = input("for downloading a list Enter (L/l) and for Single viedo Enter (S/s):")
            sub = input("do you want subtitle(y/Y) for yes and (n/N) for no:")

            # mapping request.
            if options.lower() == 'l' and sub.lower() == 'n':
                self.list_Terminator(Sub=False)
            elif options.lower() == 'l' and sub.lower() == 'y':
                raise NotImplemented
            elif options.lower() == 's' and sub.lower() == 'n':
                raise NotImplemented
            elif options.lower() == 's' and sub.lower() == 'y':
                raise NotImplemented
            else:
                raise IOError("is it a list or a single video?")

    def get_play_list_id(self):
        # extract playlist id from link
        if re.search(r'list=\S+', self.utub_url):
            urlCore = self.utub_url.split("/")[-1]
            urlList = urlCore.split("&")
            for item in urlList:
                 if 'list=' in item:
                    urlCore = item
            ind = urlCore.index("=") + 1
            urlCore = urlCore[ind:]
            return urlCore
        else:
            print("This url doesn't contain list")
            return None

    def final_video_urls(self, Urls):
        # generates valid video urls
        finals = []
        for url in Urls:
            ind = url.index("&")
            furl = 'http://www.youtube.com/' + url[:ind]
            finals.append(furl)
        finals = list(set(finals))
        return finals, len(finals)

    def set_files_generator(self, playlist_id, videos):
        play_list_dir = create_dir_in_path(self.download_dir, playlist_id)
        with open(os.path.join(play_list_dir, '.utt'), "wb") as file:
            pickle.dump(videos, file)

    def get_video_urls(self, playlist_id):
        # extracts playlist links with given id
        rawhtml = requests.get("https://www.youtube.com/playlist?list={}".format(playlist_id)).text
        patern = re.compile(r'watch\?v=\S+?list=' + playlist_id)
        matches = list(re.findall(patern, rawhtml))
        videos, num = self.final_video_urls(matches)
        self.set_files_generator(playlist_id, videos)
        return videos, num

    def title_for_url(self, video_url):
        res = requests.get(video_url).text
        soup = BeautifulSoup(res, "lxml")
        title = soup.find('span', class_="watch-title").text.replace("\n", '').strip()
        return title

    def video_streams(self, video_url):
        yt = YouTube(video_url).streams.all()
        streams = []
        for i in yt:
            item = str(i)
            itag = re.search(r'itag=\S+', item)
            itag_number = item[itag.span()[0]+6:itag.span()[1]-1]
            typepat = re.search(r'mime_type=\S+', item)
            typ, frmt = item[typepat.span()[0]+11:typepat.span()[1]-1].split("/")
            try:
                respat=re.search(r'res=\S+', item)
                res = item[respat.span()[0]+5:respat.span()[1]-1]
                streams.append((itag_number, typ, frmt, res))
            except:
                abrpat=re.search(r'abr=\S+', item)
                abr = item[abrpat.span()[0]+5:abrpat.span()[1]-1]
                streams.append((itag_number, typ, frmt, abr))
            # what else?
            else:
                pass
        return streams

    def stream_picker(self, streams, typee, formatt, res):
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
        if typee == 'audio':
            # for audio
            pass

    def video_download(self,video_url, itag, playlist_id):
        YouTube(video_url).streams.get_by_itag(itag).download(os.path.join(self.download_dir, playlist_id))

    def single_video_downloader(self, video_url, typee, formatt, res, playlist_id):
        streams = self.video_streams(video_url)
        itag, resol = self.stream_picker(streams, typee, formatt, res)
        self.video_download(video_url, itag, playlist_id)
        return resol

    def list_Terminator(self, Sub):
        pi = self.get_play_list_id()
        if pi is None:
            return
        videos, number = self.get_video_urls(pi)
        print("there are {} videos in this playlist".format(number))
        for i in range(len(videos)):
            print(str(i+1) + "-" + self.title_for_url(videos[i]))
        select = input("Enter Number of videos you want with '-' between:")

        if (not Sub) and (select == '0'):
            # just download all list without sub
            formatt = input("what format do you want:")
            ress = input("what resolotion do you want:")
            for i in range(len(videos)):
                try:
                    resol = self.single_video_downloader(video_url=videos[i], typee='video', formatt=formatt,
                                                         res=ress, playlist_id=pi)
                    print('{}-link:{}-done!'.format(i+1, videos[i]))
                    print('res=' + resol)
                    print("########################")
                except Exception as err:
                    print(bcolors.FAIL + '{}-link:{}-error!'.format(i+1, videos[i]))
                    print(bcolors.FAIL+str(err))
                    print(bcolors.FAIL+"########################")

        elif (not Sub) and (select != '0'):
            # downloading chosen items without sub
            pass

        elif (Sub) and (select == '0'):
            # download all list with sub
            pass

        elif (Sub) and (select != '0'):
            # downloading chosen items with sub
            pass

        else:
            print("the value of sub parameter or the numbers of videos is invalid")


if __name__ == "__main__":
    video = UTUBE()
