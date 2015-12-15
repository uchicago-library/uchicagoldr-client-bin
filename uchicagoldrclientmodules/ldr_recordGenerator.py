#!/usr/bin/python3

# Default package imports begin #
from argparse import ArgumentParser
from os import _exit
from os.path import split, exists, join, abspath, expandvars, isdir
import json
# Default package imports end #

# Third party package imports begin #
# Third party package imports end #

# Local package imports begin #
from uchicagoldrLogging.loggers import MasterLogger
from uchicagoldrLogging.handlers import DefaultTermHandler, DebugTermHandler, \
    DefaultFileHandler, DebugFileHandler, DefaultTermHandlerAtLevel,\
    DefaultFileHandlerAtLevel
from uchicagoldrLogging.filters import UserAndIPFilter

from uchicagoldrRecords.record.recordFieldsBooleans import RecordFieldsBooleans
from uchicagoldrRecords.record.recordFieldsValidation import \
    RecordFieldsValidation
from uchicagoldrRecords.record.recordFieldsDefaults import RecordFieldsDefaults
from uchicagoldrRecords.fields.ldrFields import LDRFields
from uchicagoldrRecords.readers.digitalAcquisitionRead import \
    ReadAcquisitionRecord
from uchicagoldrRecords.readers.dummyReader import DummyReader
from uchicagoldrRecords.mappers.digitalAcquisitionMap import \
    AcquisitionRecordMapping
from uchicagoldrRecords.mappers.dummyMapper import DummyMapper
from uchicagoldrRecords.record.recordWriting import instantiateRecord, \
    meldRecord, manualInput, booleanLoop, validate, generateFileEntries, \
    computeTotalFileSizeFromRecord, writeNoClobber, createSubRecord

from uchicagoldrStaging.validation.validateBase import ValidateBase
# Local package imports end #

# Header info begins #
__author__ = "Brian Balsamo"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "0.0.2"
__maintainer__ = "Brian Balsamo"
__email__ = "balsamo@uchicago.edu"
__status__ = "Prototype"
# Header info ends #

"""
A module meant to ingest a digital acquisitions form and a staged directory
and produce a record designed for use by Special Collections, the LDR,
and the DAS.
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
    parser.add_argument(
                        "--acquisition-record", '-a',
                        help="Enter a noid for an accession or a " +
                        "directory path that you need to validate against" +
                        " a type of controlled collection",
                        action='append'
                        )
    parser.add_argument(
                        "--out-file", '-o',
                        help="The location where the full record should be " +
                        " written to disk.",
                        required=True,
                        action="append"
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
        # Begin module code #
        # Keep in mind that population order here matters a lot in terms of
        # how much input the user will be asked for.

        # Instantiate a blank record with all our fields set to a blank string,
        # for bounding loops and no funny business when we try and print it.
        logger.info("Instantiating Record")
        record = instantiateRecord()

        # Map our defaults right into the record.
        logger.info("Mapping defaults")
        meldRecord(record, RecordFieldsDefaults(), DummyReader, DummyMapper)

        # Read all the digital acquisition forms,
        # populate the record with their info, address conflicts
        logger.info("Reading and mapping digital acquisition records.")
        for acqRecord in args.acquisition_record:
            meldRecord(record, acqRecord, ReadAcquisitionRecord,
                       AcquisitionRecordMapping)

        # Manual input loop
        logger.info("Beginning Manual Input Loop")
        manualInput(record)

        # Run some automated processing over the record to clean up
        # certain values if required.
        logger.info("Beginning attempts at automated boolean interpretation")
        record = booleanLoop(record, RecordFieldsBooleans())
        # Validate the record fields against their stored regexes
        logger.info("Validating...")
        record = validate(record, RecordFieldsValidation())

        # File level information population
        logger.info("Generating file info...")
        record['fileInfo'] = generateFileEntries(args.root, args.item)

        logger.info("Computing total size")
        record['totalDigitalSize'] = computeTotalFileSizeFromRecord(record)

        # Write two records, one which contains the entirety of the record,
        # including potential internal information, to an internal source,
        # and another which contains information pertinent to the LDR into
        # the admin directory
        logger.info("Writing whole record to out files: " +
                    str(args.out_file))
        for filepath in args.out_file:
            assert(writeNoClobber(record, filepath))

        logger.info("Creating subrecord")
        pubRecord = createSubRecord(record, LDRFields())

        logger.info("Attempting to write LDR subrecord into staging structure.")
        ldrRecordPath = None
        validation = ValidateBase(args.item)
        if validation[0] == True:
            ldrRecordPath = join(*validation[1:], "admin", 'record.json')
        else:
            logger.warn("You don't seem to have pointed the script at a " +
                        "fully qualified staging structure. Please manually " +
                        "specify a location to save the LDR record to, " +
                        "otherwise leave this line blank to save only " +
                        "the full record."
                        )
            while ldrRecordPath == None:
                ldrRecordPath = input("LDR Record Path: ")
                if ldrRecordPath == "":
                    break
                if len(ldrRecordPath) > 0:
                    ldrRecordPath = abspath(expandvars(ldrRecordPath))
                    print("Attempted abspath " + ldrRecordPath)
                if not isdir(ldrRecordPath):
                    ldrRecordPath = None

        if ldrRecordPath != "":
            writeNoClobber(pubRecord, ldrRecordPath)
            logger.info("LDR Record written")
        else:
            logger.info("LDR Record generation skipped.")

        logger.info(json.dumps(record, indent=4, sort_keys=True))
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
