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

from uchicagoldr.batch import Batch

from uchicagoldrStaging.validation.validateBase import ValidateBase
from uchicagoldrStaging.population.readExistingFixityLog import \
    ReadExistingFixityLog
from uchicagoldrStaging.population.writeFixityLog import WriteFixityLog
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
This module generates fixity information for files being moved into staging.
It generates fixity information as the files appear in library disk-space.
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
                        "dest_root",
                        help="Enter the destination root path",
                        action='store'
    )
    parser.add_argument(
                        "containing_folder",
                        help="The name of the containing folder on disk " +
                        "(prefix+number)",
                        action='store'
    )
    parser.add_argument(
                        "--rehash",
                        help="Disregard any existing previously generated " +
                        "hashes, recreate them on this run",
                        action="store_true"
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
        validation = ValidateBase(args.dest_root)
        if validation[0] == True:
            stageRoot = join(*validation[1:])
        else:
            logger.critical("ENDS: Your staging root appears to not be valid!")
            exit(1)
        destinationAdminRoot = join(stageRoot, 'admin/')
        destinationDataRoot = join(stageRoot, 'data/')
        containing_folder = args.containing_folder
        destinationAdminFolder = join(destinationAdminRoot, containing_folder)
        destinationDataFolder = join(destinationDataRoot, containing_folder)

        stagingDebugLog = DebugFileHandler(
            join(destinationAdminFolder, 'log.txt')
        )
        logger.addHandler(stagingDebugLog)

        logger.debug("Creating batch from moved files.")
        movedFiles = Batch(destinationDataFolder,
                           directory=destinationDataFolder)

        logger.info("Hashing copied files.")
        existingHashes = None
        if args.rehash:
            logger.info(
                "Rehash argument passed. Not reading existing hashes."
            )
        if not args.rehash and exists(
                join(destinationAdminFolder, 'fixityOnDisk.txt')
        ):
            existingHashes = ReadExistingFixityLog(join(destinationAdminFolder,
                                                        'fixityOnDisk.txt')
                                                   )
        WriteFixityLog(
            join(destinationAdminFolder, 'fixityOnDisk.txt'),
            movedFiles, existingHashes=existingHashes
        )
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
