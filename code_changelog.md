# To-Do

### Main problems ordered by targeted release
- 0.7a0
  - handle name permutations like: Anthony Lucassen Arjen, Arjen Anthony Lucassen
  - probably encoding problem when downloading lyrics
  - treadpool progressbar is not showing or showing late !!!!!!!
  - add button to open lyrics url _lyric_sources is prepared for that and button to open browser with lyrics search
  - when genre is N/A in search if rewritten in GUI it reverts back To N/A on save
  - problem with writing lyrics to flac files or maybe only rocketplayer does
    not know how to read them
  - something is wrong with artist completition when reading file from disk
    for this album https://en.wikipedia.org/wiki/Ayreon_Universe_–_The_Best_of_Ayreon_Live
  - fix as many bugs as possible
  - update manifest and check build system
  - use show() or open() for non-modal dialogs and messages
  - a lot of errors when writing tags
      Traceback (most recent call last):
      File "c:\users\marián rynik\onedrive\dokumenty\visual studio 2019\projects\python\wiki_music\wiki_music\utilities\wrappers.py", line 48, in wrapper
        return function(*args, **kwargs)
      File "c:\users\marián rynik\onedrive\dokumenty\visual studio 2019\projects\python\wiki_music\wiki_music\utilities\wrappers.py", line 85, in wrapper
        return function(*args, **kwargs)
      File "c:\users\marián rynik\onedrive\dokumenty\visual studio 2019\projects\python\wiki_music\wiki_music\library\tags_io.py", line 153, in read_tags
        return tags
      UnboundLocalError: local variable 'tags' referenced before assignment 
  - add defaut aspec ratio checked for image editor
  - ger coverart from url should open browser window with search
  - use https://github.com/sczhengyabin/Image-Downloader instead of google images download
- 0.8a0
  - better modularity for GUI one superclass is a bad idea, we have to limit
    interactions and side effects to minimum. The namespace of the GUI class
    is gigantic and poluted with names inimportant to whole object.
  - implement undo/redo https://www.informit.com/articles/article.aspx?p=1187104
  - fix travis CI system setup
- 0.xb0
  - parallel freezing should implement locks on some resources, otherwise
    processes colide
  - fix a problem with google images download https://github.com/hardikvasa/google-images-download/issues/302 until then add a warning if no coverart could be downloaded
  - make proper progressbar indicators
  - fix gui scaling and elements moving around
  - convert constants to re patterns for better matching and use more re for better extraction
  - make parser parts as plugins so different parts of extraction can use
    different backends
  - cells with dropdowns for subtracks
  - make parser iterable
  - implement image search controls
  - support more music formats
  - keep reference of all running threads and gui elements and cleanup on exit
    use atexit module
- 1.0.0
  - write automated tests
  - use https://coveralls.io for code test coverage stats


### Freezing problems
- upx probably messes some dll, PIXmap does not work, pictures are blank

### Ideas
- add system tray icon menu: http://rowinggolfer.blogspot.com/2011/06/pyqt-qsystrayicon-example.html
- add cue spliting and audio conversions
- migrate to QThreads, Qsignals don't work with threading module
- include different backends than wikipedia
- represent each song with its own class
- research PIL interface to PyQt, and what about Pyside?
- cover art search could anounce new downloaded images by signals
  if we were using QThreads
- use themes https://github.com/ColinDuquesnoy/QDarkStyleSheet ,
  https://github.com/seanwu1105/pyqt5-qtquick2-example
- enable to open files from more dirs at once, when files are spread
- implement web based GUI through flask
- implement a threadsafe dict alternative to queue for control queues or
  maybe use some alternative to multiprocessing pipe
- https://github.com/beetbox/beets
- https://picard.musicbrainz.org
- http://docs.puddletag.net/about.html
- https://acoustid.org/chromaprint


###  Individual problem cases 
- load guests as in https://en.wikipedia.org/wiki/Emerald_Forest_and_the_Blackbird
- load composer fails for https://en.wikipedia.org/wiki/Pursuit_of_the_Sun_%26_Allure_of_the_Earth
- tracklist not found here https://en.wikipedia.org/wiki/Ethera
- try extract this https://en.wikipedia.org/wiki/Aina_(band)
- non existent name appearing here https://en.wikipedia.org/wiki/Queen_of_Time
- extract appearences like in https://en.wikipedia.org/wiki/Ayreon_Universe_–_The_Best_of_Ayreon_Live
  and info from brackets
- cannot handle french lyrics! for https://genius.com/albums/Alcest/Spiritual-instinct
- on save Star One artist name is getting split to letters https://en.wikipedia.org/wiki/Space_Metal_(Star_One_album)
- wrong parse of tracklist here: https://en.wikipedia.org/wiki/Space_Metal_(Star_One_album)
  times are not deleted from track name

# Release checklist
- update version
- update docs as necessary
- run build docs test
- remove dirs `dist` and `build`
- build wheel with `python setup.py build bdist_wheel`
- check if proper files are present in wheel
- upload with `twine upload dist/*`
- build frozen app, check if it runs, package to zip
- create a github release

# Change Log

### 19.4.2020
- lowered fuzz ratio for coverart matching on wikipedia

### 18.4.2020
- fixed bug in reading flac files when no cover art was in file

### 5.3.2020
- maybe fixed coverart not resizing bug
- fixed bug when there was fewertracks on disk tha found tracks on wiki, files
  were assigned incorrectly

### 4.3.2020
- fixed bud with wrong identified files, if they were in sudirs of the work dir
- fixed bud in extraction of tables, when wrong html part was
  passed to extractor
- fixed bug if no personel section was on page
- added option to load cover art from url

### 3.3.2020
- experiments with async version of pool similar to asyncio, so the pool
  does not halt main loop but still can wait for results

### 31.3.2020
- added textwrap.fill to format long paragraphs of text in console
- fixed bug. If artist field is empty, album artist is passed there on save
  and split to letters

### 15.3.2020
- fixed reading coverart file from disk
- bug with recuring gender prompt is probably fixed, caused by stupid typo
  wiki:search function was connected to wrong QAction signal in menubar

### 13.3.2020
- patched freeze process, fixed minor bugs
- upgraded to pyinstaller 3.6
- search and replace is finished
- added icons from tango https://commons.wikimedia.org/wiki/Tango_icons
- written a generator for icon resources based
  on https://github.com/ppinard/qtango
- updated docs

### 12.3.2020
- impovements to search and replace

### 11.3.2020
- additional spliting of code, custom classes noe occupy independent
  sub-directory.

### 10.3.2020
- tidying up and consolidating search & replace codebase
- split master GUI class to more files

### 9.3.2020
- search & replace controls are almost finished color higlighting is working
  up to 80% of times

### 8.3.2020
- implemented QStyledDelegate to control search & replace highlight colors

### 7.3.2020
- started implementing search and replace function, search is complete.
  Replace shouild be working by highlighting and moving to next/previous is
  broken for now. For now respective classes and functions are scattered
  around the code, this shold be consolidated upon completion.

### 28.2.2020
- implemented loading coverart from disk to editor

### 23.2.2020
- added logs with caller traces to action class to hunt down, bug with double
  display of gender prompt

### 20.2.2020
- bugfix when there were more songs than files the remaining song would be
  ignored by parser and because of that table fields in GUI would not exist
  and this would throw exceptions whenever table cell was clicked

### 6.2.2020
- fixed bug, save all would save only selected tracks if some of the track
  were actually selected. If none was selected it worked normal

### 12.1.2020
- caught bug when flac artist were not split

### 11.1.2020
- got rid of yaml dependency, replaced with json for saving album data
  and configparser for saving configuration *.ini files
- fixed bug in flac tags reading, only first value of coverart bytes was fetched 
- added multi threaded switch to GUI
- enhanced composer extraction from brackets in track name

### 10.1.2020
- implemented some itertools and operator functions to shorten codebase
- new more reliable wiki page guessing in difficult scenarios

### 5.1.2020
- some minor code cleanup, remove normalize_caseless from fuzzywuzzy functions,
  as they cast to lowercase by default
- handle when we end up on artist page instead of album page

### 24.12.2019 - 0.6a0
- drag&drop is implemented and working
- fixed bug  when NLTK import would delay start of the whole app
- moved last opened dir to settings
- significant startup speedups from NLTK fix and delayed preload
- got rid of timing methods in favour of yappi
- last opened dir is now cached in YmlSettings
- cleaned profiling methods, stats are now saved to own directory
- started monitoring dependencies with https://requires.io
- implemented Travis CI system, testing for Windows, Linux and MacOS with
  python versions 3.6 - 3.8. Except MacOs does not have 3.8
- added more badges to README
- handle CTRL-C gracefully in GUI

### 23.12.2019
- started to implement drag and drop for folders into table to easilly
  import album dirs
- implemented CustomQTableView class. It is replaced by QTableView placeholder
  in QtDesigner
- preliminary implementation is complete. Have to reimplement: dragEnterEvent,
  dragMoveEvent and dropEvent

### 18.12.2019
- slow file load speed is finally resolved, added Qtimer to delay preload start
  by 0.5 seconds.
- python 3.5 has typing too, but no f-strings so it will not be supported

### 17.12.2019
- found the source of slow file loading - preload is slowing us down - maybe too
  many instances are running
- changes to yappi implementation

### 16.12.2019
- started implemented yappi profiling thanks to:
  https://github.com/pantsbuild/pants/wiki/Debugging-Tips:-multi-threaded-profiling-with-yappi

### 13.12.2019
- fixed personnel extraction for endless forms most beautiful
- artist is split to letters sometimes when writing tags, probablly happening
  when gui send data back to parser. Should be fixed now.
- Simplified handling of classes in utilities.sync module. Newly created
  instances of control classes are automatically put in queue
- simplified SharedVars and renames to GuiLogger
- significantlly reduced threadpool progressbar check rate

### 2.12.2019
- minor fixes
- moved most of the code from SharedVars class to Action and Progress,
  respective queues are now encapsulated by their controling classs
- perspectively move all code to these classes and destroy SharedVars class

### 29.11.2019
- some minor typing fixes
- cleaned up and rewritten freezing script, added parallel build for CLI and
  GUI and zip packaging for release

### 17.11.2019
- fully rewritten info tracks method, extraction code is cleaner and should be
  more robust

### 13.11.2019
- fix lyricfinding for songs with numbers like:
  Iced Earth: Clear The Way (December 13th, 1862)
- fixed file assingnmet bug when track name was same as album name, than mapping
  was ambigous
- fixed bug NoCoverArt exception was not being caught because it was in
  separate thread, moved decorator to inner function
- fixed bug: manual google api search key was running even if NO was selected

### 8.11.2019
- return back to lazy loaded tag handlers, exceptions were caused by
  inactive virtual environment
- fixed extract Feat. not only feat.
- added own response queue for Control action, otherwise when action and
  control message woulb be displayed at the same time answer order
  could not be guaranted
- new, more robust method for file-track matching

### 7.11.2019
- implemented saving tags only to selected files
- fixed bug when info of non-existent file is loast in passing info to GUI
  and back
- fixed: sometimes darklyrics has empty lyris field but everything passes
  only the lyrics is an empty string, in this case throw NoLyrics exception
- fixed lyrics reading bug for mp3 files, literal_eval is probably not needed
- fixed comma appearing before artist name in reading and also writing

### 6.11.2019
- fixed comment tag writing and track number writing in m4a
- fixed lyrics not loading to GUI
- fixed cover art save to file
- fixed messed up lyrics order

### 2.11.2019
- delete do not bother setting when api key or nltk data are manualy
  downloaded

### 26.10.2019
- new preload implementation is finished and tested, fixed few bugs

### 25.10.2019
- preload has been completelly reworked, better encapsulation, multiple
  preload instances, can be paused, instances are separated in threads
- threads doesn't seem to want to wake up from pause??

### 24.10.2019 - 0.5a0
- some changes to lyricsfinder to speed things up
- made test music files a lot smaller, for git push and pull to be faster
- last opened file is now not included in dist wheel

### 21.10.2019
- finnished and tested new implementation of parser - GUI comunication, it is
  a lot cleaner and less error prone
- SharedVars class ha been simplified a lot
- improved type checking in library.lyrics module
- better progress reporting in ThreadPool with less overhead and potential to
  collect messages from running thread.
- fixed (with a workaround) a strange problem when low level lazy-loaded tag
  handlers would refuse to load

### 20.10.2019
- comunication between gui and parser has been completely reworked with use of
  queue.Queue. It is musch more elegant and effective. An action object is
  passed byck anf forth by gui and parser
- reworked exception classes loading
- TypedDict implementation in google images download and lyrics for correct
  type checking

### 19.10.2019
- finished porting to pathlib
- fixed api key and nltk download halting gui
- multiple docstings inprovements
- simplified low level tag handling, used more of mutagen utilitie functions
- added async threadpool generator
- fixed multiple small bugs
- tags for each song are read in separate thread
- improvements to lock in SharedVars
- fixed parser reinit, moved to separate method
- tag writing tested, should be more reliable
- fixed some typing errors
- moved api key getter and nltk downloader to separate files

### 18.10.2019
- fixed lyricsfinding in frozen app, had to move away from lyricsfinder nice
  automatic imports
- moved nlth data download to app from setup.py
- implemented one universal settings dict class which takes care of saving
  and reading configuration
- classes for getting google API key and nltk data are now in separate file:
  getters under utilities
- started pathlib implementation, this wil cause maaaaany bugs

### 17.10.2019 - 0.4a0
- selenium dependency was caused by high download limit for
  google_images_download, limit is now set to 100
- fixed premature preload start
- experiment with UPX
- cleanup in parser.in_out
- some dlls must be excluded from UPX compression otherwise they are messed up
  and the executable is not working
- we got ~37% reduction in size of GUI app and 25% for CLI app
- new docs build test

### 16.10.2019 - 0.3a5
- fixed some gui scaling problems
- parser get methods now return so they can be used directly
- fixed marking of private methods in parser
- added GUI progressbar
- implemeted theadpool progressbar
- added selenium dependency for google_images_download
- added pypiwin32 dependency for building frozen app

### 15.10.2019 - 0.3a4
- completelly reworked logging
- finally readthedocs build is passing at long last, had to install with pip
- publish to PyPi

### 14.10.2019 - 0.3a2
- update readme and docs before PyPi publish.
- corrected version name
- fixed manifest including google API key
- published to test PyPi, all seems in order
- fixed wrong spelling of appdirs dependenxy in reuirements
- relax Pillow to requirement to >=6.1.0

### 12.10.2019
- we have automatic nktk data download in setup.py
- we have semi-auto google API key getting, user still has to do all the steps
  in browser
- got rid of package_setup script, replace it with setup.py develop
  installation
- we can now detect platform specific data directories with appdir and place
  data there
- implemented warnings for Mp3tag for non-win platformas and non default path
- if Mpštag is not found dialog is displayed for user to point to executable
- ignore some pydocstyle errors because we use numpy docstrings
- debugging mode in gui and debug logs are shown only if --debug command line
  swith is set

### 11.10.2019 - 0.2a0
- do not generate python files from ui files instead use uic to load them directly
- optimizations to parser and GUI comunication
- all docstrings are written
- docs are finished
- bumping version to 0.2.0-alpha
- build is broken again at readthedocs despite PySide2 installing!!

### 10.10.2019
- now we have cover art search that is resumable, the load more button
  is working, use of queue from standard library for simplification of
  comunication with the background downloading thread. Queue is also thread
  safe
- most of the gui_lib is now documented only data_model and main_window remain
- remamed some methods from: \_\_method\_\_ to _method

### 9.10.2019 - 0.1a0
- added license, mainfest and setup.py file
- publish to read the docs, build is passing now after somme debugging
- written setup.py file, instalation is working
- fixer problem with no Qt backend found in the installed package, although
  for readthe docs we had to implement a workarounf by installing PySide2
  it was reporting error No module named 'PyQt5.sip' although it can be
  clearlly seen it was being installed
- vesion was changed ot 0.1.0-alpha, this is a better description
- started writing gui dostrings

### 8.10.2019
- finished parser docsrings, now only gui remains
- found bug, pickle is evidently unable to unpickle complex pages
- revriten a lot of parser methods, more use of BeautifulSoup and re,
  less unreadable and unreliable string searching, should result in better
  extractions, but will be probably still full of bugs.
- new methods should be a lot easier to maintain
- added ne parser constants
- added new types of exceptions, all extraction methods in parser now raise
  if the extraction has gone wrong somehow
- warnnings wrapper now catches only wiki_music defined exceptions

### 7.10.2019
- continue to write parser docstrings
- writen new tags test
- added some regex expresions to track extraction for shorter and cleaner code
- we have docstrings for almost whole lib only gui lib remains
- rewrote some getter methods in parser to be more robust and have less code

### 6.10.2019
- continue to write docstrings, so far we have documented constants,
  external libraries, utilities, part of library and antry point scripts
- some minor improvements to type anotations, use of TYPE_CHECKING constant
- ThreadPool in parser_utils is now smart and doesnt spawn new threads
  if it gets only one set of arguments
- got rid of only_lyrics: bool argument in lyrics saving. It is useless because
  of the code is selectively writing only the tags that have changed

### 5.10.2019
- found the bug that was preventing frozen gui code from running. There was
  gui.py file and gui folder with other submodules which was evidentlly
  confusing python. Renamed the gui folder to gui_lib and gui.py to app_gui.py
- added version file
- started building docs with sphinx and readthedocs theme
- docs are looking good, so far the utilities and external_lbraries are documented

### 4.10.2019
- trying to freeze gui app, no success some wild bug is on loose

### 3.10.2019
- now we are using a separate virtual environment for building freezed app
  size is reduced to ~ 100MB which is still a lot but accetable
- console app is now working ok
- further reduction of frozen app size by use of vanilla numpy which is not
  built against OPENBLAS or Intel MKL. Pre-built wheels are available at:
  https://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy The finall size is now ~75MB
- updated package dependencies
- fixed few bugs and enhanced lyricsfinding
- new hook for wiki_music hidden imports
- cleanup to install script
- thorough cleanup in imports, all lazy modules are now marked in root init file,
  we have a lot cleaner and readable imports code

### 2.10.2019
- tried to get rid of lazy_import package, replaced wth custom LazyLoad class
  stolen from tensorflow https://github.com/tensorflow/tensorflow/blob/master/tensorflow/python/util/lazy_loader.py
  as a result got weird interactions with logger and freezing
- now we are monkey patching necessary pyinstaller hooks
- new custom hook for nltk to include only data we need, size reduced by ~0.5GB
- final freezed app is still too big, because of conda numpy being built against
  mkl library. Solution is to create virtual env and install pip version
  of numpy. refer to:
  https://github.com/pyinstaller/pyinstaller/issues/2270
  https://stackoverflow.com/questions/43886822/pyinstaller-with-pandas-creates-over-500-mb-exe/48846546#48846546
  https://github.com/conda-forge/numpy-feedstock/issues/84
- having a virtual environment could potentialy solve problem with too many
  unecessary includes in freezed app
- nltk.ne_chunk() numpy dependency cannot be avoided
- alternatives are spaCy which has even more dependencies, including mkl and
  Stanford NLP parser, but that requires java virtual machine running. So
  basically both are worth shit, for our purposes.
 
### 1.10.2019
- setting up pyinstaller to work with console version - success
- setup is also delicate job, but maybe a little less buggy than cx_Freeze
- got rid of joblib dependency, substituted with custom ThreadPool
- implemented custom hook for lazy_import
- implemented custom runtime hook for nltk
- pyinstaller setup is now contained in separate dir - wiki_music/setup

### 30.9.2019
- been plying around with cx_Freeze, it's useless, cant get it to work
  after hours of experiments
- abandon cx_Freeze, substitute with pyinstaller

### 27.5.2019
- typechecking is now in most modules
- integrated application into parser
- all files now support typing, although there are some workarounds, mainly
  for properties and lazy imports
- wrote first test

### 26.5.2019
- introduced typechecking to parser and use of mypy linting
- split parser to one more file that contais class which takes
  care of input and output

### 23.9.2019
- fixed some image editing bugs
- unable to do something with crop selection not respecting image borders,
  logic is too complex CPU rockets to 30%, aaaah. Need to find some way.
- I got saved by StackOverflow https://stackoverflow.com/questions/58053735/get-real-size-of-qpixmap-in-qlabel/58063020#58063020
- wrote some simple tests for GUI
- fixed cover art compression bug when gui was ignoring resize on compression
- now we are writing only tags that have changed
- constistence of TAGS in constants is asserted with those in init
  methods in tag handlers
- fixed minor bugs in tag writing
- after tests are written we will advance to 1.0.0 version

### 22.9.2019
- got rid of tkinter gui, the parser API has changed so much
  that it does not make sense to keep it
- cleanup in problems, some were solved, others I didn't even remember what
  they were trying to say
- simplification to package imports
- moved constants to separate directory
- got rid of pytaglib dependency
- simplified tag writing hihg level functions and low level classes
- implemented coverart writing
- written some tags tests
- tag writing is now parallel with joblib

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
- fixed bug, GUI was displaying only the first selected cover art

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
- minor tweak to tags_io.py .mp3 files apparently also have lyrics under LYRICS tag same as .m4a

### 24.8.2018
- some further code reorganize
- added logger to tags_io
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
- more work done in lyrics.py a tags_io.py

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
