from slimpicker.providers import ShowInfoProvider, LinkProvider, SubscriptionProvider
from slimpicker.data import Subscriptions
from sys import exit
from datetime import datetime
from argparse import ArgumentParser
from configparser import ConfigParser
import os, subprocess


class Options:
    parser = ArgumentParser()
    options = ConfigParser()
    args = None
    user_home = os.getenv("HOME")
    config_dir = os.path.join(user_home, '.slimpicker')
    options_file = os.path.join(config_dir, "options.ini")
    subscriptions_file = os.path.join(config_dir, 'subscriptions.ini')
    showrss = {
        'login_url': 'http://showrss.karmorra.info/?cs=login',
        'shows_url': 'http://showrss.karmorra.info/?cs=shows',
        'selection_url': 'http://showrss.karmorra.info/?cs=browse'
    }
    filestube = {
        'service_url': 'http://api.filestube.com'
    }
    tvrage = {
        'search_url': 'http://services.tvrage.com/feeds/search.php',
        'episode_info_url': 'http://services.tvrage.com/feeds/episodeinfo.php',
        'episode_list_url': 'http://services.tvrage.com/feeds/episode_list.php'
    }
    download = {}
    hoster = {}

    def __init__(self):
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir, 0o755)
        self.init_arg_parser()
        self.parse_arguments()
        self.parse_options(self.options_file)
        self.showrss['username'] = self.options['showrss']['username']
        self.showrss['password'] = self.options['showrss']['password']
        self.filestube['api_key'] = self.options['filestube']['api_key']
        self.download['dir'] = os.path.join(self.user_home, self.options['download']['dir'])
        self.download['plowdown_executable'] = self.options['download']['plowdown_executable']

    def init_arg_parser(self):
        self.parser.add_argument('-t', '--template',
                                 action="store_true",
                                 help="create subscriptions template")
        self.parser.add_argument('-u', '--update',
                                 action="store_true",
                                 help="bring subscription up-to-date")
        self.parser.add_argument('-w', '--write',
                                 action="store_true",
                                 help="write download links in file")
        self.parser.add_argument('-d', '--download',
                                 action="store_true",
                                 help="download files")

    def parse_arguments(self):
        self.args = self.parser.parse_args()

    def parse_options(self, filename):
        try:
            self.options.read_file(open(filename))
        except IOError as e:
            raise IOError(e)
        self.parse_hoster_info()

    def parse_hoster_info(self):
        l = LinkProvider(self)
        for key in self.options['hoster']:
            hoster, item = key.split('.')
            self.hoster[hoster] = {}
            self.hoster[hoster]['id'] = l.get_hoster_id(hoster)
        for key in self.options['hoster']:
            hoster, item = key.split('.')
            self.hoster[hoster][item] = self.options['hoster'][key]

class Console:
    options = Options()
    show_info_provider = ShowInfoProvider(options)
    link_provider = LinkProvider(options)
    subscription_provider = SubscriptionProvider(options)
    subscriptions = Subscriptions(show_info_provider)
    query_string_format = '{:s} S{:s}E{:s}'

    def get_query_strings(self, **kwargs):
        query_strings_by_show = {}
        self.subscriptions.update_subscriptions()
        for show_name, episodes in self.subscriptions.get_wanted_episodes().items():
            query_strings = []
            show = self.subscriptions.subscriptions[show_name]
            for episode in episodes:
                if show.use_date is True:
                    query_string = show.name + ' '
                    query_string += show.latest_date.strftime('%Y %m %d')
                else:
                    season_number, episode_number = episode.split('x')
                    query_string = self.query_string_format.format(show.name, season_number, episode_number)
                if 'params' in kwargs:
                    query_string += ' ' + kwargs['params']
                query_strings.append(query_string)
            query_strings_by_show[show_name] = query_strings
        return query_strings_by_show

    def get_download_links(self, query_strings):
        download_links_by_show = {}
        for show, query_strings in sorted(query_strings.items()):
            download_links = {}
            for query_string in sorted(query_strings, key=str.lower):
                download_links[query_string] = self.link_provider.get_download_links(query_string, 1, 64, 'avi')
            download_links_by_show[show] = download_links
        return download_links_by_show

    def write_plow_file(self, download_links, filename):
        header = '# This file was generated by slimpicker.\n'
        header += '# {0}\n\n\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        content = self.format_plow_data(download_links)
        content = header + content
        with open(filename, 'w') as file:
            file.write(content)
        for show in self.subscriptions.get_subscriptions().values():
            show.last = show.latest
        self.subscriptions.save_subscriptions(self.options.subscriptions_file)

    def format_plow_data(self, download_links):
        content = ''
        for show, episodes in download_links.items():
            if not episodes:
                continue
            content += '##  {0}  ##\n'.format(show)
            for episode, links in episodes.items():
                content += '## {0}\n'.format(episode)
                for link in links:
                    content += '{0}\n'.format(link)
                content += '\n'
            content += '\n'
        return content

    def write_subscription_template(self, filename):
        sp = SubscriptionProvider(self.options)
        subscribed_shows = sp.get_subscribed_shows()
        header = '# This file was generated by slimpicker.\n'
        header += '# {0}\n\n\n'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        content = self.format_subscription_template(subscribed_shows)
        content = header + content
        with open(filename, 'w') as file:
            file.write(content)
        self.subscriptions.load_subscriptions(self.options.subscriptions_file)
        self.subscriptions.save_subscriptions(self.options.subscriptions_file)

    def format_subscription_template(self, subscribed_shows):
        content = ''
        for show in subscribed_shows:
            content += '[{0}]\n\n'.format(show)
        return content

    def main(self):
        if self.options.args.template:
            self.write_subscription_template(self.options.subscriptions_file)
        if self.options.args.update:
            self.subscriptions.load_subscriptions(self.options.subscriptions_file)
            self.subscriptions.update_subscriptions()
            self.subscriptions.save_subscriptions(self.options.subscriptions_file)
        if self.options.args.write:
            self.subscriptions.load_subscriptions(self.options.subscriptions_file)
            dl = self.get_download_links(self.get_query_strings())
            timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d_%H%M%S')
            self.options.download['file'] = \
                os.path.join(self.options.download['dir'],
                             'slimlinks_' + timestamp + '.txt')
            self.write_plow_file(dl, self.options.download['file'])
        if self.options.args.download:
            if not self.options.download['file']:
                raise ValueError('No download links given.')
            hoster = next(iter(self.options.hoster.values()))
            plowdown_args = ['-m']
            plowdown_args.append('-v0')
            if hoster:
                plowdown_args.append('-a' + hoster['username'] + ':' + hoster['password'])
            plowdown_args.append('-o' + self.options.download['dir'])
            plowdown_args.append(self.options.download['file'])
            cmd = [self.options.download['plowdown_executable']] + plowdown_args
            subprocess.call(cmd)



def main_func():
    c = Console()
    c.main()
    exit(0)


if __name__ == '__main__':
    c = Console()
    main_func()
    exit(0)