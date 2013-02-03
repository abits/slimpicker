from configparser import ConfigParser
from slimpicker.providers import ShowInfoProvider

class Subscriptions:
    subscriptions = {}
    config = ConfigParser()
    episode_format = '{:0>2}x{:0>2}'

    def __init__(self, show_info_provider):
        self.show_info_provider = show_info_provider

    def update_show(self, show):
        if show in self.subscriptions:
            sid = self.subscriptions[show]['id']
        else:
            sid = self.show_info_provider.get_show_id(show)
            self.subscriptions[show]['id'] = sid
        latest_episode = self.show_info_provider.get_latest_episode(sid)
        self.subscriptions[show]['name'] = latest_episode['show_name']
        self.subscriptions[show]['latest'] =\
            self.episode_format.format(latest_episode['season'], latest_episode['episode'])

    def load_subscriptions(self, filename):
        try:
            self.config.read_file(open(filename))
        except IOError as e:
            raise IOError(e)
        self.subscriptions = {} # reset field
        for show in self.config.sections():
            subscription = {}
            for field in ['id', 'name', 'last', 'latest']:
                if self.config.has_option(show, field):
                    subscription[field] = self.config.get(show, field)
            self.subscriptions[show] = subscription

    def save_subscriptions(self, filename):
        for show, subscription in self.subscriptions.items():
            for section, value in sorted(subscription.items()):
                self.config.set(show, section, value)
        self.config.write(open(filename, mode='w'), True)

    def get_subscriptions(self):
        return self.subscriptions

    def get_subscription(self, show):
        subscriptions = self.get_subscriptions()
        if show in subscriptions:
            subscription = { show : subscriptions[show] }
        else:
            subscription = None
        return subscription

    def get_delta_for_show(self, show_name):
        if self.subscriptions[show_name]['last'].split('x') == self.subscriptions[show_name]['latest'].split('x'):
            delta = []
        else:
            episode_list = self.show_info_provider.get_episode_list(self.subscriptions[show_name]['id'])
            last = episode_list.index(self.subscriptions[show_name]['last']) + 1
            latest = episode_list.index(self.subscriptions[show_name]['latest']) + 1
            delta = episode_list[last:latest]
        return delta

    def update_subscriptions(self):
        for show in self.get_subscriptions().keys():
            self.update_show(show)

    def get_wanted_episodes(self):
        wanted_episodes = {}
        for show in self.get_subscriptions().keys():
            wanted_episodes[show] = (self.get_delta_for_show(show))
        return wanted_episodes

if __name__ == '__main__':
    sip = ShowInfoProvider()
    s = Subscriptions(sip)
    s.load_subscriptions()
    s.update_subscriptions()
    print(s.get_subscriptions())
