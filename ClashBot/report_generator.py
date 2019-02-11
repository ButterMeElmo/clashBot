import json

from ClashBot import session_scope, DatabaseAccessor


class ReportGenerator:

    def __init__(self):
        self.max_message_size = 2000