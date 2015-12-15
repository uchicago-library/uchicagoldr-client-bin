#!/usr/bin/python3

# Default package imports begin #
from argparse import ArgumentParser
from os import _exit
from os.path import split, exists, splitext, basename, isdir, isfile, abspath, \
    join
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
from uchicagoldr.item import Item
from uchicagoldr.bash_cmd import BashCommand
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
This program takes a batch object and produces preservation stable
file formats from the files in it.
"""


# Functions begin #
def parseResult(result,filepath):
    if result[0] == False:
        logger.warn("Conversion failed!")
        logger.debug("Command output follows:")
        logger.debug(result[1])
        logger.debug("Command output ends")
    elif result[0] == None:
        pass
    else:
        logger.debug(str(result))
        if result[1].returncode != 0:
            logger.warn("Conversion of " +
                        filepath +
                        " returned a non-zero exit status: " +
                        str(result[1].returncode))
            logger.debug("Command output follows:")
            logger.debug(result[1])
            logger.debug("Command output ends")
        logger.info("Conversion run")


def audioConverter(item):
    if not exists(item.get_file_path()+'.presform.wav'):
        audioConvertArgs = ['ffmpeg', '-n', '-i', item.get_file_path(),
                            item.get_file_path()+'.presform.wav']
        audioConvertCommand = BashCommand(audioConvertArgs)
        audioConvertCommand.set_timeout(timeout)
        audioConvertCommand.run_command()
        logger.debug(audioConvertCommand.get_data())
        return audioConvertCommand.get_data()
    else:
        logger.info("Audio (wav) preservation format for file exists. " +
                    "Not Clobbering.")
        return (None, None)


def videoConverter(item):
    if not exists(item.get_file_path()+'.presform.avi'):
        videoConvertArgs = ['ffmpeg', '-n', '-i', item.get_file_path(),
                            '-vcodec', 'rawvideo', '-acodec', 'pcm_u24le',
                            '-pix_fmt', 'uyvy422', '-vtag', '2vuy',
                            item.get_file_path()+".presform.avi"]
        videoConvertCommand = BashCommand(videoConvertArgs)
        videoConvertCommand.set_timeout(timeout)
        videoConvertCommand.run_command()
        logger.debug(videoConvertCommand.get_data())
        return videoConvertCommand.get_data()
    else:
        logger.info("Video (avi) preservation format for file exists. " +
                    "Not Clobbering.")
        return (None, None)


def imageConverter(item):
    if not exists(item.get_file_path()+'.presform.tif'):
        imageConvertArgs = ['ffmpeg', '-n', '-i', item.get_file_path(),
                            item.get_file_path()+'.presform.tif']
        imageConvertCommand = BashCommand(imageConvertArgs)
        imageConvertCommand.set_timeout(timeout)
        imageConvertCommand.run_command()
        logger.debug(imageConvertCommand.get_data())
        return imageConvertCommand.get_data()
    else:
        logger.info("Image (tif) preservaiton format for file exists. " +
                    "Not Clobbering.")
        return(None, None)


def gifConverter(item):
    if not exists(item.get_file_path()+'.presform'):
        mkdirArgs = ['mkdir', item.get_file_path()+".presform"]
        mkdirCommand = BashCommand(mkdirArgs)
        mkdirCommand.run_command()
        gifConvertArgs = ['ffmpeg', '-n', '-i', item.get_file_path(),
                          item.get_file_path() +
                          '.presform/output%04d.presform.tif']
        gifConvertCommand = BashCommand(gifConvertArgs)
        gifConvertCommand.set_timeout(timeout)
        gifConvertCommand.run_command()
        logger.debug(gifConvertCommand.get_data())
        return gifConvertCommand.get_data()
    else:
        logger.info("Image (tif) preservation format for file exists. " +
                    "Not Clobbering.")
        return(None, None)


def zipConverter(item):
    if not exists(item.get_file_path()+'.presform.extracted'):
        unzipCommandArgs = ['7z', 'x',
                            '-o'+item.get_file_path()+'.presform.extracted',
                            item.get_file_path()]
        unzipCommand = BashCommand(unzipCommandArgs)
        unzipCommand.set_timeout(timeout)
        unzipCommand.run_command()
        if exists(item.get_file_path()+'.presform.extracted'):
            b = Batch(root, item.get_file_path()+'.presform.extracted')
            for item in b.find_items(from_directory=True):
                itemStack.append(item)
        return unzipCommand.get_data()
    else:
        logger.info("Already extracted.")
        return(None, None)


def officeConverter(item):
    if not exists(item.get_file_path()+'.presform.pdf'):
        fileName, fileExtension = splitext(item.get_file_path())
        mkdirArgs = ['mkdir', '-p', '/tmp/officeConv']
        mkdirCommand = BashCommand(mkdirArgs)
        mkdirCommand.set_timeout(timeout)
        mkdirCommand.run_command()
        officeConvertArgs = ['/Applications/LibreOffice.app/Contents/MacOS/soffice',
                             '--headless', '--convert-to', 'pdf',
                             '--outdir', '/tmp/officeConv',
                             item.get_file_path()]
        officeConvertCommand = BashCommand(officeConvertArgs)
        officeConvertCommand.set_timeout(timeout)
        officeConvertCommand.run_command()
        cpCommandArgs = ['cp', '/tmp/officeConv/'+basename(fileName)+'.pdf',
                         item.get_file_path()+'.presform.pdf']
        cpCommand = BashCommand(cpCommandArgs)
        cpCommand.run_command()
        rmCommandArgs = ['rm', '-r', '/tmp/officeConv']
        rmCommand = BashCommand(rmCommandArgs)
        rmCommand.run_command()
        logger.debug(officeConvertCommand.get_data())
        return officeConvertCommand.get_data()
    else:
        logger.info("Office (PDF) preservation format for file exists. " +
                    "Not Clobbering.")
        return(None, None)


def xlsConverter(item):
    if not exists(item.get_file_path()+'.presform.csv'):
        fileName, fileExtension = splitext(item.get_file_path())
        mkdirArgs = ['mkdir', '-p', '/tmp/officeConv']
        mkdirCommand = BashCommand(mkdirArgs)
        mkdirCommand.set_timeout(timeout)
        mkdirCommand.run_command()
        officeConvertArgs = ['/Applications/LibreOffice.app/Contents/MacOS/soffice',
                             '--headless', '--convert-to', 'csv',
                             '--outdir', '/tmp/officeConv',
                             item.get_file_path()]
        officeConvertCommand = BashCommand(officeConvertArgs)
        officeConvertCommand.set_timeout(timeout)
        officeConvertCommand.run_command()
        cpCommandArgs = ['cp', '/tmp/officeConv/'+basename(fileName)+'.csv',
                         item.get_file_path()+'.presform.csv']
        cpCommand = BashCommand(cpCommandArgs)
        cpCommand.set_timeout(timeout)
        cpCommand.run_command()
        rmCommandArgs = ['rm', '-r', '/tmp/officeConv']
        rmCommand = BashCommand(rmCommandArgs)
        rmCommand.set_timeout(timeout)
        rmCommand.run_command()
        logger.debug(officeConvertCommand.get_data())
        return officeConvertCommand.get_data()
    else:
        logger.info("Office (CSV) preservation format for file exists. " +
                    "Not Clobbering.")
        return(None, None)


def txtConverter(item):
    if not exists(item.get_file_path()+'.presform.txt'):
        fileName, fileExtension = splitext(item.get_file_path())
        mkdirArgs = ['mkdir', '-p', '/tmp/officeConv']
        mkdirCommand = BashCommand(mkdirArgs)
        mkdirCommand.set_timeout(timeout)
        mkdirCommand.run_command()
        officeConvertArgs = ['/Applications/LibreOffice.app/Contents/MacOS/soffice',
                             '--headless', '--convert-to', 'txt:Text',
                             '--outdir', '/tmp/officeConv',
                             item.get_file_path()]
        officeConvertCommand = BashCommand(officeConvertArgs)
        officeConvertCommand.set_timeout(timeout)
        officeConvertCommand.run_command()
        cpCommandArgs = ['cp', '/tmp/officeConv/'+basename(fileName)+'.txt',
                         item.get_file_path()+'.presform.txt']
        cpCommand = BashCommand(cpCommandArgs)
        cpCommand.set_timeout(timeout)
        cpCommand.run_command()
        rmCommandArgs = ['rm', '-r', '/tmp/officeConv']
        rmCommand = BashCommand(rmCommandArgs)
        rmCommand.set_timeout(timeout)
        rmCommand.run_command()
        logger.debug(officeConvertCommand.get_data())
        return officeConvertCommand.get_data()
    else:
        logger.info("Office (CSV) preservation format for file exists. " +
                    "Not Clobbering.")
        return(None, None)


def htmlConverter(item):
    if not exists(item.get_file_path()+'.presform.pdf'):
        originalFilePath = item.get_file_path()
        intermediaryFilePath = originalFilePath+'.intermediary.pdf'
        wkhtmltopdfArgs = ['wkhtmltopdf', item.get_file_path(),
                           intermediaryFilePath]
        wkhtmltopdfCommand = BashCommand(wkhtmltopdfArgs)
        wkhtmltopdfCommand.set_timeout(timeout)
        wkhtmltopdfCommand.run_command()
        i = Item(intermediaryFilePath, root)
        itemStack.append(i)
        return wkhtmltopdfCommand.get_data()
    else:
        return (None, None)


def parse(item):
    # Handy dandy lists
    audioExtensions = ['.mp3', '.wma', '.wav', '.aiff', '.midi']
    audioMimes = ['audio/x-aiff', 'audio/basic', 'audio/midi', 'audio/mp4',
                  'audio/mpeg', 'audio/x-ape', 'audio/x-pn-realaudio',
                  'audio/x-wav']
    officeExtensions = ['.docx', '.doc', '.xls', '.xlsx', '.ppt', '.pptx',
                        '.pdf', '.rtf']
    officeMimes = ["application/msword", "application/vnd.ms-office",
                   "application/vnd.ms-excel", "application/vnd.ms-powerpoint",
                   "application/vnd.oasis.opendocument.spreadsheet",
                   "application/vnd.oasis.opendocument.text",
                   "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                   "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   'text/rtf', 'application/pdf']
    videoExtensions = [".wmv", ".vob"]
    videoMimes = ["video/quicktime", 'video/3gpp', 'video/mp2p', 'video/mp4',
                  'video/mpeg', 'video/mpv', 'video/x-flv', 'video/x-m4v',
                  'video/x-ms-asf', 'video/x-msvideo']
    imageExtensions = ['.jpg', '.jpeg', '.png', '.pct']
    imageMimes = ["image/jpeg", "image/x-ms-bmp", 'image/x-ms-bmp',
                  'image/png', 'image/x-paintnet', 'image/x-portable-bitmap',
                  'image/x-portable-greymap']
    zipExtensions = ['.zip', '.tar.gz', '.7z', '.rar']
    zipMimes = ['application/x-7z-compressed', 'application/x-bzip2',
                'application/x-gzip', 'application/x-rar',
                'application/x-stuffit', 'application/x-tar',
                'application/zip']
    htmlExtensions = ['.html', '.htm']
    htmlMimes = ['text/html']

    excludeExtensions = ['.exe']
    excludeMimes = ['application/x-executable']

    extension = item.find_file_extension().lower()

    # Skip cases
    if ".presform" in item.find_file_name():
        logger.info("Skipping - presform")
        return

    if ".DS_Store" == item.find_file_name():
        logger.info("Skipping - .DS_Store")
        return

    if item.find_file_name()[0] == ".":
        logger.info("Skipping - dotfile")
        return

    if extension in excludeExtensions:
        logger.info("Skipping - excluded extension")
        return

    if item.find_file_mime_type() in excludeMimes:
        logger.info("Skipping - excluded mime type")
        return

    # Conversion conditionals
    if extension in audioExtensions or item.find_file_mime_type() in audioMimes:
        logger.info("Audio extension or mime detected")
        result = audioConverter(item)
        parseResult(result, item.get_file_path())

    if extension in officeExtensions or \
            item.find_file_mime_type() in officeMimes:
        logger.info("Office extension or mime detected")
        result = officeConverter(item)
        parseResult(result, item.get_file_path())

    if extension == ".xls" or extension == ".xlsx":
        logger.info("XLS extension detected")
        result = xlsConverter(item)
        parseResult(result, item.get_file_path())

    if extension == ".doc" or extension == ".docx":
        logger.info("DOC extension detected")
        result = txtConverter(item)
        parseResult(result, item.get_file_path())

    if extension in videoExtensions or item.find_file_mime_type() in videoMimes:
        logger.info("Video extension or mime detected")
        result = videoConverter(item)
        parseResult(result, item.get_file_path())

    if extension in imageExtensions or item.find_file_mime_type() in imageMimes:
        logger.info("Image extension or mime detected")
        result = imageConverter(item)
        parseResult(result, item.get_file_path())

    if extension == ".gif":
        logger.info("GIF extension detected")
        result = gifConverter(item)
        parseResult(result, item.get_file_path())

    if extension in zipExtensions or item.find_file_mime_type() in zipMimes:
        logger.info("Zip extension or mime detected")
        result = zipConverter(item)
        parseResult(result, item.get_file_path())

    if extension in htmlExtensions or item.find_file_mime_type() in htmlMimes:
        logger.info("HTML extension or mime detected")
        result = htmlConverter(item)
        parseResult(result, item.get_file_path())
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
                        "directory path that you need to validate against" +
                        " a type of controlled collection"
    )
    parser.add_argument(
                        "root",
                        help="Enter the root of the directory path",
                        action="store"
    )
    parser.add_argument(
                        "-t", '--timeout',
                        help="Enter a timeout for conversions in seconds, " +
                        "after which they will fail",
                        action="store",
                        type=int
    )
    parser.add_argument(
                        '--admindir',
                        help="Enter the location of the admin directory " +
                        "where the required debug log will be saved",
                        action="store",
                        required=True
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

    if not exists(args.admindir):
        logger.critical("The specified admin directory doesn't exist!")
        return(1)
    if not isdir(args.admindir):
        logger.critical("The specified admin directory location isn't" +
                        "a directory!")
    stagingDebugLog = DebugFileHandler(join(
        args.admindir, "fileConversions.txt")
    )
    logger.addHandler(stagingDebugLog)
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
        global itemStack
        itemStack = []
        global root
        root = abspath(args.root)
        item_path = abspath(args.item)
        global timeout
        timeout = args.timeout

        if isdir(item_path):
            b = Batch(root, item_path)
            for item in b.find_items(from_directory=True):
                itemStack.append(item)
        if isfile(item_path):
            itemStack.append(Item(item_path, root))

        for item in itemStack:
            logger.info("Parsing "+item.get_file_path())
            parse(item)
            logger.info("Parsing complete on "+item.get_file_path())
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
