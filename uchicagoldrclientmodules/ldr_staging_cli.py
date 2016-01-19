#!/usr/bin/python3

# Default package imports begin #
from argparse import ArgumentParser
from os import _exit
from os.path import split, exists, isabs
# Default package imports end #

# Third party package imports begin #
# Third party package imports end #

# Local package imports begin #
from uchicagoldrlogging.loggers import MasterLogger
from uchicagoldrlogging.handlers import DefaultTermHandler, DebugTermHandler, \
    DefaultFileHandler, DebugFileHandler, DefaultTermHandlerAtLevel,\
    DefaultFileHandlerAtLevel
from uchicagoldrlogging.filters import UserAndIPFilter
from uchicagoldrconfig import LDRConfiguration

from uchicagoldr.batch import StagingDirectory
# Local package imports end #

# Header info begins #
__author__ = "Brian Balsamo"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "0.0.1"
__maintainer__ = "Brian Balsamo"
__email__ = "balsamo@uchicago.edu"
__status__ = "Development"
# Header info ends #

"""
A command line interface for building, populating, and validating
staging structures for the UChicago LDR.
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
    logger.info("BEGINS")
    # Application specific log instantation ends #

    # Parser instantiation begins #
    parser = ArgumentParser(description="[A brief description of the utility]",
                            epilog="Copyright University of Chicago; " +
                            "written by "+__author__ +
                            " "+__email__)

    parser.add_argument(
                        "-v",
                        help="See the version of this program",
                        action="version",
                        version=__version__
    )
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
                        'ark'
    )
    parser.add_argument(
                        'ead'
    )
    parser.add_argument(
                        'accno'
    )
    parser.add_argument(
                        '-c', '--create',
                        help="create the specified staging structure on disk."
    )
    parser.add_argument(
                        '-i', '--ingest',
                        nargs='*',
                        help="Specify paths to ingest into the staging " +
                             "directory."
    )
    parser.add_argument(
                        '-r', '--root',
                        help="Specify a root path for the staging structure " +
                             "if not the default."
    )
    parser.add_argument(
                        '-v', '--validate',
                        action='store_true',
                        help="Validate the staging directory"
    )
    parser.add_argument(
                        '--alt-config-dir',
                        help='specify an alternate configuration location'
    )
    parser.add_argument(
                        '--rehash',
                        action='store_true',
                        default=False,
                        help="Disregard existing hashes when possible."
    )
    parser.add_argument(
                        '-p', '--prefix'
    )
    parser.add_argument(
                        '--regex'
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
    if args.alt_config:
        if not isabs(args.alt_config_dir):
            logger.critical("Alternate configuration locations must be " +
                            "specified via absolute paths!")
            return(1)
        if not exists(args.alt_config_dir):
            logger.critical("The alternate configuration specified " +
                            "does not exist!")
            return(1)

    if args.containing_folder and args.prefix:
        logger.critical("Can not specify a prefix and a containing folder.")
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

    # Configuration parsing and population begins
    if args.alt_config_dir:
        config = LDRConfiguration(args.alt_config_dir).read_config_data()
    else:
        config = LDRConfiguration().read_config_data()
    # Configuration parsing ends

    try:
        # Begin module code #
        if args.root:
            root = args.root
        else:
            root = config['staging']['staging_root_path']
        ark, ead, accno = args.ark, args.ead, args.accno
        staging_dir = StagingDirectory(root, ark, ead, accno)
        staging_dir.populate()
        if args.containing_folder:
            for ingest_dir in args.ingest:
                if args.regex:
                    staging_dir.ingest(ingest_dir,
                                       containing_folder=args.containing_folder,
                                       rehash=args.rehash,
                                       pattern=args.regex)
                else:
                    staging_dir.ingest(ingest_dir,
                                       containing_folder=args.containing_folder,
                                       rehash=args.rehash)

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
