import json

from ClashBot import session_scope, DatabaseAccessor


class ReportGenerator:

    def __init__(self):
        self.max_message_size = 2000

    def generate_war_performance_report(self):

        try:
            with session_scope() as session:
                database_accessor = DatabaseAccessor(session)
                war_performance_data = database_accessor.get_war_performance(num_wars_to_include=10)

            output_pages = []
            current_page = ""
            for entry in war_performance_data:
                entry_string = json.dumps(entry, indent=4)
                combined_length = len(current_page) + len(entry_string)
                if combined_length <= self.max_message_size:
                    current_page += entry_string + "\n"
                else:
                    output_pages.append(current_page)
                    current_page = entry_string
            output_pages.append(current_page)
        except Exception as e:
            print(e)
            output_pages = [
                "An error occurred when producing your report."
            ]

        return output_pages

    def generate_war_strengths_report(self):

        try:
            with session_scope() as session:
                database_accessor = DatabaseAccessor(session)
                member_strength_data = database_accessor.get_member_strengths()

            output_pages = []
            current_page = ""
            for entry in member_strength_data:
                entry_string = json.dumps(entry, indent=4)
                combined_length = len(current_page) + len(entry_string)
                if combined_length <= self.max_message_size:
                    current_page += entry_string + "\n"
                else:
                    output_pages.append(current_page)
                    current_page = entry_string
            output_pages.append(current_page)
        except Exception as e:
            print(e)
            output_pages = [
                "An error occurred when producing your report."
            ]

        return output_pages

    def generate_war_strengths_report_short(self, include_rank=True):
        try:
            with session_scope() as session:
                database_accessor = DatabaseAccessor(session)
                member_strength_data = database_accessor.get_member_strengths()

            output_pages = []
            current_page = ""
            for entry in member_strength_data:
                if include_rank:
                    entry_string = "{}) {}".format(entry["rank"], entry["member_name"])
                else:
                    entry_string = "{}".format(entry["member_name"])
                combined_length = len(current_page) + len(entry_string)
                if combined_length <= self.max_message_size:
                    current_page += entry_string + "\n"
                else:
                    output_pages.append(current_page)
                    current_page = entry_string
            output_pages.append(current_page)
        except Exception as e:
            print(e)
            output_pages = [
                "An error occurred when producing your report."
            ]

        return output_pages
