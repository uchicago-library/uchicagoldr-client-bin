#!/usr/bin/python3

# Default package imports begin #
from argparse import ArgumentParser
from os import _exit
from os.path import split, exists, join, isdir
# Default package imports end #

# Third party package imports begin #
# Third party package imports end #

# Local package imports begin #
from uchicagoldrLogging.loggers import MasterLogger
from uchicagoldrLogging.handlers import DefaultTermHandler, DebugTermHandler, \
    DefaultFileHandler, DebugFileHandler, DefaultTermHandlerAtLevel,\
    DefaultFileHandlerAtLevel
from uchicagoldrLogging.filters import UserAndIPFilter

from uchicagoldr.bash_cmd import BashCommand

from uchicagoldrStaging.validation.validateBase import ValidateBase
from uchicagoldrStaging.population.prefixToFolder import prefixToFolder
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
This module is meant to take a location on physical media (or all the contents)
and move it into disk space in the LDR staging area.
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
                        "item",
                        help="Enter a noid for an accession or a " +
                        "directory path that you need to validate against " +
                        "a type of controlled collection"
    )
    parser.add_argument(
                        "root",
                        help="Enter the root of the directory path",
                        action="store"
    )
    parser.add_argument(
                        "dest_root",
                        help="Enter the destination root path",
                        action='store'
    )
    parser.add_argument(
                        "prefix",
                        help="The prefix of the containing folder on disk",
                        action='store'
    )
    parser.add_argument(
                        "--rehash",
                        help="Disregard any existing previously generated " +
                        "hashes, recreate them on this run",
                        action="store_true"
    )
    parser.add_argument(
                        "--chain",
                        help="Write the prefix+num to stdout, for chaining " +
                        "this command into the others via some " +
                        "intermediate connection",
                        action="store_true"
    )
    parser.add_argument(
                        "--weird-root",
                        help="If for some reason you deliberately want to " +
                        "generate a strange item root structure which " +
                        "doesn't reflect rsyncs path interpretation " +
                        "behavior pass this option",
                        default=False,
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
    if args.item[-1] == "/" and args.item != args.root and not args.weird_root:
        logger.critical("Root appears to not conform to rsync path specs.")
        exit(1)
    # End user specified log instantiation #
    try:
        # Begin module code #
        validation = ValidateBase(args.dest_root)
        if validation[0] != True:
            logger.critical("Your staging root isn't valid!")
            exit(1)
        else:
            stageRoot = join(*validation[1:])

        destinationAdminRoot = join(stageRoot, 'admin/')
        destinationDataRoot = join(stageRoot, 'data/')
        prefix = args.prefix

        if not prefix[-1].isdigit():
            destFolder = prefixToFolder(destinationDataRoot, prefix)
            logger.info("Creating new data and admin directories for your " +
                        "prefix: "+destFolder)

            destinationAdminFolder = join(destinationAdminRoot, destFolder)
            destinationDataFolder = join(destinationDataRoot, destFolder)

            mkAdminDirArgs = ['mkdir', destinationAdminFolder]
            mkAdminDirComm = BashCommand(mkAdminDirArgs)
            assert(mkAdminDirComm.run_command()[0])
            logger.debug("mkAdminDir output begins")
            logger.debug(mkAdminDirComm.get_data()[1].args)
            logger.debug(mkAdminDirComm.get_data()[1].returncode)
            logger.debug(mkAdminDirComm.get_data()[1].stdout)
            logger.debug("mkAdminDir output ends")

            mkDataDirArgs = ['mkdir', destinationDataFolder]
            mkDataDirComm = BashCommand(mkDataDirArgs)
            assert(mkDataDirComm.run_command()[0])
            logger.debug("mkDataDir output begins")
            logger.debug(mkDataDirComm.get_data()[1].args)
            logger.debug(mkDataDirComm.get_data()[1].returncode)
            logger.debug(mkDataDirComm.get_data()[1].stdout)
            logger.debug("mkAdminDir output ends")

            assert(isdir(destinationAdminFolder))
            assert(isdir(destinationDataFolder))

        else:
            destFolder = args.prefix
            logger.info("Attempting to resume transfer into "+destFolder)

            destinationAdminFolder = join(destinationAdminRoot, destFolder)
            destinationDataFolder = join(destinationDataRoot, destFolder)

            for folder in [destinationAdminFolder, destinationDataFolder]:
                if not exists(folder):
                    logger.critical('It looks like you are trying to resume ' +
                                    'a transfer, but a corresponding data ' +
                                    'or admin folder is missing! Please ' +
                                    'remedy this and try again! Exiting (1)')
                    exit(1)

        stagingDebugLog = DebugFileHandler(
            join(destinationAdminFolder, 'log.txt')
        )
        logger.addHandler(stagingDebugLog)

        logger.info("Beginning rsync")
        rsyncArgs = ['rsync', '-avz', args.item, destinationDataFolder]
        rsyncCommand = BashCommand(rsyncArgs)
        assert(rsyncCommand.run_command()[0])
        with open(join(destinationAdminFolder,
                       'rsyncFromOrigin.txt'), 'a') as f:
            f.write(str(rsyncCommand.get_data()[1])+'\n')
        if rsyncCommand.get_data()[1].returncode != 0:
            logger.warn("Rsync exited with a non-zero return code: " +
                        str(rsyncCommand.get_data()[1].returncode))
        logger.debug("Rsync output begins")
        logger.debug(rsyncCommand.get_data()[1].args)
        logger.debug(rsyncCommand.get_data()[1].returncode)
        for line in rsyncCommand.get_data()[1].stdout.split('\n'):
            logger.debug(line)
        logger.debug("Rsync output ends")
        logger.info("Rsync complete.")

        if args.chain:
            try:
                folderName = split(destinationDataFolder)[1]
                with open('/tmp/folderName.txt', 'w') as f:
                    f.write(folderName)
            except Exception as e:
                logger.critical("ENDS: Failure in writing to tmp for chaining.")
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
