import datetime


class APIKey:
    node_id: int
    api_key: str
    created: datetime.datetime
    quota: int
    next_reset: datetime.datetime
    events_post: int
    suspended_event: object

    def __init__(self, node_id, api_key, created, quota, next_reset, events_posted, suspended_event):
        self.node_id = node_id
        self.api_key = api_key
        self.created = created
        self.quota = quota
        self.next_reset = next_reset
        self.events_posted = events_posted
        self.suspended_event = suspended_event
