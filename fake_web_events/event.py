from faker import Faker
from fake_web_events.utils import WeightedRandom
from fake_web_events.user import User
import json
import random
from datetime import timedelta, datetime
from dateutil import parser
import math


class Event(Faker, WeightedRandom):
    """
    Creates events and keeps tracks of sessions
    """

    def __init__(self, current_timestamp: datetime, user: User, batch_size: int):
        super().__init__(['en_US'])
        self.previous_page = None
        self.current_page = self.select('landing_pages')
        self.custom_event = 'pageview'
        self.event_properties = {}
        self.user = user
        self.batch_size = batch_size
        self.current_timestamp = self.randomize_timestamp(current_timestamp)
        self.is_new_page = True

    def randomize_timestamp(self, timestamp: datetime) -> datetime:
        """
        Randomize timestamps so not all events come with the same timestamp value
        """
        range_milliseconds = int(self.batch_size * 0.3 * 1000)
        random_interval = random.randrange(-range_milliseconds, range_milliseconds)
        return timestamp + timedelta(milliseconds=random_interval)

    def get_next_page(self) -> str:
        """
        Calculate which one should be the next page
        """
        pages, weights = self.get_pages(self.current_page)
        self.current_page = random.choices(pages, weights=weights)[0]

        return self.current_page

    def get_custom_event(self) -> str:
        """
        Calculate which one should be the next page
        """
        events, weights, properties = self.get_events(self.current_page)
        if len(events>0):
            self.custom_event = random.choices(events, weights=weights)[0]
            self.event_properties = properties[self.custom_event]
        else:
            self.custom_event = 'pageview'
            self.event_properties = {}
        return self.custom_event, self.event_properties

    def create_properties(self, properties: dict) -> dict:
        props = dict()
        if properties is None or len(properties) == 0:
            return props
        else:
            try:
                for prop, value in properties.items():
                    if value['type'] == 'string':
                        props[prop] = self.random_choices(value['values'], 1)[0]
                    elif value['type'] == 'boolean':
                        props[prop] == self.boolean()
                    elif value['type'] == 'int':
                        min_ = value['values'][0]
                        max_ = value['values'][-1]
                        props[prop] = self.random_int(min=min_, max=max_)
                    elif value['type'] == 'float':
                        min_ = value['values'][0]
                        max_ = value['values'][-1]
                        min_int = math.floor(min_)
                        max_int = math.ceil(max_)
                        float_ = min_int - 1
                        while float_ < min_ or float_ > max_:
                            float_ = self.pyfloat(min_value=min_int, max_value=max_int)
                        props[prop] = float_
                    elif value['type'] in ['date', 'datetime']:
                        max_ = parser.parse(value['values'][-1])
                        min_ = parser.parse(value['values'][0]) if len(value['values']) > 1 else None
                        datetime_ = self.date_time_between_dates(min_, max_)
                        if value['type'] == 'date':
                            datetime_ = datetime_.date()
                        props[prop] = datetime_
                    elif value['type'] == 'email':
                        props[prop] = self.ascii_free_email()
                    elif value['type'] in ['phone', 'phone_number']:
                        props[prop] = self.phone_number()
                    elif value['type'] == 'address':
                        props[prop] = self.address()
                    elif value['type'] == 'geolocation':
                        if value['values'] is not None:
                            props[prop] = self.local_latlng(country_code=value['values'])
                        else:
                            props[prop] = self.local_latlng(country_code='US')
                    else:
                        pass

                return props
            except:
                raise Exception('Property paramaters not correctly configured')

    def generate_event(self) -> dict:
        """
        Return the event information as a dictionary
        """
        if self.custom_event == 'pageview':
            return {
                'event_id': self.uuid4(),
                'event_timestamp': self.current_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'event_type': self.custom_event,
                'page_url': f'http://www.dummywebsite.com/{self.current_page}',
                'page_url_path': f'/{self.current_page}',
                'properties': {
                    **self.user.referer(),
                    **self.user.utm(),
                }
            }
        else:
            return {
                'event_id': self.uuid4(),
                'event_timestamp': self.current_timestamp.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'event_type': self.custom_event,
                'page_url': f'http://www.dummywebsite.com/{self.current_page}',
                'page_url_path': f'/{self.current_page}',
                'properties': self.create_properties(self.event_properties)
            }

    def asdict(self) -> dict:
        """
        Return the event + user as a dictionary
        """
        return {
            **self.generate_event(),
            **self.user.geo(),
            **self.user.ip(),
            **self.user.browser(),
            **self.user.operating_system(),
            **self.user.device(),
            **self.user.user()
        }

    def is_active(self) -> bool:
        """
        Check if session is currently active
        """
        return self.current_page != 'session_end'

    def update(self, timestamp: datetime) -> bool:
        """
        Update state / Change pages
        """
        if self.is_active():
            self.current_timestamp = self.randomize_timestamp(timestamp)
            self.previous_page = self.current_page
            self.get_next_page()
            self.is_new_page = self.current_page != self.previous_page
            if self.is_new_page:
                self.custom_event = 'pageview'
                self.event_properties = {}
            else:
                self.get_custom_event()

            return self.is_new_page, self.custom_event

    def __str__(self) -> str:
        """
        Human readable event
        """
        return json.dumps(self.asdict(), indent=4, ensure_ascii=False)
