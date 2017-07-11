# moodlescrapr
A simple (very badly written) ACBT scraper to download course files. 

Usage: 

Run `python moodlescrapr.py` 

Additional options:

    moodlescrapr [-h] [-u USERNAME] [-p PASSWORD] [-s SUBJECT] [-w WEEK]
    
    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            moodle username
      -p PASSWORD, --password PASSWORD
                            moodle password
      -s SUBJECT, --subject SUBJECT
                            scrape only specific subject
      -w WEEK, --week WEEK  scrape only specific week number (w 0 = outline)

Prerequisites: 

    bs4 == 0.0.1
    requests == 2.18.1

 *Note:*  Make sure to have all week containers in the moodle expanded before running this script. 

 *Note-2:*  Only tested on my account.

 *Note-3:*  Since `Note-2` I can't add support for some file types (.xlsx) because I couldn't find them on my moodle. If an error pops up create an issue or submit your own fix as a fork.  