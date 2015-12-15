#!/usr/bin/python3

# Default package imports begin #
from argparse import ArgumentParser
from os import _exit
from os.path import split, exists, join
# Default package imports end #

# Third party package imports begin #
# Third party package imports end #

# Local package imports begin #
from uchicagoldrLogging.loggers import MasterLogger
from uchicagoldrLogging.handlers import DefaultTermHandler, DebugTermHandler, \
    DefaultFileHandler, DebugFileHandler, DefaultTermHandlerAtLevel,\
    DefaultFileHandlerAtLevel
from uchicagoldrLogging.filters import UserAndIPFilter

from uchicagoldrStaging.validation.validateBase import ValidateBase
from uchicagoldrStaging.validation.validateOrganization import \
    ValidateOrganization
# Local package imports end #

# Header info begins #
__author__ = "Brian Balsamo"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "0.0.2"
__maintainer__ = "Brian Balsamo"
__email__ = "balsamo@uchicago.edu"
__status__ = "Development"
# Header info ends #

"""
This module validates a staging root structure.
"""

# Functions begin #
# Functions end #


def main():
    # Master log instantiation begins #
    global masterLog
    masterLog = MasterLogger()
    # Master log instantiation ends #

    # Application specific log instantation begins #
    global logger
    logger = masterLog.getChild(__name__)
    f = UserAndIPFilter()
    termHandler = DefaultTermHandler()
    logger.addHandler(termHandler)
    logger.addFilter(f)
    # Application specific log instantation ends #

    # Parser instantiation begins #
    parser = ArgumentParser(description="[A brief description of the utility]",
                            epilog="Copyright University of Chicago; " +
                            "written by "+__author__ +
                            " "+__email__)

    parser.add_argument("-v", help="See the version of this program",
                        action="version", version=__version__)
    # let the user decide the verbosity level of logging statements
    # -b sets it to INFO so warnings, errors and generic informative statements
    # will be logged
    parser.add_argument(
                        '-b', '--verbosity',
                        help="set logging verbosity " +
                        "(DEBUG,INFO,WARN,ERROR,CRITICAL)",
                        nargs='?',
                        const='INFO'
    )
    # -d is debugging so anything you want to use a debugger gets logged if you
    # use this level
    parser.add_argument(
                        '-d', '--debugging',
                        help="set debugging logging",
                        action='store_true'
    )
    # optionally save the log to a file.
    # Set a location or use the default constant
    parser.add_argument(
                        '-l', '--log_loc',
                        help="save logging to a file",
                        dest="log_loc",

    )
    parser.add_argument(
                        "item",
                        help="Enter a noid for an accession or a " +
                        "directory path that you need to validate against" +
                        " a type of controlled collection"
    )
    parser.add_argument(
                        "root",
                        help="Enter the root of the directory path",
                        action="store"
    )
    try:
        args = parser.parse_args()
    except SystemExit:
        logger.critical("ENDS: Command line argument parsing failed.")
        exit(1)

    # Begin argument post processing, if required #
    if args.verbosity and args.verbosity not in ['DEBUG', 'INFO',
                                                 'WARN', 'ERROR', 'CRITICAL']:
        logger.critical("You did not pass a valid argument to the verbosity \
                        flag! Valid arguments include: \
                        'DEBUG','INFO','WARN','ERROR', and 'CRITICAL'")
        return(1)
    if args.log_loc:
        if not exists(split(args.log_loc)[0]):
            logger.critical("The specified log location does not exist!")
            return(1)
    # End argument post processing #

    # Begin user specified log instantiation, if required #
    if args.log_loc:
        fileHandler = DefaultFileHandler(args.log_loc)
        logger.addHandler(fileHandler)

    if args.verbosity:
        logger.removeHandler(termHandler)
        termHandler = DefaultTermHandlerAtLevel(args.verbosity)
        logger.addHandler(termHandler)
        if args.log_loc:
            logger.removeHandler(fileHandler)
            fileHandler = DefaultFileHandlerAtLevel(args.log_loc,
                                                    args.verbosity)
            logger.addHandler(fileHandler)

    if args.debugging:
        logger.removeHandler(termHandler)
        termHandler = DebugTermHandler()
        logger.addHandler(termHandler)
        if args.log_loc:
            logger.removeHandler(fileHandler)
            fileHandler = DebugFileHandler(args.log_loc)
            logger.addHandler(fileHandler)
    # End user specified log instantiation #
    try:
        logger.info("BEGINS")
        # Begin module code #
        logger.info("Validating Base Structure.")
        validation = ValidateBase(args.item)
        if validation[0] != True:
            logger.critical("Your staging base has not validated!")
            logger.critical(validation)
            exit(1)

        dataPath=join(*validation[1:], 'data')
        adminPath=join(*validation[1:], 'admin')

        logger.info("Checking data directory.")
        dataValid = ValidateOrganization(dataPath)
        if dataValid[0] != True:
            logger.critical("Your data directory is not well formed!")
            logger.critical(dataValid)
            exit(1)
        for x in dataValid[1]['notDirs']:
            logger.warn("The following appears in the data dir " +
                        "but is not a directory: "+x)

        logger.info("Checking admin directory.")
        adminValid = ValidateOrganization(adminPath,
                                          reqTopFiles=['record.json',
                                                       'fileConversions.txt'],
                                          reqDirContents=[
                                              'fixityFromOrigin.txt',
                                              'fixityOnDisk.txt',
                                              'log.txt',
                                              'rsyncFromOrigin.txt']
                                          )
        if adminValid[0] != True:
            logger.critical("ENDS: Your admin directory is not well formed!")
            logger.warn(adminValid)
            exit(1)
        if dataValid[1]['dirs'] != adminValid[1]['dirs']:
            for x in dataValid[1]['dirs']:
                if x not in adminValid[1]['dirs']:
                    logger.warn("Directory appears in data but not admin: "+x)
            for x in adminValid[1]['dirs']:
                if x not in dataValid[1]['dirs']:
                    logger.warn("Directory appears in admin but not data: "+x)
        # End module code #
        logger.info("ENDS: COMPLETE")
        return 0
    except KeyboardInterrupt:
        logger.error("ENDS: Program aborted manually")
        return 131
    except Exception as e:
        logger.critical("ENDS: Exception ("+str(e)+")")
        return 1
if __name__ == "__main__":
    _exit(main())
