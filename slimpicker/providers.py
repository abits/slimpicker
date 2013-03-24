import requests
from xml.etree import ElementTree
from bs4 import BeautifulSoup
from datetime import date
import re


class SubscriptionProvider:
    _options = None

    def __init__(self, options):
        self._options = options

    def get_subscribed_shows(self):
        subscribed_shows = []
        s = requests.session()
        payload = {'username' : self._options.showrss['username'],
                   'password' : self._options.showrss['password']}
        s.post(self._options.showrss['login_url'], data=payload)
        r = s.get(self._options.showrss['shows_url'])
        soup = BeautifulSoup(r.text)
        shows = soup.find_all(href=re.compile('cs=browse&show='))
        for show in shows:
            subscribed_shows.append(show.get_text())
        return subscribed_shows


class ShowInfoProvider:
    _options = None

    def __init__(self, options):
        self._options = options

    def get_latest_episode(self, show_id):
        if not show_id:
            raise ValueError('show_id must not be None.')
        parameters = {'sid': show_id}
        user_agent = {'User-agent': 'Mozilla/5.0'}
        r = requests.get(self._options.tvrage['episode_info_url'], 
            headers=user_agent,
            params=parameters)
        soup = BeautifulSoup(r.text, features='xml')
        latest_episode = soup.latestepisode
        if not latest_episode:
            episode_info = None
        else:
            epnum = soup.latestepisode.number
            if epnum:
                epnum_str = epnum.string
                season, episode = epnum_str.split('x')
            else:
                season = None
                episode = None
            aird = soup.latestepisode.airdate
            if aird:
                aird_str = aird.string
                year, month, day = aird_str.split('-')
            else:
                year = None
                month = None
                day = None
            nam = soup.find('name')
            if nam:
                nam_str = nam.string
            tit = soup.title
            if tit:
                tit_str = tit.string
            episode_info = {
                'show_id': show_id,
                'show_name': nam_str,
                'season': season,
                'episode': episode,
                'airdate': date(int(year), int(month), int(day)),
                'title': tit_str
            }

        return episode_info

    def get_show_id(self, show_name):
        show_id = None
        parameters = {'show': show_name}
        r = requests.get(self._options.tvrage['search_url'], params=parameters)
        soup = BeautifulSoup(r.text, features='xml')
        shows = soup.find_all('show')
        discontinued = ['Pilot Rejected', 'Canceled'
                                          '/Ended']
        # use the first match which is not a discontinued show
        for show in shows:
            status = show.find('status').string
            if status in discontinued:
                continue  # don't use discontinued shows
            else:
                show_id = show.find('showid').string
                break  # we use the first match

        return show_id

    def get_episode_list(self, sid):
        episode_list = []
        parameters = {'sid': sid}
        r = requests.get(self._options.tvrage['episode_list_url'],
                         params=parameters)
        soup = BeautifulSoup(r.text, features='xml')
        seasons = soup.find_all('Season')
        for season in seasons:
            season_number = season.get('no')
            for episode in season.find_all('episode'):
                if episode:
                    episode_number = episode.seasonnum
                    if episode_number:
                        episode_number_str = episode_number.string
                        episode_list.append(
                            '{:0>2}x{:0>2}'.format(season_number,
                                                   episode_number_str))

        return episode_list


class LinkProvider():
    _options = None

    def __init__(self, options):
        self._options = options

    def get_download_links(self,
                           query_string, count=1, hosting=64, extension='avi'):
        download_links = []
        parameters = {
            'extension': extension,
            'sort': 'dd',
            'phrase': query_string,
            'key': self._options.filestube['api_key'],
            'hosting': hosting
        }
        r = requests.get(self._options.filestube['service_url'],
                         params=parameters)
        soup = BeautifulSoup(r.text, features='xml')
        if int(soup.hasResults.string) > 0:
            hits = soup.find_all('hits')
            for hit in hits:
                if count < 1:
                    break
                else:
                    url = hit.find('link').string
                    links = self.scrape(url)
                    if links:
                        count -= 1
                        download_links += links
        return download_links

    def scrape(self, url):
        if not url:
            download_links = None
        else:
            r = requests.get(url)
            soup = BeautifulSoup(r.text)
            try:
                download_links = soup.find(
                    id='copy_paste_links').string.split('\r\n')
                download_links = download_links[:-1]
            except AttributeError:
                download_links = None
            except requests.exceptions.MissingSchema:
                download_links = None

        return download_links

if __name__ == '__main__':
    sp = SubscriptionProvider()
    print(sp.get_subscribed_shows())