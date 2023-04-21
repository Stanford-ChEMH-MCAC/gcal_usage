# standard lib imports
from __future__ import print_function
import httplib2
import os
import datetime
import argparse

#  parsing isoformat dates
import dateutil.parser

# oauth2 imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# pandas
import numpy as np
import pandas as pd

# global variables
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = '/Users/curt/SECRET/client_secret.json'
APPLICATION_NAME = 'Octant Google Calendar Usage Log'

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
            default=None,
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

        if parsed.output_file is None:
            start = parsed.start_date.date()
            end = parsed.end_date.date()
            calendar = parsed.calendar
            parsed.output_file = 'from_{}_to_{}_{}.csv'.format(start, end, calendar)
        
        return(parsed)

    except ValueError:
        print('Unable to parse arguments.')

def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        creds, the obtained credential.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

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
    service = build('calendar', 'v3', credentials=credentials)

    cal_start = start_date.isoformat() + 'Z'
    cal_end = end_date.isoformat() + 'Z'

    # get calendarId from input arg
    calendar_flag = args.calendar
    if calendar_flag == 'access':
        calendar_id = 'c_1886qo4c7unqigb4m1obks43vft66@resource.calendar.google.com'
    else:
        raise ValueError('Only supported calendars is "access".')

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

    print('Found {} events totalling {} hours and wrote to file {}'.format(len(out_df),
                                                                           out_df['duration_hr'].sum(),
                                                                           out_file))
    out_df.to_csv(out_file, index=False)


if __name__ == '__main__':
    main()