
import re
import requests
import time
from bs4 import BeautifulSoup

class ChannelList:

    __filter = [
    '/','/u/login','/u/dashboard','#',
    '/channels/ranking',
    '/games',
    '/clips',
    '/statistics',
    '/statistics/viewers',
    '/statistics/channels',
    '/statistics/active-streamers',
    '/statistics/watch-time',
    '/statistics/stream-time',
    '/statistics/games',
    '/languages',
    '/subscribers',
    '/channels/live',
    '/channels/viewership',
    '/channels/peak-viewers',
    '/channels/hours-watched',
    '/channels/ranking',
    '/channels/followers-growth',
    '/channels/most-followers',
    '/channels/most-views',
    'https://twitchtracker.com/channels/ranking/german',
    'https://twitchtracker.com/channels/ranking/german?page=3',
    '/api',
    ]


    __streamer = []

    def extract(self):
        cookies = dict(BCPermissionLevel='PERSONAL')
        self.__response = []
        number_of_pages = 50 # 50

        for i in range (1, number_of_pages+1,1):
            url = f'https://twitchtracker.com/channels/ranking/german?page={i}'
            print(url)
            self.__response.append(requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, cookies=cookies,stream=True).content)
            time.sleep(5)
        print(f'Number of pages: {len(self.__response)}')





    def transform(self,html_document):
        html_document = (str)(html_document)
        soup = BeautifulSoup(html_document, 'html.parser')
        link_tag = soup.find_all('a')
        last_channel = ""
        for link in link_tag:
            if 'https' in link['href']:
                continue
            if link["href"] in self.__filter:
                continue
            if '#' in link['href']:
                continue
            
            channel = link["href"].replace('/','')

            if channel == last_channel:
                continue
            self.__streamer.append('{}\n'.format(channel))
            last_channel = channel
            
        


    def load(self):
        f = open("ChannelList.txt", "a")
        f.writelines(self.__streamer)
        f.close()


    def main(self):
        self.extract()
        for entry in self.__response:
            self.transform(entry)
        self.load()



if __name__ == '__main__':
    ChannelList().main()