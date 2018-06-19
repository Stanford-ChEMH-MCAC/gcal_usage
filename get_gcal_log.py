# standard lib imports
from __future__ import print_function
import httplib2
import os
import datetime
import argparse

#  parsing isoformat dates
import dateutil.parser

# oauth2 imports
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

# pandas
import numpy as np
import pandas as pd

# global variables
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = '../../SECRET/client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def parse_arguments():
    """
    Parses arguments from the command line.
    """
    def valid_date(s):
        """
        Determines if input string s is a valid date.
        """
        try:
            return datetime.datetime.strptime(s, "%Y-%m-%d")
        except ValueError:
            msg = "Not a valid date: '{0}'.".format(s)
            raise argparse.ArgumentTypeError(msg)

    try:    
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '-s',
            "--start_date", 
            action='store',
            help="Retrieve events after this date, format YYYY-MM-DD",
            required=True,
            type=valid_date
                        )
        parser.add_argument(
            '-e',
            "--end_date", 
            action='store',
            help="Retrieve until after this date, format YYYY-MM-DD",
            required=False,
            default=None,
            type=valid_date
                        )
                        
        parser.add_argument(
            '-f',
            "--output_file", 
            action='store',
            help="Filename of csv file to store",
            required=False,
            default='out.csv',
            type=str
                        )

        parser.add_argument(
            '-c',
            "--calendar",
            action='store',
            help="Which Google Calendar to interrogate ('qtof' or 'qqq')",
            required=False,
            default='qtof',
            type=str
                        )

        parser.add_argument(
            '-b',
            "--by_user",
            action='store',
            help="whether to aggregate output by user",
            required=False,
            default=None,
            type=bool
                        )
        
        parsed = parser.parse_args()
        
        if parsed.end_date is None:
            today = datetime.datetime.utcnow()
            parsed.end_date = today
        
        return(parsed)

    except ValueError:
        print('Unable to parse arguments.')

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, None)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def main():
    """
    Reads a Google Calendar and outputs a .tsv file of up to 2500
    events on the calendar starting from supplied date.
    """
    args = parse_arguments()
    start_date = args.start_date
    end_date = args.end_date
    out_file = args.output_file

    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    cal_start = start_date.isoformat() + 'Z'
    cal_end = end_date.isoformat() + 'Z'

    # get calendarId from input arg
    calendar_flag = args.calendar
    if calendar_flag == 'qtof':
        calendar_id = 'gnpn.chemh.lc.ms@gmail.com'
    elif calendar_flag == 'qqq':
        calendar_id = '3eic0r8c6jmtdf9e350dg8cl74@group.calendar.google.com'
    else:
        raise ValueError('Only supported calendars are "qtof" and "qqq".')

    # whether to aggregate by user:
    if args.by_user:
        aggregate = True
    else:
        aggregate = False

    eventsResult = service.events().list(
        calendarId=calendar_id,
        timeMin=cal_start, 
        timeMax=cal_end,
        singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No events found in specified date range.')

    # initialize lists that will become pd.DataFrame columns
    event_ids = []
    event_names = []
    creator_names = []
    creator_emails = []
    start_times = []
    end_times = []
    created_at = []
    updated_at = []
    
    # process all events, adding them to above lists if criteria are met
    for event in events:
        # skip events that have no start or end times
        if 'dateTime' not in event['start'].keys():
            continue
        if 'dateTime' not in event['end'].keys():
            continue

        # skip events that contain "EXCLUDE" in the event name
        if 'EXCLUDE' in event['summary']:
            continue

        # add "unknown" placeholder to missing names / emails
        creator_keys = ['displayName', 'email']
        for needed_key in creator_keys:
            if needed_key not in event['creator'].keys():
                event['creator'][needed_key] = 'unknown'

        event_ids.append(event['id'])
        event_names.append(event['summary'])
        creator_names.append(event['creator']['displayName'])
        creator_emails.append(event['creator']['email'])
        start_times.append(event['start']['dateTime'])
        end_times.append(event['end']['dateTime'])
        created_at.append(event['created'])
        updated_at.append(event['updated'])

    # convert to dataframe
    out_df = pd.DataFrame({
                          'calendar': calendar_flag,
                          'event_id': event_ids,
                          'event_name': event_names,
                          'creator_name': creator_names,
                          'creator_email': creator_emails,
                          'start_time': [dateutil.parser.parse(s) for s in start_times],
                          'end_time': [dateutil.parser.parse(s) for s in end_times],
                          'created_at': created_at,
                          'updated_at': updated_at
                          })

    out_df['duration_hr'] = (out_df['end_time'].sub(out_df['start_time'])) / np.timedelta64(1, 'h')

    # do aggregation, if requested
    if aggregate:
      out_df = out_df.groupby('creator_email').aggregate({'calendar': 'first',
                                                          'creator_name': 'first',
                                                          'creator_email': 'first',
                                                          'duration_hr': 'sum',
                                                          }, axis='columns')

    print('Found {} events and wrote to file {}'.format(len(out_df), out_file))
    out_df.to_csv(out_file, index=False)

if __name__ == '__main__':
    main()