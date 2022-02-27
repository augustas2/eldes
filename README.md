[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)

# Eldes Alarm

Custom component for Home Assistant. This component is designed to integrate the Eldes security systems including sensors, outputs, etc.

## Installation

You have two options for installation:

### HACS

- In the [HACS](https://hacs.xyz) panel, go to integrations and click the big orange '+' button. Search for 'Eldes Alarm' and click \'Download this repository with HACS'.

### Manually

- Copy "eldes_alarm" folder to the "/config/custom_components" folder.
- Restart HA server.

## Usage

### Events

#### Event attributes

- `alarms` -> holds events with alarms
- `user_actions` -> holds events with user action like arm and disarm
- `events` -> holds all other events

#### Display events

To display events used another integration:
[lovelace-home-feed-card](https://github.com/gadgetchnnel/lovelace-home-feed-card)

#### Example config for [lovelace-home-feed-card](https://github.com/gadgetchnnel/lovelace-home-feed-card)
```
type: custom:home-feed-card
title: Alarm Feed
card_id: main_feed
show_notification_title: true
show_empty: false
scrollbars_enabled: false
show_icons: false
entities:
  - entity: sensor.events
    list_attribute: user_actions
    multiple_items: true
    timestamp_property: event_time
    max_items: 5
    content_template: '{{type}} set by {{name}}'
  - entity: sensor.events
    list_attribute: alarms
    multiple_items: true
    timestamp_property: event_time
    max_items: 2
    content_template: '!!!!! ALARM !!!!! {{message}}'
```

## Supported devices

- [ESIM364](https://eldesalarms.com/product/esim364)
- [ESIM384](https://eldesalarms.com/product/esim384)
- [Pitbull Alarm PRO](https://eldesalarms.com/product/pitbull-pro/3g)
