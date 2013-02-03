from configparser import ConfigParser
from slimpicker.providers import ShowInfoProvider

class Show:
    id = None
    last = None
    latest = None
    name = None
    use_date = False

class Episode:
    pass

class Resource:
    pass

class Subscriptions:
    subscriptions = {}
    config = ConfigParser()
    episode_format = '{:0>2}x{:0>2}'

    def __init__(self, show_info_provider):
        self.show_info_provider = show_info_provider

    def update_show(self, show_name):
        show = self.get_or_create_subscribed_show(show_name)
        latest_episode = self.show_info_provider.get_latest_episode(show.id)
        show.name = latest_episode['show_name']
        show.latest = self.episode_format.format(latest_episode['season'], latest_episode['episode'])
        self.subscriptions[show_name] = show

    def load_subscriptions(self, filename):
        try:
            self.config.read_file(open(filename))
        except IOError as e:
            raise IOError(e)
        self.subscriptions = {} # reset field
        for section in self.config.sections():
            show = Show()
            for key in self.config[section]:
                show.__setattr__(key, self.config[section][key])
            self.subscriptions[section] = show

    def save_subscriptions(self, filename):
        for show_name, show in self.subscriptions.items():
            for attribute, value in sorted(show.__dict__.items()):
                self.config.set(show_name, attribute, value)
        self.config.write(open(filename, mode='w'), True)

    def get_subscriptions(self):
        return self.subscriptions

    def get_or_create_subscribed_show(self, show_name):
        subscriptions = self.get_subscriptions()
        if not show_name in subscriptions:
            show = Show()
            show.id = self.show_info_provider.get_show_id(show_name)
            self.subscriptions[show_name] = show
        return subscriptions[show_name]

    def get_delta_for_show(self, show_name):
        show = self.subscriptions[show_name]
        if not (hasattr(show, 'last') and hasattr(show, 'latest') and hasattr(show, 'id')):
            raise ValueError('Show \'{0}\' instance is missing attribute(s).'.format(show_name))
        if show.last.split('x') == show.latest.split('x'):
            delta = []
        else:
            episode_list = self.show_info_provider.get_episode_list(show.id)
            last = episode_list.index(show.last) + 1
            latest = episode_list.index(show.latest) + 1
            delta = episode_list[last:latest]
        return delta

    def update_subscriptions(self):
        for show_name in self.get_subscriptions().keys():
            self.update_show(show_name)

    def get_wanted_episodes(self):
        wanted_episodes = {}
        for show_name in self.get_subscriptions().keys():
            wanted_episodes[show_name] = self.get_delta_for_show(show_name)
        return wanted_episodes
