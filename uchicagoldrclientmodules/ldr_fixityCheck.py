
__author__ = "Tyler Danstrom"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "1.0.0"
__maintainer__ = "Tyler Danstrom"
__email__ = "tdanstrom@uchicago.edu"
__status__ = "Production"
__description__ = "This program takes a random selection of files from the ldr database and evaluates for file corruption."

from sys import argv, path

path.insert(0, "/home/tdanstrom/src/apps/ldr_lib/lib")

from argparse import Action, ArgumentParser
from configobj import ConfigObj
from datetime import datetime, timedelta
from grp import getgrgid
from pwd import getpwuid
from hashlib import md5, sha256
from logging import DEBUG, FileHandler, Formatter, getLogger, \
    INFO, StreamHandler
from os import _exit, stat
from os.path import exists
from sqlalchemy import func, or_, and_, Table

from batch import Batch
from database import Database

class dbBeforeTables(Action):
    def __call__(self,parser,namespace,value,option_string=None):

        if not getattr(namespace,'from_db'):
            raise ValueError("Not allowed to set tables without a table url")
        else:
            setattr(namespace,self.dest,value)    

            
            
def main():
    def find_group_name(filepath):
        unix_stat_of_file = stat(fp)
        grp_id_of_file = unix_stat_of_file.st_gid
        group_name = getattr(getgrgid(grp_id_of_file), 'gr_name', None)
        return group_name

    def find_user_name(filepath):
        uid_of_file = unix_stat_of_file.st_uid
        user_name = getpwuid(uid_of_file)
        return user_name
        
    parser = ArgumentParser(description="{description}". \
                            format(description=__description__),
                            epilog="Copyright University of Chicago; " + \
                            "written by {author} ". \
                            format(author = __author__) + \
                            " <{email}> University of Chicago". \
                            format(email = __email__))
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
    selection = parser.add_mutually_exclusive_group()

    selection.add_argument("--directory_path", 
                           help="Enter a directory that you need to work on ",
                           action='store')
    selection.add_argument("--from_db",help="Select to create a batch " + \
                           "from database",
                           action="store")
    parser.add_argument("--tables",help="Only use this is selecting from_db",
                        nargs="*",action=dbBeforeTables)    
    parser.add_argument("root",help="Enter the root of the directory path",
                        action="store")
    parser.add_argument("numfiles",help="Enter the number of files you " + \
                        "want to check in this iteration.",action="store",
                        type=int)
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


    current_date = datetime.now()
    isof_current_date = current_date.strftime("%Y-%m-%dT%H:%M:%S")
    sixty_days_ago_date = current_date - timedelta(days=60)
    isof_sixty_days_ago_date = sixty_days_ago_date.strftime( \
                            "%Y-%m-%dT%H:%M:%S")
    if args.from_db:
        db = Database(args.from_db, ['record','file'])
        class Record(db.base):
            __table__ = Table('record', db.metadata, autoload=True)
            
        class File(db.base):
            __table__ = Table('file', db.metadata, autoload=True)        
        accessions_to_check  = db.session.query(Record). \
                                   filter(or_(Record.lastFixityCheck == None,
                                          Record.lastFixityCheck \
                                              <= isof_sixty_days_ago_date,
                                          Record.fixityCheckCompleteness \
                                              == 'incompleted',
                                          Record.fixityCheckCompleteness \
                                              == None)).subquery()
        files_to_check = db.session.query(File.accession,
                                          File.checksum,
                                          File.size,
                                          File.filepath). \
                            filter(File.accession== \
                                   accessions_to_check.c.receipt,
                               or_(File.lastFixityCheck == None,
                                   File.lastFixityCheck \
                                       <= isof_sixty_days_ago_date)). \
                                       order_by(func.random()).limit(args.numfiles)
        b = Batch(args.root, query = files_to_check)
        generated_output = b.find_items(from_db = True)
    else:
        b = Batch(args.root, directory = args.directory_path)
        generated_output = b.find_items(from_directory=True)
    b.set_items(generated_output)
    try:
        for n in b.items:
            if exists(n.filepath):
                sha256_fixity = n.find_hash_of_file(sha256)
                mime = n.find_file_mime_type()
                n.set_hash(sha256_fixity)
                n.set_file_mime_type(mime)
                new_hash = n.get_hash()
                old_hash = n.get_old_hash()
                if new_hash != old_hash:
                    logger.error("{path} is corrupted".format(path=n.filepath))
            else:
                logger.error("{path} does not exist on the filesystem".format(path=n.filepath))
        return 0
    except KeyboardInterrupt:
         logger.error("Program aborted manually")
         return 131

if __name__ == "__main__":
    _exit(main())
