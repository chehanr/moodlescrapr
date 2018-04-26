# moodlescrapr
A simple (very badly written) ACBT scraper to download course files. 

### Usage: 
Run `python moodlescrapr[2-3].py` 

#### GUI:
Run `gui.py` or run a downloaded executable from [releases](https://github.com/chehanr/moodlescrapr/releases). 

##### Building:
- Install [pyinstaller](https://www.pyinstaller.org/)
- Run `pyinstaller build.spec`
 
### Additional Options:
    usage: moodlescrapr [-h] [-u USERNAME] [-p PASSWORD] [-s SUBJECT] [-w WEEK]
                        [-l]

    ACBT moodle scraper (by chehanr)

    optional arguments:
      -h, --help            show this help message and exit
      -u USERNAME, --username USERNAME
                            moodle username
      -p PASSWORD, --password PASSWORD
                            moodle password
      -s SUBJECT, --subject SUBJECT
                            scrape only specific subject (comma separated)
      -w WEEK, --week WEEK  scrape only specific week number (comma separated)
      -l, --list-subjects   list available subjects

### Prerequisites: 
Run `pip install -r "requirements.txt"` 

If you're using `moodlescrapr3.py` (`gui.py`) you must have `wget` installed and placed in your `PATH` or placed inside the directory/ ENV. 

 ~~*Note:*  Make sure to have all week containers in the moodle expanded before running this script.~~

 *Note-2:*  Only tested on my account.

 *Note-3:*  Since `Note-2` I can't add support for some file types ~~(.xlsx)~~ because I couldn't find them on my moodle. If an error pops up create an issue or submit your own fix as a fork.  

 *Update:*  On the process of rewriting the script, use `moodlescrapr3.py` (Might not work properly). 