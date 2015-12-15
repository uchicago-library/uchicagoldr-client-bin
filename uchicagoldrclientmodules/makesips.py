
__author__ = "Tyler Danstrom"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "1.0.0"
__maintainer__ = "Tyler Danstrom"
__email__ = "tdanstrom@uchicago.edu"
__status__ = "Production"
__description__ = "This program takes a random selection of files from the ldr database and evaluates for file corruption."

from sys import argv, path

from argparse import Action, ArgumentParser
from configobj import ConfigObj
from datetime import datetime, timedelta
from grp import getgrgid
from pwd import getpwuid
from hashlib import md5, sha256
from logging import DEBUG, FileHandler, Formatter, getLogger, \
    INFO, StreamHandler
from os import _exit, stat
from os.path import exists, join, relpath
from re import compile as re_compile, split as re_split
from sqlalchemy import Table
from xml.etree import ElementTree as ET

from uchicagoldr.batch import Batch
from uchicagoldr.database import Database
from uchicagoldrsips.LDRFileTree import Data
from uchicagoldrsips.SIPS import make_identifier, make_providedcho

def evaluate_items(b, createdate):
    for n in b.items:
        header_pat = re_compile('^(\d{4}-\d{3})')
        if exists(n.filepath):
            n.root_path = args.root
            accession = n.find_file_accession()
            n.set_accession(accession)
            canonpath = n.find_canonical_filepath()
            if header_pat.search(canonpath):
                dirheader = header_pat.search(canonpath).group(1)
                canonpath = '/'.join(canonpath.split('/')[1:])
            else:
                dirheader = ""
                canonpath = canonpath
            n.set_canonical_filepath(canonpath)
            n.dirhead = dirheader
            n.createdate = createdate
            sha256_fixity = n.find_hash_of_file(sha256)
            md5_fixity = n.find_hash_of_file(md5)
            n.checksum = sha256_fixity
            mime = n.find_file_mime_type()
            size = n.find_file_size()
            n.mimetype = mime
            n.filesize = size
            accession = n.find_file_accession()
            if n.filepath.endswith('.dc.xml'):
                opened_file = open(n.filepath,'r')
                xml_doc = ET.parse(opened_file)
                xml_root = xml_doc.getroot()
                logger.info(xml_doc)
                logger.info(xml_root)
                n.title = xml_root.find('title').text if xml_root.find('title') != None else ""
                n.description = xml_root.find('description').text \
                                if xml_root.find('description') != None else ""
                n.date = xml_root.find('date').text if xml_root.find('date') != None else ""
                n.identifier = xml_root.find('identifier').text if xml_root.find('identiifer') != None else ""
            if n.mimetype == 'image/tiff':
                fits_file_path = join(n.filepath+'.fits.xml')
                if exists(fits_file_path):
                    opened_file = open(join(n.filepath+'.fits.xml'),'r')
                    xml_doc = ET.parse(opened_file)
                    xml_root = xml_doc.getroot()
                    md5checksum = xml_root.find("{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}fileinfo/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}md5checksum")
                    imageheight = xml_root.find("{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}metadata/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}image/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}imageHeight")
                    imagewidth = xml_root.find("{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}metadata/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}image/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}imageWidth")
                    bitspersample =  xml_root.find("{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}metadata/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}image/" + \
                                                "{http://hul.harvard.edu/ois/xml/ns/fits/fits_output}bitsPerSample")
                    n.imageheight = imageheight.text if imageheight != None else ""
                    n.imagewidth = imagewidth.text if imagewidth != None else ""
                    n.bitspersample = bitspersample.text if bitspersample != None else ""
                    n.mixchecksum = md5checksum.text if md5checksum != None else ""
                else:
                    logger.error("no fits.xml file for tiff {filename}". \
                                 format(filename = n.filepath))
            yield n
        else:
            logger.error("{path} does not exist on the filesystem". \
                         format(path=n.filepath))            

def main():
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
    parser.add_argument("-o","--object_level",
                        help="Enter the level at which object starts",
                        type=int,
                        action='store')
    parser.add_argument("-r", "--root",
                       help="Enter the root of the directory path",
                        action="store")
    parser.add_argument("directory_path", 
                        help="Enter a directory that you need to work on ",
                        action='store')

    parser.add_argument('pattern', help="Enter a pattern to filter files with",
                        action="store")
    global args
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
    db = Database("sqlite:////media/repo/repository/databases/" +  
                  "official/repositoryAccessions.db.new",tables_to_bind= \
                  ['record'])
                  

    class Record(db.base):
        __table__ = Table('record', db.metadata, autoload=True)
        
    b = Batch(args.root, directory = args.directory_path)
    difference_in_path = relpath(args.directory_path, args.root)

    query = db.session.query(Record.createdate).filter(Record.receipt == \
                                                       difference_in_path) 
    createdate = query.first()[0]
    items = b.find_items(from_directory = True, 
                         filterable = re_compile(args.pattern))
    b.set_items(items)
    try:
        generated_data = evaluate_items(b,createdate)
        count = 0
        objects = {}
        descriptive_metadata = '.dc.xml$'
        representation_file = '.pdf$'
        file_definers = ['dc.xml','ALTO','TIFF','JPEG','pdf','mets.xml',
                         '\d{4}.txt']
        file_definer_sequences = ['ALTO','TIFF','JPEG']
        page_number_pattern = '_(\w{4})'
        for n in generated_data:
            id_parts = args.pattern.split('/')
            id_parts_enumerated = [x for x in range(args.object_level)]
            id_part_values = [n.canonical_filepath.split('/')[x] \
                              for x in id_parts_enumerated]
            identifier = "-".join(id_part_values)
            to_add = None
            for p in file_definers:
                if p in n.canonical_filepath:
                    to_add = n
                    break
            if to_add:
                if objects.get(identifier):
                    objects.get(identifier).append(n)
                else:
                    objects[identifier] = [n]
            else:
                logger.error("{fpath} in {id} could not be matched". \
                             format(fpath = n.canonical_filepath,
                                    id = identifier))
        for k, v in objects.items():
            for p in file_definer_sequences:
                sequence = sorted([(int(re_compile(page_number_pattern). \
                            search(x.canonical_filepath).group(1).lstrip('0')),
                             x.canonical_filepath) \
                            for x in v if p in x.canonical_filepath])
                known_complete_page_range = [x for x in \
                                             range(sequence[-1][0])][1:]
                what_is_actually_present  = [x[0] for x in sequence]
                if set(known_complete_page_range) - \
                   set(what_is_actually_present):
                    difference = list(set(known_complete_page_range) - \
                                      set(what_is_actually_present))
                    l = [str(x) for x in list(difference)]
                    logger.error("The sequence part {part} ". \
                                 format(part = p) + 
                                 "is missing pages {pages}". \
                                 format(pages = ','.join(l)))
            for p in file_definers:
                seek = [x for x in v if p in x.canonical_filepath]
                if len(seek) == 0:
                    logger.error("{identifier}". \
                                 format(identifier = identifier) + \
                                " missing part {part}".format(part = p))
            i = make_identifier(id_part_values, v)
            metadata = [x for x in v if re_compile(descriptive_metadata). \
                        search(x.canonical_filepath)][0]
            representation = [x for x in v if re_compile(representation_file). \
                        search(x.canonical_filepath)][0]
            providedcho = make_providedcho(i, metadata)
            print(providedcho)
            aggregation = make_aggregation(i, representation)
            print(aggregation)
            logger.info(i)

        return 0
    except KeyboardInterrupt:
         logger.error("Program aborted manually")
         return 131

if __name__ == "__main__":
    _exit(main())
