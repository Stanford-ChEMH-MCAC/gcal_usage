# gcal_usage

This repository contains a python script for analyzing the users (event creators) and hours (total duration of events) on a [Google calendar](https://www.google.com/calendar/about/) in specified intervals of time.  The script relies on Google's [Google calendar python API](https://developers.google.com/calendar/quickstart/python).  The [ChEM-H MCAC](https://chemh.stanford.edu/knowledge-centers/metabolic-chemistry-analysis-center) uses this script to distribute operating costs for our LC-MS instruments to our collaborators on a usage-time normalized basis.

We are publishing it because (a) we want to be transparent about how our cost-sharing is done and (b) because learning the Google calendar API took a lot of time and there is a chance this may be useful to other folks that use Google Calendar to track instrument usage.

## Installation

The script here is not packaged for easy installation; you will have to download the source and manually integrate it into your own stack.

## Requirements

Requirements are many and varied.  A rough guide:

* python 3.5 or higher
* all the requirements for the Google Calendar API (e.g. `apiclient` and `oauth2client`)
* numpy, pandas, and other standard python libraries.
* the [`dateutil`](http://dateutil.readthedocs.io/en/stable/) package for parsing isoformatted datetime strings.
* `argparse`.

* general tip: use the [conda](https://conda.io/docs/) system for package management and installation.

## Usage example:

### Log creation

`python get_gcal_log.py -s 2018-01-01 -e 2018-02-01 -c qqq`

results in 

`Found 35 events and wrote to file out.csv` being printed to standard out and a file out.csv that looks like this:

```
calendar	created_at	creator_email	creator_name	end_time	event_id	event_name	start_time	updated_at	duration_hr
qqq	2018-01-02T19:52:27.000Z	EMAIL1@example.com	Charles C. Collaborator	2018-01-02 17:30:00-08:00	_8p0jgh9m851jgba16h2jgb9k651jiba18l0jcb9i6p0j8hhg6h23cc1n8k	event_name_1	2018-01-02 12:00:00-08:00	2018-01-02T19:54:07.690Z	5.5
qqq	2017-12-29T20:53:07.000Z	EMAIL2@example.com	Beverly W. Coworker	2018-01-04 07:15:00-08:00	5bpocmj2bcrohgr86683oqct4o	event_name_2	2018-01-03 07:45:00-08:00	2018-01-04T00:06:32.532Z	23.5
<etc>									
```

### Aggregation by user:

The `-b True` flag allows aggregation of time by event creator.

`python get_gcal_log.py -s 2018-01-01 -e 2018-02-01 -c qqq -b True`

results in a .csv file that looks like

```
creator_name	duration_hr	calendar	creator_email
Charles C. Collaborator	35.25	qqq	email1@example.com
Beverly W. Coworker	6	qqq	email2@example.com
<etc>
```

### Getting help

`pyton get_gcal_log.py -h` results in 

```
usage: get_gcal_log.py [-h] -s START_DATE [-e END_DATE] [-f OUTPUT_FILE]
                       [-c CALENDAR] [-b BY_USER]

optional arguments:
  -h, --help            show this help message and exit
  -s START_DATE, --start_date START_DATE
                        Retrieve events after this date, format YYYY-MM-DD
  -e END_DATE, --end_date END_DATE
                        Retrieve until after this date, format YYYY-MM-DD
  -f OUTPUT_FILE, --output_file OUTPUT_FILE
                        Filename of csv file to store
  -c CALENDAR, --calendar CALENDAR
                        Which Google Calendar to interrogate ('qtof' or 'qqq')
  -b BY_USER, --by_user BY_USER
                        whether to aggregate output by user

```

## License

This code is licensed with the [MIT License](https://opensource.org/licenses/MIT).






## Contributing

Pull requests are welcome.  If you have questions about how any bit of this works, please file an [issue](https://github.com/Stanford-ChEMH-MCAC/gcal_usage/issues) here on GitHub.

## Authors

* The code, as of June 2018, was written by [Curt R. Fischer](https://github.com/Stanford-ChEMH-MCAC/).

## License

This code is licensed with the [MIT License](https://opensource.org/licenses/MIT).
