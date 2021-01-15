import os
import yaml
import random
import sys
import logging

from typing import Tuple, List


def _get_abs_path(path: str) -> str:
    __location__ = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(__location__, path)


def load_config(config_path: str = None) -> dict:
    """
    Load config file. If not found, then load the template
    """
    try:
        if config_path is None:
            with open(os.path.join(sys.path[0], 'config.yml'), 'r') as f:
                return yaml.safe_load(f)
        else:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
    except FileNotFoundError:
        logging.info('config.yml not found, loading default template.')
        with open(_get_abs_path('config.template.yml'), 'r') as f:
            return yaml.safe_load(f)
    else:
        raise Exception('Error in configuration File')


class WeightedRandom:

    def __init__(self, config: dict = None):
        if config is None:
            self.config = load_config()
        else:
            self.config = config

    def select(self, property_name: str) -> str:
        """
        Select a weighted random value from a property defined in config file
        :param property_name: a property name defined in config file
        :return:
        """
        keys = [key for key in self.config.get(property_name).keys()]
        weights = self.config.get(property_name).values()
        return random.choices(keys, weights=weights)[0]

    def get_pages(self, page: str, curr_cycle: int) -> Tuple[List[str], List[float]]:
        """
        Returns list of pages and weights from config
        """
        dict_ = self.config['pages'].get(page)
        max_cycle = dict_['max_decay_cycles']
        if curr_cycle  <= max_cycle:
            pages_info = { k: v * curr_cycle/max_cycle for k, v in dict_.get('pages').items() if k != page}
            pages_info[page] = 1 - sum([x for x in pages_info.values()])
        else:
            pages_info = dict_.get('pages')

        pages = [page for page in pages_info.keys()]
        weights = list(pages_info.values())
        return pages, weights

    def get_events(self, page: str, prereq: str = None) -> Tuple[List[str], List[float], dict, dict, bool]:
        """
        Returns list of pages and weights from config
        """
        events_dict = self.config['events'].get(page)
        if events_dict is not None:
            events = [event for event in events_dict.keys() if events_dict.get(event).get('prereq') == prereq]
            if len(events) == 0:
                events_prereq = False
                events = [event for event in events_dict.keys() if events_dict.get(event).get('prereq') is None]
            else: events_prereq = True
            weights = [events_dict.get(event).get('prob') for event in events]
            modal = {event: events_dict.get(event).get('modal') for event in events}
            modal = {k:(False if v is None else v) for k,v in modal.items()}
            properties = {event: events_dict.get(event).get('properties') for event in events}
            return events, weights, modal, properties, events_prereq
        else: return [], [], [], {}, False

