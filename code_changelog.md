# To-Do

### Main problems
- acoustic, instrumental, orcghestral tracks have the same composer as ones without these labels
- consolidate flags into dict
- write automated tests
- write only tags that have changed
- write cover art tag with mutagen and abandon pytaglib
- something is wrong in displaying cropped image, it shows with weird crop

### Freezing problems
- frozen code doesn't run on x86 systems, need 32bit python installation to build 32bit app
- freezed Qt app is too big ~ 0.65GB - most files probably not needed
- use "zip_include_packages" in cx_freeze setup to reduce size refer to:  
    https://github.com/anthony-tuininga/cx_Freeze/issues/256  
    https://stackoverflow.com/questions/27281317/cx-freeze-preventing-including-unneeded-packages
- tcl files are not needed for PyQt version but cx_freeze includes them

### Ideas
- maybe integrate application to parser?
- introduce typing https://docs.python.org/3/library/typing.html this will bind app to python version 3.7, maybe to a great idea?
- parser probably should have its own lock? - access to its mutable variables should be guarded  see 13.1.2019 entry in changelog
- add system tray icon menu: http://rowinggolfer.blogspot.com/2011/06/pyqt-qsystrayicon-example.html
- parser should probably include one API channel to comunicate with "outer" world. Now communication is becoming messy and it is not clear how changes in parser API are affecting other classes that are using it.
- maybe get rid of tkinter GUI? The parser API has changed so much that it does not make sense to keep it
- add cue spliting and audion conversions


###  Individual problem cases 
- load guests as in https://en.wikipedia.org/wiki/Emerald_Forest_and_the_Blackbird
- load composer fails for https://en.wikipedia.org/wiki/Pursuit_of_the_Sun_%26_Allure_of_the_Earth
- tracklist not found here https://en.wikipedia.org/wiki/Ethera
- try extract this https://en.wikipedia.org/wiki/Aina_(band)

# Change Log

### 21.9.2019
- another major GUI restructure
- heavy use of signals and properties to transparently handle variable changes
- implemented tag name based data copying between gui and parser
- new custom classes for QStandardItem and QStandardItemModel for codebase reduction
  and easier readability
- parser is split to multiple files and classes based on responsibility
- some fixes in parser
- implemented own custom for parser
- implemented wrapper to easily handle folder select with remembering
- moved tag writing from GUI to new method in parser
- prepare for use of QThreads, so parser can emit signals to GUI
- all communication with parser is now handled by data_model module, relies
  heavily on use of properties coresponding with tag names
- moved constants to package init module
- altered superclass inintialization order in gui, to aviod problems with
  missing attributes

### 20.9.2019
- further gui rewrite and bugfixes
- split classes to even more basic building blocks
- rewrites to better use Qt signals

### 14.9.2019
- major GUI restructure and cleanup
- GUI is split to more classes and files
- complete overhaul of image search
- fixed numerous bugs
- greatly improved readability

### 13.9.2019
- compatibility layer for all major Qt backends is now implemented
- We support: PyQt5, PyQt4, PySide2 and PySide
- added new dependency: PyQt
- moved Qt importing to separate file
- moved cover art search and its custom Qt classes to separate file

### 12.9.2019
- cover art manipulation is roughly implemented but still quite buggy
- started implementing compatibility layer for different Qt backends, will use
  https://github.com/spyder-ide/qtpy/blob/master/qtpy/QtWidgets.py
- gui needs to be cleaned up 

### 11.9.2019
- offline debug for coverart search is now implemented
- added some random pictures to test/offline_debug folder for testing
- begun works on picture compression
- fixed bug with infinite recursion when setting image size and the
  dimensions where not some nice round numbers

### 9.9.2019
- started to implement offline debug for cover art search

### 8.9.2019
- fixed bug in mp3 and m4a lyrics writing

### 6.9.2019
- restructuring of tags handling, reduced codebase
- added proxy properties to access parser variables, now they can be called
  with same names as tags
- restructured read_files and data_to_dict methods in parser, significant
  codebase reduction and improved readability
- began testing for new cover art handling in tests folder
- implemented new base class for cover art selection popup window

### 5.9.2019
- revisions to preload, reduced preload class codebase and simplification
- preload error messages are now displayed only when search button is clicked
- change of preload handling in GUI, major simplification
- overhaul of lyrics finding function and dulpicate lyrics handling, which
  results in less lyrics downloading if some tracks have same lyrics
- wrote test for lyrics search

### 31.8.2019
- abandon asyncio version of lyricsfinder
- overhaul of the old lyricsfinder version to be thread safe
- ported lyricsfinding from multiprocessing to joblib with threading backend
- result is major speed improvement
- reduce codebase in lyrics functions
- introduce nice ordered printing in lyrics functions
- fix bug in darklyrics extractor

### 30.9.2019
- further development of mutagen implementation
- now if app is run under python 3.6 pytaglib backend is loaded and
  for 3.7 mutagen backend is loaded.
- mutagen implementation is complete for mp3, flac and m4a other file types
  should be easy to add. The API mimics that of pytaglib.
- mutagen needs further testing
- experiments with asyncio lyricsfinder version, seems like thread safety
  affects also async version. Lyricsfinder will need major overhaul to be
  thread safe
- minor bugfixes to gui

### 29.8.2019
- bug fix, preload would reinit parser attributes and gui would display nothing
- started migration to [mutagen](https://mutagen.readthedocs.io/en/latest/index.html)
  tagging library, basic functionality is implemented.
  This will allow to ditch complicated taglib dependency that
  needs compiling and allow saving album art. But mutagen is more difficult to
  use as it doesn't provide the same high level of abstraction. This will need
  to be implemented, along with some tagging restructuring
- taglib version of the code now enters deprecation phase
- whole codebase will migrate to python 3.7 namely lyricfinder module, old
  multiprocessing lyrics search will from now on get only bug fixes and will
  not be further developed
- implemented remembereing last opened dir

### 7.7.2019
- finally timeout is implemented on wiki search
- moved wiki search and soup cooking to separate thread

### 6.7.2019
- lyrics module now supports python 3.6 (multiprocessing) and 3.7 (asyncio),
  asyncio support is experimental for now.
- still cannot compile pytaglib for python 3.7
- minor bugfixes
- moved edited versions of external libs (google_images_search, lyricsfinder)
  to new folder.
- further reorganizing of code, moved setup files to separate folder
- started writing automated tests
- added command line argument parser

### 24.6.2019
- bugfixes and further restructure
- moved table extractors to own class
- replaced json with YAML and implemented loading
- created new folder with settings

### 22.6.2019
- major restructure of package. Now it is more comprehensible.
- transformed class in sync.py, now all attributes belog to class. This solves
  many import problems
- helper methods are moved to utilities directory
- major simplification of package __init__.py file - import simplification
- utils.py module is split to 3 modules, one for GUI, one for parser and
  one general
- UI base classes now have their own directory
- library imports are fixed and work OK now
- loggers have their own module now located in utilities
- all imports have been revised, resulting in great simplification and
  readability improvement
- nltk importer thread now implements its own lock so nltk lib cannot be
  accessed before it is imported

### 20.5.2019
- edits to preload method gui is now split to multiple classes which are then
  inherited by the main
- implemented killable thread for preload

### 18.5.2019
- more strict PEP8 adherance
- minor bug fixes
- significant speedups by moving some data processing to other threads
- implemented preloading of wiki page for aditional speedup

### 28.4.2019
- added for/else clauses for readability
- use f-strings instead of format() function
- parser function names to lowercase according to PEP8 guidelines
- merge most parts of disk write and console printing

### 19.2.2019
- minor bug fixes to lyrics writing
- some use of f-strings

### 27.1.2019
- cover art search dialog now has its own base class created in qt designer

### 26.1.2019
- numerous bug fixes
- rewrite code in a nicer more pythonic way
- write docstrings in utils module
- new much better method of wikipedia page guessing

### 16.1.2019
- changes to handling google api key

### 14.1.2019
- Added cover art search with proper GUI window

### 13.1.2019 
- got rid of the global statements functions do not make a local copying of object as it is done with variables, they simply reference the original object  
- major cleanup in locks - most were not needed as they where guarding atomic operations  
- marked non-atomic operations on parser object, for now they are without lock since all operations on parser should be done serialy  
- major reorganization of tag writing function  
- moved wrappers to __init__  

### 12.1.2019 
- started test for retrieving images in tests/cover_art.py using [google-images-download](https://github.com/hardikvasa/google-images-download#), quite starightforward - need to make only fronted - some popup window  
- selected pic will be resized and the copied to clipboard to paste in mp3tag  
- do not use tineye - too complicated  

### 11.1.2019
- Added super-duper hack with subclassing QStandarditem so we can display full path in the detail window effortlessly  
- codebase for gui PyQt now has ~30% less lines compared to Tkinter  
- added button for searching for each track file  
- use decorators for exceptions where aplicable  
- fixed few bugs caused by differences between Tkiniter and PyQt  
- fixed bug - writing tags overides any manually assigned files to tracks  
- added setup_qt.py for freezing the Qt version of app  
- some code cleanup and reorganizing  

### 10.1.2019
- Continue porting efforts. Much of the things can be done in similar way with only minor alterations  
- All methods are now ported to PyQt5  
- Need to port some remaining detailes, and fix bugs  
- Need to come up with some workarounds or new approaches, since PyQt philosophy is different from Tkiniter, mailny it is not able to track variable changes - use signals and slots instead  
- Extensive testing is needed

### 9.1.2019
- started porting to PyQt  
- data reading from HDD and sorting in table is now working. Sorting is much more elgant than in tkinter.  
- Need to addres the issue with PyQt not tracking variables though.  
- This is much simpler in Tkiniter.  

### 18.9.2018
- composers extraction has been completely reworked should be more robust. the function now inputs data directly to tracklist_composeres list  
- new method for offline debugging has been implemented reads the wikipedia.page object from picle file on disc  
- implemented saving of wikipedia.page to disk with use of pickle  
- new re_init method in sync class to avoid overwriting variables at the start of the run  
- added signal handler to catch ctrt-C and exit gracefully  
- removed tracklist_composeres, now we have only composers which is a 2D list  
- started code update to PEP8 style coding  

### 27.8.2018
- improved, more robust methods for extracting genres and release dates  
- implemented cover art download from wikipedia  
- substantial improvement to wiki page selection  
- added removing (bonus track) and similar appended strings in brackets from track names  
- added checking track name <--> file name, not against whole path as this caused some wrong matching when album had the same name as one of the tracks  
- added thorough check for band name on the found page if other band than the one that was input is found user is asked if he wants to continue the search

### 26.8.2018
- added workaround when there is no page content
- made json dump optional

### 25.8.2018
- added copying of NLTK data to build folder to setup.py without it program was unable to run on diferent PCs
- now we are able to read tracklists which are not formated in table
- bracket behind track is now checked for special characters like , / \ etc. which indicates that more artists are present. The string is than split on these delimiters and all are checked against aditional personnel
- parser now has its own logger and catches exceptions on lower level which does not halt the main thread
- minor tweak to ID3_tags.py .mp3 files apparently also have lyrics under LYRICS tag same as .m4a

### 24.8.2018
- some further code reorganize
- added logger to ID3_tags
- hopefully all possible exceptions are now caught and subsequently sent to corespondind logger, displayed in GUI and printed to console
- added log_print function to application.py which takes care of logging, printing and sending messages to gui
- some gui polishing, either tkinter is worth shit or I am. Working with it is really painful

### 23.8.2018
- now all modeles that can be, are lazy imported
- some lazy imports had to be omitted as they caused some weird interactions which resulted in throwing exceptions.

### 22.8.2018
- solved problems with parser import
- package has now new structure

### 21.8.2018
- finally caught the sneaky bug causing the sys.stdout.flush() exception. It was in multiprocessing.process. stdout apparently can be None in some situations in which case flush of the stream causes attribute error. Thanks to https://stackoverflow.com/questions/37212551/cx-freeze-using-sys-stdout-flush-and-multiprocessing I got It.
- the bug is probably related to multiprocessing freeze_support()

### 20.8.2018
- problems with imports. parser is not imported in spawned processes
- added icons

### 15.8.2018
- freeze support is now working for the consolee app
- various problems encountered with multiprocessing
- appending correct values sys path so we can load whole module
- non-trivial modifications to lyricsfinder needed in order for it´s imports to work properly
- gui freeze support is partialy working now there is some wild bug in lyrics module
- setup.py is now one unified file for GUI and console app
- first implementation of logging, this prooves to be mighty usefull for debugging compiled GUI app. Need to use it moooar!!!

### 14.8.2018
- various bug fixes
- improved search for composer names
- started work on freeze support, cx_freeze was chosen

### 13.8.2018
- implemented advanced sorting of columns in Tkinter
- lyrics download is now parallel. This gives 1.5x - 2x speed
- GUI now displayes in the title what is going on
- various bug fixes
- implemented sorting when reading data from disc

### 12.8.2018
- separate lyrics method is now working
- some wild spaces flying around in entries with multiple items separated by commas
- first basic concept of sorting is implemented
- reload from disc now works
- interactive console mode abandoned in favour of gui

### 11.8.2018
- separate method for downloading lyrics only
- file matching to song titles repaired

### 2.7.2018
- started to develop binding between console app and gui. Its a mess, need to research other methods

### 26.6.2018
- we have working input there is no output yet

### 24.6.2018
- works on gui started. Using Tkinter

### 22.6.2018
- testing of recursive functions to use in parser.COMPLETE method for simplicity, less lines and maybe redability :D
- minor tweaks to how CDs are identified
- artists in columns after tracks are now loaded to artist if header has no corresponding label or to composers if one of the defined labels is found

### 21.6.2018
- added lazy loading for better startup speed
- addeed some multiprocessing and threading to further impove speed mainly to lyrics dowloading
- some other optimizations and code cleanup
- wikipedia parser class is now loded from __init__.py

### 20.6.2018
- added json dum so we dont have to dwnolad data all over again
- all variables are now stored in parser object
- fixed ordering of artists

### 17.5.2018
- compiled taglib, pytaglib and lyricsfinder
- preparations for tag writing and lyrics search
- experiments with GUI libraries. Qt - too complicated, Tkinter will be used
- read disk label for every disk which is in separate table
- use NLTK for extracting composers, considerably better results

### 14.5.2018
- split code to more files for better orientation
- prepares for GUI

### 10.5.2018
- starting to implement fuzzywuzzy

### 18.2.2018
- added ability to search darklyrics to lyricsfinder module + minor changes
- more work done in lyrics.py a ID3_tags.py

### 2.2.2018
- fixed bug in ordering artists when list length was = 0
- added automatic opening of the folder with output files

### 19.1.2018
- make automatic test on some ensemble
- started to develop interactive console mode

### 9.1.2018
- fixed - sometimes composer not found
- fixed - sometimes in personel there is bracket at the end
- added extracting composers from bracked following track name
- added extraction of instrumental, acoustic, orchestral ... track types

### 20.12.2017
- added extraction of release date and genre from wikipedia
- modifications to lyricsfinder. If google custom search does not work then addresses are generated according to template

### Septemder 2017
- development start
