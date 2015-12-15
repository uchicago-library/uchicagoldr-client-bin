
__author__ = "Brian Balsamo"
__copyright__ = "Copyright 2015, The University of Chicago"
__version__ = "1.0.0"
__maintainer__ = "Brian Balsamo"
__email__ = "balsamo@uchicago.edu"
__status__ = "Prototype"

"""
Compute the TFIDFs of the terms in .presform.txt files in a batch
"""

from argparse import ArgumentParser
from logging import DEBUG, FileHandler, Formatter, getLogger, \
    INFO, StreamHandler
from os import _exit
from operator import itemgetter
from os.path import abspath
from operator import itemgetter

from uchicagoldr.batch import Batch
from uchicagoldr.item import Item
from uchicagoldr.textitem import TextItem
from uchicagoldr.textbatch import TextBatch

def main():
    # start of parser boilerplate
    parser = ArgumentParser(description="Produce TFIDF numbers for terms in the text preservation formats in a batch",
                            epilog="Copyright University of Chicago; " + \
                            "written by "+__author__ + \
                            " "+__email__)

    parser.add_argument("-v", help="See the version of this program",
                        action="version", version=__version__)
    # let the user decide the verbosity level of logging statements
    # -b sets it to INFO so warnings, errors and generic informative statements
    # will be logged
    parser.add_argument( \
                         '-b','-verbose',help="set verbose logging",
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
    parser.add_argument("restritem", help="Enter a noid for an accession or a " + \
                        "directory path that you need to validate against" + \
                        " a type of controlled collection"
    )
    parser.add_argument("restrroot",help="Enter the root of the directory path",
                        action="store"
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
    ch = StreamHandler()
    ch.setFormatter(log_format)
    logger.setLevel(args.log_level)
    if args.log_loc:
        fh = FileHandler(args.log_loc)
        fh.setFormatter(log_format)
        logger.addHandler(fh)
    logger.addHandler(ch)
    try:
        args.restritem=abspath(args.restritem)
        args.restrroot=abspath(args.restrroot)
        args.item=abspath(args.item)
        args.root=abspath(args.root)

        b = Batch(args.restrroot, args.restritem)
        restrDocs=TextBatch(args.restritem,args.restrroot)
        for item in b.find_items(from_directory=True):
            if ".presform.txt" in item.find_file_name():
                textDoc=TextItem(item.get_file_path(),item.get_root_path())
                restrDocs.add_item(textDoc)
        if restrDocs.validate_items():
            logger.info("Generating language model from provided document set.")
            logger.info("Getting document term indices")
            term_map={}
            for item in restrDocs.get_items():
                item.set_raw_string(item.find_raw_string())
                indexOut=item.find_index(purge_raw=True,scrub_text=False,stem=False,term_map=term_map)
                item.set_index(indexOut[0])
                term_map.update(indexOut[1])
            restrDocs.set_term_map(term_map)
            logger.info("Generating corpus term index")
            restrDocs.set_term_index(restrDocs.find_term_index())
            logger.info("Getting iIDFs")
            restrDocs.set_doc_counts(restrDocs.find_doc_counts())
            restrDocs.set_iIdfs(restrDocs.find_iIdfs())
            logger.info("Computing Language Model")
            restrDocs.set_language_model(restrDocs.find_language_model())
            logger.info("Computing LM VSM")
            restrDocs.set_vector_space_model(restrDocs.find_vector_space_model())

        c=Batch(args.root,args.item)
        Docs=TextBatch(args.root,args.item)
        for item in c.find_items(from_directory=True):
            if ".presform.txt" in item.find_file_name():
                textDoc=TextItem(item.get_file_path(),item.get_root_path())
                Docs.add_item(textDoc)
        if Docs.validate_items():
            logger.info("Generating TFIDF models for each document in the batch.")
            logger.info("Getting document term indices")
            tote=len(Docs.get_items())
            i=0
            for item in Docs.get_items():
                i+=1
                print("\r"+str(i)+"/"+str(tote)+" - "+item.get_file_path(),end="")
                item.set_raw_string(item.find_raw_string())
                indexOut=item.find_index(purge_raw=True,scrub_text=False,stem=False,term_map=term_map,only_mapped=True)
                item.set_index(indexOut[0])
            print()
            logger.info("Getting IDFs")
            Docs.set_doc_counts(Docs.find_doc_counts())
            Docs.set_idfs(Docs.find_idfs())
            logger.info("Computing TFIDFs")
            Docs.set_tf_idfs(Docs.find_tf_idfs())
            logger.info("Generating document vector space models.")
            Docs.set_document_vector_space_models(Docs.find_document_vector_space_models())
            
            logger.info("Computing similarity metrics.")
            
            rels=[]
            for document in Docs.get_document_vector_space_models():
                rels.append((document,restrDocs.find_similarity(Docs.get_document_vector_space_models()[document])))
            logger.info("Sorting similarity metrics for output")
            rels=sorted(rels,key=itemgetter(1))
            for entry in rels:
                print(entry[0]+": "+str(entry[1]))

            
        return 0
    except KeyboardInterrupt:
        logger.error("Program aborted manually")
        return 131

if __name__ == "__main__":
    _exit(main())
