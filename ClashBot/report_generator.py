import json

from ClashBot import session_scope, DatabaseAccessor


class ReportGenerator:

    def __init__(self):
        self.max_message_size = 2000

    def generate_war_performance_report(self):

        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            war_performance_data = database_accessor.get_war_performance(num_wars_to_include=10)

        output_pages = []
        current_page = ""
        for entry in war_performance_data:
            entry_string = json.dumps(entry, indent=4)
            combined_length = len(current_page) + len(entry_string)
            if combined_length <= self.max_message_size:
                current_page += entry_string
            else:
                output_pages.append(current_page)
                current_page = entry_string
        output_pages.append(current_page)

        return output_pages
