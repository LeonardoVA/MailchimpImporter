"""Contains MailchimpImporter class"""
import pprint
import json
import os
import sys
from datetime import datetime

import requests

class MailchimpImporter:
    """class handles making requests to retreive mailchimp data for multiple
    companies possibly with multiple lists (as defined in the config file passed in)"""

    def __init__(self, config_file_path):
        """

        :param config_file_path: The config file to use for what lists to import
        """
        self.config_file_path = config_file_path

    @staticmethod
    def send_transformed_data(data,
                              endpoint="http://ec2-34-242-147-110.eu-west-1.compute.amazonaws.com:8080/record"):
        """

        :param data:
        :param endpoint:
        :return:
        """

        if not data:
            print("No Data to send since last sync for this part of the list")
            return

        print(f"Attempting to send data to endpoint: {endpoint}")
        api_key = "2ca89228-266a-4c4c-b4ec-d6c2bdadfdf0"
        headers = {'Authorization': api_key,
                   'Content-Type': 'application/json'}

        res = requests.post(endpoint, data=json.dumps(data), headers=headers)
        print(f"\nresponse: {res.text}\n"
              f"data tried: {json.dumps(data)}\n")


    @staticmethod
    def set_off_cloudwatch_alarm(alarm_string):
        """

        :param alarm_string:
        :return:
        """
        print("Here we would set off the aws cloudwatch alarm, which would be "
              "plugged into sns to inform ometria of a failure in the system.\n "
              f"Example alarm string: {alarm_string}")

    def check_and_process_response(self, response, api_key):
        """

        :param response:
        :param api_key:
        :return:
        """
        if response.status_code == 200:
            ometria_formated_data = self.process_request_data(response)

            print(f"Finished transformed data: {ometria_formated_data}")

            self.send_transformed_data(ometria_formated_data)


            # This true is just to check if the initial request returned a 200 it doesn't
            # guarantee success later on it designed to fail gracefully for some things
            # and continue trying the rest
            return True

        error_string = f"Error making response to url: {response.url} with api key: {api_key}.\n"\
                       f"See response: {response.status_code} {response.text}"

        self.set_off_cloudwatch_alarm(error_string)
        return False


    def process_request_data(self, request_response):
        """

        :param request_response:
        :return: returns either the transformed data or false if it wasn't
        able to transform this section of the list
        """
        transformed_list_data = []
        for x, list_entry in enumerate(request_response.json()['members']):

            print(f"\nEntry number {x+1}\n")
            # transform data in ometria friendly format
            try:
                transformed_entry = {"id":list_entry['id'],
                                     "firstname": list_entry['merge_fields']['FNAME'],
                                     "lastname": list_entry['merge_fields']['LNAME'],
                                     "email": list_entry['email_address'],
                                     "status": list_entry['status']}

                transformed_list_data.append(transformed_entry)
            except KeyError as key_error:
                print(f"Error: There was an issue: {key_error} transforming data to ometria format for entry:")
                pprint.pprint(list_entry)
                return False

        return transformed_list_data


    def create_url(self, count, list_id):
        """

        :param count: The number of items we would like to get back from this request max 1000
        :param list_id: The mailchimp list id
        :return mailchimp_url: A completed mailchimp URL,
        """
        mailchimp_partial_resquest_url = "?fields=members.email_address,members.id," \
                                         "members.status,members.merge_fields," \
                                         f"members.last_changed,total_items&count=2"
        partial_sync_url = ""
        if not FULL_SYNC:
            try:
               # At the moment reads local file this will be a file in S3 in future.
               last_run_json = MailchimpImporter.read_json_file(f"{self.config_file_path}.time")

               # If we are doing a partial sync request only things that have changed since then
               # to cut down on data
               partial_sync_url = f"&since_last_changed={last_run_json['Time']}"

            except FileNotFoundError:
                print("Please ensure you have run a full sync before running incremental "
                      f"Last known run time file could not be found: {self.config_file_path}.time")
                sys.exit(1)

        mailchimp_url = f"https://us9.api.mailchimp.com/3.0/lists/{list_id}" \
                        f"/members{mailchimp_partial_resquest_url}{partial_sync_url}"

        return mailchimp_url

    def get_mail_list(self, list_id, api_key):
        count = 1000

        auth_tuple = ("", api_key)

        mailchimp_url = self.create_url(count, list_id)

        response = requests.get(mailchimp_url, auth=auth_tuple)

        response_success = self.check_and_process_response(response, api_key)

        # Check if we got all the list entries or there is more to do
        if response_success:

            total_items = response.json()['total_items']
            # We just got the first 1000, count will still be 1000
            while count < total_items:
                offset_url = f"&offset={count}"
                response = requests.get(mailchimp_url+offset_url, auth=auth_tuple)
                self.check_and_process_response(response, api_key)
                count += 1000
            # Now write datetime file so that we can filter further requests for incremental sync
            time = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S+00:00.')
            print(f"Finished getting this mail list! count was up to {count} "
                  f"and time is {time}")
            MailchimpImporter.write_json_time_file(time, f"{self.config_file_path}.time")

    @staticmethod
    def write_json_time_file(time, file_name):
        with open(file_name, "w") as json_file:
            json.dump({"Time":time}, json_file)

    @staticmethod
    def read_json_file(file_name):
        """Be wary this method will load the contents of the files in
        the mail list directory into memory"""

        with open(file_name) as mail_list_json_file:
            json_data = json.load(mail_list_json_file)

        return json_data

    def retreive_contact_data(self, mail_list_data):
        print(f"Config file to use for this import:\n {mail_list_data}")
        for company in mail_list_data['Companys']:
            print(f"\nProcessing lists for company: {company['Name']}")
            for count, mail_list in enumerate(company['Mail_Lists']):
                print(f"\nProcessing list {count+1}\n")
                self.get_mail_list(mail_list['list_id'], mail_list['api_key'])


    def start_import(self):
        """Start Method for the importer, reads the config file then calls rest of program"""
        mail_list_data = MailchimpImporter.read_json_file(self.config_file_path)
        self.retreive_contact_data(mail_list_data)






if __name__ == "__main__":
    # Env variable over cmdline so that it can be one container image and just pass in
    # different env vars in the task settings for AWS ECS
    FULL_SYNC = os.getenv("FULL_SYNC")
    if FULL_SYNC:
        print("Full sync detected!")

    # At the moment we just use the default hardcoded list but in the future this will
    # Be passed through to the container via environment variable
    default_config_file = "company_mail_lists/company_mail_list_1.json"

    mailchimp_importer = MailchimpImporter(default_config_file)
    mailchimp_importer.start_import()
