import boto3
import json
import matplotlib.pyplot as plt
import os
from pathlib import Path
import urllib

from ClashBot import session_scope, DatabaseAccessor


class ContentCreator:

    def __init__(self):
        with open("configs/aws.json") as infile:
            aws_config = json.load(infile)
            self.s3_bucket_name = aws_config["s3_bucket_name"]
            self.aws_access_key_id = aws_config["aws_access_key_id"]
            self.aws_secret_access_key = aws_config["aws_secret_access_key"]
            self.image_extension = "png"
            self.s3_key_charts = "charts/donations"
            self.donated_charts_webpage_name = "donated_charts.html"
            self.aws_session = boto3.Session(
                    aws_access_key_id=self.aws_access_key_id,
                    aws_secret_access_key=self.aws_secret_access_key
                )
            self.output_dir = "output"

    def generate_donation_webpage(self, create_for_s3=True):
        image_file_names = self.create_donation_graphs()
        webpage_file_name = self.create_donation_webpage(image_file_names, create_for_s3=create_for_s3)
        self.upload_images_to_s3(image_file_names)
        self.upload_webpages_to_s3([webpage_file_name])
        return "https://s3.amazonaws.com/{}/{}/{}".format(self.s3_bucket_name, self.s3_key_charts, self.donated_charts_webpage_name)

    def create_donation_graphs(self):

        with session_scope() as session:
            database_accessor = DatabaseAccessor(session)
            donation_data = database_accessor.get_donations_for_x_days(30)

        file_names = []
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
            if not os.path.exists(self.output_dir):
                print("Output directory does not exist")
            file_name = "{}.{}".format(member_name, self.image_extension)
            image_location = "{}/{}".format(self.output_dir, file_name)
            plt.savefig(image_location)
            plt.close()

            file_names.append(file_name)

        return file_names

    def create_donation_webpage(self, file_names, create_for_s3=False):
        html_code = """<body>"""
        for file_name in file_names:
            url_safe_name = urllib.parse.quote(file_name)
            if create_for_s3:
                s3_file_name = url_safe_name.replace(" ", "+")
                image_source = "https://s3.amazonaws.com/{}/{}/{}".format(self.s3_bucket_name, self.s3_key_charts, s3_file_name)
            else:
                absolute_path = "{}/{}".format(Path().absolute(), self.output_dir)
                image_source = "{}/{}.{}".format(absolute_path, url_safe_name)
            print(image_source)
            html_code += "<img src={}></img>".format(image_source)
        html_code += """</body>"""
        output_file_name = "{}/{}".format(self.output_dir, self.donated_charts_webpage_name)
        with open(output_file_name, "w") as outfile:
            outfile.write(html_code)
        return self.donated_charts_webpage_name

    def upload_images_to_s3(self, file_names_to_upload):
        s3_client = self.aws_session.resource('s3')
        for file_name in file_names_to_upload:
            file_path = "{}/{}".format(self.output_dir, file_name)
            s3_client.Bucket(self.s3_bucket_name).upload_file(file_path, "{}/{}".format(self.s3_key_charts, file_name), ExtraArgs={'ContentType': "image/png", 'ACL': "public-read"})

    def upload_webpages_to_s3(self, file_names_to_upload):
        s3_client = self.aws_session.resource('s3')
        for file_name in file_names_to_upload:
            file_path = "{}/{}".format(self.output_dir, file_name)
            s3_client.Bucket(self.s3_bucket_name).upload_file(file_path, "{}/{}".format(self.s3_key_charts, file_name), ExtraArgs={'ContentType': "text/html", 'ACL': "public-read"})


def init():
    if __name__ == "__main__":
        content_creator = ContentCreator()
        url = content_creator.generate_donation_webpage(create_for_s3=True)
        print(url)


init()
