# MailchimpImporter
An importer of Mailchimp data


Architecture

S3 Bucket with companies/mail lists json config files - in format which can be read by the python class.
These lists will be split up across multiple config files so that the time taken to complete a full sync is no
more than 15 minutes of full load - which would be the worst case scenario for an incremental sync.

First S3 Bucket for initial Sync - This will take longer and is expected - once the initial sync has been finished
on the data set the config is moved into the second bucket

Second S3 Bucket which will contain the configs of company lists that only require partial updates.

Cloudwatch event rules

We will have a cloudwatch event rule which will launch an ECS task of a containerized version of the python class
which will do an incremental sync every x(5? 15?) minutes for every config file. When we run a sync task for a
config file we save the corresponding the run time saved in UTC, this could be in file in the bucket. We know the
time that we ran the initial sync or the last incremental sync, so when doing a list request from mailchimp we only
ask for items that have been updated since the last sync time.


Sync Flag
