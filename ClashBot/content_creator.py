import json
import matplotlib.pyplot as plt
import os
from pathlib import Path
import urllib

from ClashBot import session_scope, DatabaseAccessor


class ContentCreator:

    def __init__(self):
        with open("configs/app.json") as infile:
            app_config = json.load(infile)
            self.s3_bucket_name = app_config["s3_bucket_name"]
            self.image_extension = "png"

    def create_donation_graphs(self):

        with session_scope() as session:

            database_accessor = DatabaseAccessor(session)

            donation_data = database_accessor.get_donations_for_x_days(30)

            member_names = []
            for member_name, data in sorted(donation_data["results"].items(), key=lambda x: x[0].upper()):
                print(member_name)

                x_data = [x[0] for x in data]
                y_data = [x[1] for x in data]

                plt.plot(x_data, y_data)
                plt.xlabel("Timestamp (epoch) - tracks last 30 days")
                plt.ylabel("Donated in hour period")
                plt.title(member_name)
                plt.ylim(top=donation_data["max_y"], bottom=0)
                plt.xlim(right=donation_data["max_x"], left=donation_data["min_x"])
                output_dir = "output"
                if not os.path.exists(output_dir):
                    print("Output directory does not exist")
                image_location = "{}/{}.{}".format(output_dir, member_name, self.image_extension)
                plt.savefig(image_location)
                plt.close()

                member_names.append(member_name)

        return member_names

    def create_donation_webpage(self, member_names, create_for_s3):
        html_code = """<body>"""
        for member_name in member_names:
            print(member_name)

            output_dir = "output"
            if create_for_s3:
                s3_member_name = member_name.replace(" ", "+")
                image_source = "https://s3.amazonaws.com/{}/charts/{}.{}".format(self.s3_bucket_name, s3_member_name, self.image_extension)
            else:
                absolute_path = "{}/{}".format(Path().absolute(), output_dir)
                url_safe_name = urllib.parse.quote(member_name)
                image_source = "{}/{}.{}".format(absolute_path, url_safe_name, self.image_extension)
            print(image_source)
            html_code += "<img src={}></img>".format(image_source)
        html_code += """</body>"""
        with open("{}/donated_charts.html".format(output_dir), "w") as outfile:
            outfile.write(html_code)


def init():
    if __name__ == "__main__":
        x = ContentCreator()
        member_names = x.create_donation_graphs()
        x.create_donation_webpage(member_names, True)


init()