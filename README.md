# Fake Web Events

Generator of semi-random fake web events. 

When prototyping event streaming and analytics tools such as Kinesis, Kafka, Spark Streaming, you usually want to 
have a fake stream of events to test your application. However you will not want to test it with complete 
random events, they must have some logic and constraints to become similar to the real world.

This package generates semi-random web events for your prototypes, so that when you build some charts 
out of the event stream, they are not completely random. This is a typical fake event generated with this package:

```json
{
 "event_id": "94e5d9ba-c455-4cac-9b0b-7448cfe80f59",
 "event_timestamp": "2020-01-01 23:05:21.808884",
 "event_type": "pageview",
 "page_url": "http://www.dummywebsite.com/home",
 "page_url_path": "/home",
 "properties": {"referer_url": "www.bing.com",
  "referer_url_scheme": "http",
  "referer_url_port": "80",
  "referer_medium": "search",
  "utm_medium": "cpc",
  "utm_source": "bing",
  "utm_content": "ad_4",
  "utm_campaign": "campaign_1",
  "click_id": "ca4a4122-a7e4-4bee-bc81-981c93285950"},
 "geo_latitude": "44.98901",
 "geo_longitude": "38.94324",
 "geo_country": "RU",
 "geo_timezone": "Europe/Moscow",
 "geo_region_name": "Yablonovskiy",
 "ip_address": "143.94.155.161",
 "browser_name": "Chrome",
 "browser_user_agent": "Mozilla/5.0 (X11; Linux i686) AppleWebKit/531.1 (KHTML, like Gecko) Chrome/43.0.804.0 Safari/531.1",
 "browser_language": "en_DK",
 "os": "iPad; CPU iPad OS 10_3_4 like Mac OS X",
 "os_name": "iOS",
 "os_timezone": "Europe/Moscow",
 "device_type": "Mobile",
 "device_is_mobile": true,
 "user_custom_id": "adrianlewis@gmail.com",
 "user_domain_id": "1805eef8-f941-4d60-874e-93aff71dbe4b"
}
```

## Installation
To install simply do `pip install fake_web_events`

## Running
It is easy to run a simulation as well:
```python
from fake_web_events import Simulation


simulation = Simulation(user_pool_size = 100, sessions_per_day = 100000)
events = simulation.run(duration_seconds = 60)

for event in events:
    print(event)
```

## How it works
We create fake users, then generate session events based on a set of probabilities.

### Probabilities
There is a configuration file where we define a set of probabilities for each event. Let's say browser preference:
```yaml
browsers:
  Chrome: 0.5
  Firefox: 0.25
  InternetExplorer: 0.05
  Safari: 0.1
  Opera: 0.1
```

Also, when a user is in a determined page, there are some defined probabilities of what 
are the next page he's going to visit:
```yaml
home:
  home: 0.45
  product_a: 0.17
  product_b: 0.12
  session_end: 0.26
```
This means that at the next iteration there are 45% chance user stays at home page, 
17% chance user goes to product_a page and so on.

### Custom Events
Whenever a user lands in the same page, there is no new `pageview` event created; but additionally you can configure custom events to happen, such as clicks, opens, select, add_information etc. Custom events are also set in the config file under the `events` section; there is also possible to set a particular page with no events.
Events are set by page; each event has a name, a prereq (if said event happens after another particular event), a probability and a configurable properties field which can contain multiple properties of diferent types.

```yaml
home:
  dropdown_select:
    prereq: 'dropdown_click'
    prob: 0.3
    properties:
      drp_option:
        type: 'string'
        values: ['text1', 'text2', 'text3', 'text4']
      drp_order:
        type: 'int'
        values: [1, 4]
```

### Website Map
We designed a really simple website map to allow user browsing.
![website_map](assets/website_map.svg)

Green pages are those where a user can land at the beginning of a session. 
Yellow pages are only accessible to user who are already browsing.

You can fin how the probabilities for each page are defined in the 
[config.template.yml](fake_web_events/config.template.yml) file

### Fake user information
To generate fake user information, such as IP and email addresses we are using the module [Faker](https://github.com/joke2k/faker).

### User Pool
We create a user pool from where users are randomly chosen. This enables users to have different sessions over time.

### Simulation
When you run a simulation, it will pick an user and iterate until that user reaches session_end. 
Simulation will run in steps defined by `batch_size`. The default `batch_size` is 10 seconds, meaning that 
each iteration will add 10 seconds to the timer (with some randomness).

For each iteration an event is generated for each user when the current page is different from the previous page.

### Simulate events
When calling `simulation.run()` you have to define a duration in seconds. Please note that this duration is in "real time", 
and that time inside the simulation will usually run faster than real time.

This will return a generator, so you need to iterate over it and decide what to do to each event inside the loop.

#### Simulate events over a extended period of time
Given that the simulation is in "real time", sometimes you want to simulate a longer period of time than a couple of seconds, for example a year or so.
To do so please specify the period of time in days when setting the simulation

```python
simulation = Simulation(user_pool_size = 100, sessions_per_day = 100000, sim_days = 360)
```
This will simulate different sessions for the user across the period of time, but still following the duration in seconds of the run (meaning the run will simulate events during 10 seconds if specified but across the period of time)

#### Simulate growth

If you want to customize the simulation over a extended periof of time, you can specify what kind of growth do you want over said period of time. Please notice right now the growth starts at 0 in `init_time`.
Available options are 'linear' or 'exponential'

```python
simulation = Simulation(user_pool_size = 100, sessions_per_day = 100000, sim_days = 360, growth='linear')
```

## Advanced
If you want to customize the probabilities, you can create a file called `config.yml` in the same 
directory where you are running the script. This file will take precedence over [config.template.yml](fake_web_events/config.template.yml).

Additionally you can specify the configuraion path when setting the simulation 

```python
simulation = Simulation(user_pool_size = 100, sessions_per_day = 100000, config_path = path)
```
### Modal
Modal windows, overlays, or pop-up messages are a type of in-app messaging. They are large UI elements that sit on top of an application's main window; usually they share the same screen name of the application screen. 
Large modals usually have more than 1 associated event. To account for that you can specify if an event is associated with opening a modal (all the events inside said modal will have as prerequisite this event). Without this option only one event will be generated every time a modal opening is simulated. With this option there is a 50% chance (fixed) that a second, third, etc. event will be triggered. To specify a modal see the following example configuration:

```yaml
add_to_cart:
  prereq:
  prob: 0.3
  properties:
    qty:
      type: 'int'
      values: [ 1, 10]
    price:
      type: 'float'
      values: [ 10, 30 ]
  modal: True

remove_from_cart:
  prereq: 'add_to_cart'
  prob: 0.3
  properties:
    time_passed_sec:
      type: 'float'
      values: [0, 10]

go_to_cart:
  prereq: 'add_to_cart'
  prob: 0.7
  properties:
```

# Examples
In the folder [examples](examples) you are going to find some use cases and examples on how to use this package.

## Page visit distribution
After running the simulation for a few seconds, we get the following distribution of events per page:
![pageview_funnel](assets/pageview_funnel.png)


## Page views per hour
We also have different visit rates per hour of day. This is the distribution after running the simulation:
![events_per_hour](assets/pageviews.gif)

# Wanna help?
Fork, improve and PR.
