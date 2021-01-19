from faker import Faker
from fake_web_events.utils import WeightedRandom
from fake_web_events.user import User
import json
import random
from datetime import timedelta, datetime
from dateutil import parser
import math

from typing import Tuple


class Event(Faker, WeightedRandom):
    """
    Creates events and keeps tracks of sessions
    """

    def __init__(self, current_timestamp: datetime, user: User, batch_size: int,
                 always_forward: bool, config: dict = None
                 ):
        super().__init__(['en_US'])
        WeightedRandom.__init__(self, config=config)
        self.previous_page = None
        self.current_page = self.select('landing_pages')
        self.user = user
        self.batch_size = batch_size
        self.current_timestamp = self.randomize_timestamp(current_timestamp, always_forward)
        self.is_new_page = True
        self.always_forward = always_forward
        # custom event attributes
        self.custom_event = None
        self.event_properties = {}
        self.curr_cycle = 1
        # modal attributes
        self.modal = False
        self.modal_event = None
        self.yield_modal = False

    def randomize_timestamp(self, timestamp: datetime, always_forward: bool) -> datetime:
        """
        Randomize timestamps so not all events come with the same timestamp value
        """
        range_milliseconds = int(self.batch_size * 0.3 * 1000)
        min_range = 0 if always_forward else - range_milliseconds
        random_interval = random.randrange(min_range, range_milliseconds)
        return timestamp + timedelta(milliseconds=random_interval)

    def get_next_page(self) -> str:
        """
        Calculate which one should be the next page
        """
        pages, weights = self.get_pages(self.current_page, self.curr_cycle)
        self.current_page = random.choices(pages, weights=weights)[0]

        return self.current_page

    def update_modal(self, modal: dict, check_current: bool = True):
        """
        Update modal attributes depending on:
         - modal needs to be updated if currently there is no modal or there is no current check (meaning a forced update)
         - yield modal when modal changed to true and there was no previous modal_event assigned
         - modal event updates to current event if modal changed to true and there was no previous modal_event assigned
        """
        if check_current:
            if self.modal:
                pass
            else:
                # if there was not modal select current event modal
                self.modal = modal[self.custom_event]
        else:
            # force modal state updated with current event modal
            self.modal = modal[self.custom_event]

        if self.modal and self.modal_event is None:
            # modal state and no modal_event means a recent change in modal state
            self.yield_modal = True
            self.modal_event = self.custom_event
        else:
            # reset
            self.yield_modal = False
            self.modal_event = self.modal_event

    def get_custom_event(self) -> Tuple[str, dict]:
        """
        Calculate which one should be the next custom event
        """

        events, weights, modal, properties, events_prereq = self.get_events(self.current_page, self.custom_event)

        if len(events) > 0:  # events in the page
            self.custom_event = random.choices(events, weights=weights)[0]
            self.event_properties = properties[self.custom_event]
            if events_prereq:
                # there were events with previous prereq, selection from returned events is ok
                self.update_modal(modal)
            else:
                # there were no events with previous prereq (meaning it reached an end of the prereq tree)
                if self.modal:
                    # if there is modal state, either return to modal events or return to page events
                    modal_rand = random.random()
                    if modal_rand < 0.4:  # go to modal
                        self.custom_event = self.modal_event
                        self.yield_modal = False
                    else:  # go to page events
                        self.modal_event = None
                        # Check if the selected custom event is another modal
                        self.update_modal(modal, check_current=False)

                else:
                    # if there is no modal state, selection from returned events is ok (meaning events without prereq
                    # in  page)
                    self.update_modal(modal)

        else:  # not events for page
            self.custom_event = None
            self.event_properties = {}

        return self.custom_event, self.event_properties

    def create_properties(self, properties: dict) -> dict:
        """
        create properties dictionary from specification dictionary
        """
        props = dict()
        if properties is None or len(properties) == 0:
            # empty dict if there is no specification
            return props
        else:
            # loop over specifications and get random values depending on specifications
            try:
                for prop, value in properties.items():
                    if value['type'] in ('string', 'str'):
                        props[prop] = self.random_choices(value['values'], 1)[0]
                    elif value['type'] in ('boolean', 'bool'):
                        props[prop] = self.boolean()
                    elif value['type'] == 'int':
                        min_, max_ = value['values'][0], value['values'][-1]
                        props[prop] = self.random_int(min=min_, max=max_)
                    elif value['type'] == 'float':
                        # as floats min and max needs to be specified as integers
                        # convert to integer and iterate random float until it between specified boundaries
                        min_, max_ = value['values'][0], value['values'][-1]
                        min_int, max_int = math.floor(min_), math.ceil(max_)
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
                        if 'values' in value.keys() and value['values'] is not None:
                            props[prop] = self.local_latlng(country_code=value['values'])
                        else:
                            props[prop] = self.local_latlng(country_code='US')
                    else:
                        # if none of the pre
                        pass

                return props
            except:
                raise Exception('Property paramaters not correctly configured')

    def generate_event(self) -> dict:
        """
        Return the event information as a dictionary
        """
        if self.custom_event is None:  # pageview
            return {
                'event_id': self.uuid4(),
                'event_timestamp': self.current_timestamp, #.strftime('%Y-%m-%d %H:%M:%S.%f'),
                'event_type': 'pageview',
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
                'event_timestamp': self.current_timestamp, #.strftime('%Y-%m-%d %H:%M:%S.%f'),
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

    def update(self, timestamp: datetime, always_forward: bool) -> [bool, str]:
        """
        Update state / Change pages
        """
        if self.is_active():
            self.current_timestamp = self.randomize_timestamp(timestamp, always_forward)
            self.previous_page = self.current_page
            self.get_next_page()
            self.is_new_page = self.current_page != self.previous_page
            if self.is_new_page:
                self.custom_event = None
                self.event_properties = {}
                self.curr_cycle = 1
            else:
                self.get_custom_event()
                self.curr_cycle += 1

            return self.is_new_page, self.custom_event

    def __str__(self) -> str:
        """
        Human readable event
        """
        return json.dumps(self.asdict(), indent=4, ensure_ascii=False)
