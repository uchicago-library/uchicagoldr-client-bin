__author__ = "Tyler Danstrom"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "1.0.0"
__maintainer__ = "Tyler Danstrom"
__email__ = "tdanstrom@uchicago.edu"
__status__ = "Production"
__description__ = "This program takes a directory of files and ingests them into the ldr"

from sys import argv, path

path.insert(0, "/home/tdanstrom/src/apps/ldr_lib/lib")

from argparse import Action, ArgumentParser
from datetime import datetime, timedelta
from grp import getgrgid
from pwd import getpwuid
from hashlib import md5, sha256
from logging import DEBUG, FileHandler, Formatter, getLogger, \
    INFO, StreamHandler
from os import _exit, stat
from sqlalchemy import Table
from sys import stdout

from uchicagoldr.batch import Batch
from uchicagoldr.database import Database

def main():
    parser = ArgumentParser(description="{description}". \
                            format(description = __description__),
                            epilog="{copyright}; ". \
                            format(copyright=__copyright__) + \
                            "written by {name} ".format(name=__author__) + \
                            " <{email}> ".format(email=__email__) + \
                            "University of Chicago")
    parser.add_argument("-v", help="See the version of this program",
                        action="version", version=__version__)
    parser.add_argument( \
                         '-b','-verbose',help="set verbose logging",
                         action='store_const',dest='log_level',
                         const=INFO \
    )
    parser.add_argument( \
                         '-d','--debugging',help="set debugging logging",
                         action='store_const',dest='log_level',
                         const=DEBUG \
    )
    parser.add_argument( \
                         '-l','--log_loc',help="save logging to a file",
                         action="store_const",dest="log_loc",
                         const='./{progname}.log'. \
                         format(progname=argv[0]) \
    )
    parser.add_argument("location_root",help="Enter the root " + \
                        "of the directory path",
                        action="store")
    parser.add_argument("directory_path", 
                           help="Enter a directory that you need to work on ",
                           action='store')
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
    ch = StreamHandler()
    ch.setFormatter(log_format)
    try:
        logger.setLevel(args.log_level)
    except TypeError:
        logger.setLevel(INFO)
    if args.log_loc:
        fh = FileHandler(args.log_loc)
        fh.setFormatter(log_format)
        logger.addHandler(fh)
    logger.addHandler(ch)
    try:
        b = Batch(args.location_root, directory = args.directory_path)
        generator_object = b.find_items(from_directory=True)
        logger.debug(generator_object)
        b.set_items(generator_object)
        stdout.write("begin transaction;\n")
        for a_file in b.get_items():
            if a_file.test_readability():
                
                file_hash = a_file.find_hash_of_file(sha256)
                mime = a_file.find_file_mime_type()
                size = a_file.find_file_size()
                accession = a_file.find_file_accession()
                a_file.set_file_mime_type(mime)
                a_file.set_file_size(size)
                a_file.set_hash(file_hash)
                a_file.set_accession(accession)
                out_string = "insert into file (filepath,accession," + \
                             "mimetype,size,checksum) values (" + \
                             "\"{path}\",\"{accession}\",\"{mimetype}\"". \
                             format(path = a_file.filepath,
                                    accession = a_file.get_accession(),
                                    mimetype = a_file.get_file_mime_type()) + \
                                    ",{filesize},\"{filehash}\");\n". \
                                    format(filesize = a_file.get_file_size(),
                                           filehash = a_file.get_hash())
                stdout.write(out_string)
            else:
                logger.error("{path} could not be read". \
                             format(path=a_file.filepath))
        stdout.write("commit;\n")
        return 0 
    except KeyboardInterrupt:
        logger.warn("Program aborted manually")
        return 131

if __name__ == "__main__":
    _exit(main())
