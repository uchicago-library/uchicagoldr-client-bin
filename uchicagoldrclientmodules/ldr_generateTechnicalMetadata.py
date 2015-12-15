
__author__ = "Brian Balsamo"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "0.0.1"
__maintainer__ = "Brian Balsamo"
__email__ = "balsamo@uchicago.edu"
__status__ = "Development"

"""
This module is meant to take a batch of files (probably an accession in place) and generate the technical metadata for it.
"""

from argparse import ArgumentParser
from logging import DEBUG, FileHandler, Formatter, getLogger, \
    INFO, StreamHandler
from os import _exit
from os.path import join, exists, abspath
from subprocess import TimeoutExpired

from uchicagoldr.batch import Batch
from uchicagoldr.item import Item
from uchicagoldr.bash_cmd import BashCommand

def main():
    # start of parser boilerplate
    parser = ArgumentParser(description="This module is meant to take a batch of files (probably an accession in place) and generate the technical metadata for it.",
                            epilog="Copyright University of Chicago; " + \
                            "written by "+__author__ + \
                            " "+__email__)

    parser.add_argument("-v", help="See the version of this program",
                        action="version", version=__version__)
    # let the user decide the verbosity level of logging statements
    # -b sets it to INFO so warnings, errors and generic informative statements
    # will be logged
    parser.add_argument( \
                         '-b','-verbose',help="set verbosity for logging to stdout",
                         action='store_const',dest='log_level',
                         const=INFO,default='INFO' \
    )
    # -d is debugging so anything you want to use a debugger gets logged if you
    # use this level
    parser.add_argument( \
                         '-d','--debugging',help="set debugging logging",
                         action='store_const',dest='log_level',
                         const=DEBUG,default='INFO' \
    )
    # optionally save the log to a file. set a location or use the default constant
    parser.add_argument( \
                         '-l','--log_loc',help="save logging to a file",
                         dest="log_loc",
                         \
    )
    parser.add_argument( \
                         '-t','--timeout',help="set a timeout in seconds for any single bash command",
                         dest='timeout',default=3600,type=int \
    )
    parser.add_argument("item", help="Enter a noid for an accession or a " + \
                        "directory path that you need to validate against" + \
                        " a type of controlled collection"
    )
    parser.add_argument("root",help="Enter the root of the directory path",
                        action="store"
    )
    args = parser.parse_args()
    log_format = Formatter( \
                            "[%(levelname)s] %(asctime)s  " + \
                            "= %(message)s",
                            datefmt="%Y-%m-%dT%H:%M:%S" \
    )
    global logger
    logger = getLogger( \
                        "lib.uchicago.repository.logger" \
    )
    logger.setLevel(DEBUG)
    ch = StreamHandler()
    ch.setFormatter(log_format)
    ch.setLevel(args.log_level)
    logger.addHandler(ch)
    if args.log_loc:
        fh = FileHandler(args.log_loc)
        fh.setFormatter(log_format)
        logger.addHandler(fh)
    try:
        fitscommand="fits"
        md5command="md5"
        shacommand="sha256"

        b = Batch(abspath(args.root), abspath(args.item))
        for item in b.find_items(from_directory=True):
            if ".fits.xml" in item.find_file_name() or ".stif.txt" in item.find_file_name():
                continue
            item.find_technical_metadata()
            if item.has_technical_md:
                logger.info(item.get_file_path()+" already has technical metadata. Continuing.")
                continue
            else:
                logger.info("Attempting technical metadata generation for: "+item.get_file_path())
                fitsArgs=[fitscommand,'-i',item.get_file_path(),'-o',item.get_file_path()+'.fits.xml']
                fitsCommand=BashCommand(fitsArgs)
                fitsCommand.set_timeout(args.timeout)
                try:
                    logger.info("Attempting FITS generation for: "+item.get_file_path())
                    result=fitsCommand.run_command()
                    if isinstance(result[1],Exception):
                        raise result[1]
                    assert(exists(item.get_file_path()+'.fits.xml'))
                    logger.info("FITS generated for: "+item.get_file_path()) 
                except TimeoutExpired:
                    logger.warn("FITS generation timed out")
                    logger.info("Attempting STIF generation")
                    statArgs=['stat',item.get_file_path()]
                    statCommand=BashCommand(statArgs)
                    statCommand.set_timeout(args.timeout)

                    mimeArgs=['file','-i',item.get_file_path()]
                    mimeCommand=BashCommand(mimeArgs)
                    mimeCommand.set_timeout(args.timeout)

                    fileArgs=['file',item.get_file_path()]
                    fileCommand=BashCommand(fileArgs)
                    fileCommand.set_timeout(args.timeout)
                    
                    assert(statCommand.run_command()[0])
                    assert(mimeCommand.run_command()[0])
                    assert(fileCommand.run_command()[0])

                    md5hash=item.find_md5_hash()
                    shahash=item.find_sha256_hash

                    with open(item.get_file_path()+'.stif.txt','w') as f:
                        f.write(statCommand.get_data()[1].stdout.decode(encoding='UTF-8')+ \
                                mimeCommand.get_data()[1].stdout.decode(encoding='UTF-8')+ \
                                fileCommand.get_data()[1].stdout.decode(encoding='UTF-8')+ \
                                "md5: " + item.find_md5_hash() + '\n'+ \
                                "sha256: " + item.find_sha256_hash() \
                               )
                    assert(exists(item.get_file_path()+'.stif.txt'))
                    logger.info("STIF generated for: "+item.get_file_path())
                item.find_technical_metadata()
                assert(item.has_technical_md)
                logger.info("Technical metadata generation complete for: "+item.get_file_path())
        return 0
    except KeyboardInterrupt:
        logger.error("Program aborted manually")
        return 131

if __name__ == "__main__":
    _exit(main())
