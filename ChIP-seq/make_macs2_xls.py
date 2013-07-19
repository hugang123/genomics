#!/bin/env python
#
#     make_macs2_xls.py: Convert MACS output file to XLS spreadsheet
#     Copyright (C) University of Manchester 2013 Peter Briggs, Ian Donaldson
#
########################################################################
#
# make_macs2_xls.py
#
#########################################################################

"""make_macs2_xls.py

Convert MACS output file to XLS spreadsheet

Given tab-delimited output from MACS, creates an XLS spreadsheet with
3 sheets: one containing the tabulated data plus extra columns derived
from that data (e.g. summit+/-100bps); one containing the header
information from the input; and one describing what each of the columns
in the data sheet are.

This is a modified version of make_macs_xls.py updated to work with
output from MACS 2.0.10(alpha)."""

#######################################################################
# Import modules that this module depends on
#######################################################################

import os
import sys
import optparse
import logging
# Configure logging output
logging.basicConfig(format="[%(levelname)s] %(message)s")
# Put ../share onto Python search path for modules
SHARE_DIR = os.path.abspath(
    os.path.normpath(
        os.path.join(os.path.dirname(sys.argv[0]),'..','share')))
sys.path.append(SHARE_DIR)
from TabFile import TabFile
import Spreadsheet

#######################################################################
# Module metadata
#######################################################################

__version__ = '0.1.0'

#######################################################################
# Class definitions
#######################################################################

# No classes defined

#######################################################################
# Functions
#######################################################################

# No functions defined

#######################################################################
# Main program
#######################################################################

if __name__ == "__main__":
    # Process command line
    p = optparse.OptionParser(usage="%prog <MACS2_OUTPUT> [ <XLS_OUT> ]",
                              version=__version__,
                              description=
                              "Create an XLS spreadsheet from the output of version 2.0.10 "
                              "of the MACS peak caller. <MACS2_OUTPUT> is the output '.xls' "
                              "file from MACS2; if supplied then <XLS_OUT> is the name to use "
                              "for the output file, otherwise it will be called "
                              "'XLS_<MACS2_OUTPUT>.xls'.")
    options,args = p.parse_args()
    # Get input file name
    if len(args) < 1 or len(args) > 2:
        p.error("Wrong number of arguments")
    macs_in = args[0]

    # Build output file name: if not explicitly supplied on the command
    # line then use "XLS_<input_name>.xls"
    if len(args) == 2:
        xls_out = args[1]
    else:
        # MACS output file might already have an .xls extension
        # but we'll add an explicit .xls extension
        xls_out = "XLS_"+os.path.splitext(os.path.basename(macs_in))[0]+".xls"
    print "Input file: %s" % macs_in
    print "Output XLS: %s" % xls_out

    # Extract the header from the MACS and feed actual data to
    # TabFile object
    header = []
    data = TabFile(column_names=['chr','start','end','length','abs_summit','pileup',
                                 '-log10(pvalue)','fold_enrichment','-log10(qvalue)'])
    fp = open(macs_in,'r')
    for line in fp:
        if line.startswith('#') or line.strip() == '':
            # Header line
            header.append(line.strip())
        else:
            # Data
            data.append(tabdata=line.strip())
    fp.close()

    # Temporarily remove first line
    header_line = str(data[0])
    del(data[0])

    # Attempt to detect MACS version
    macs_version = None
    for line in header:
        if line.startswith("# This file is generated by MACS version "):
            macs_version = line.split()[8]
            break
    if macs_version is None:
        logging.error("couldn't detect MACS version")
        sys.exit(1)
    else:
        print "Input file is from MACS %s" % macs_version

    # Sort into order by fold_enrichment and then by -log10(pvalue) column
    data.sort(lambda line: line['fold_enrichment'],reverse=True)
    data.sort(lambda line: line['-log10(pvalue)'],reverse=True)

    # Restore first line
    data.insert(0,tabdata=header_line)

    # Insert "order" column
    data.appendColumn("order")
    # Perhaps confusingly must also insert initial value "#order"
    data[0]['order'] = "#order"
    for i in range(1,len(data)):
        data[i]['order'] = i
    # Reorder columns to put it at the start
    data = data.reorderColumns(['order','chr','start','end','length','abs_summit','pileup',
                                '-log10(pvalue)','fold_enrichment','-log10(qvalue)'])

    # Legnds text
    legends_text = """order\tSorting order Pvalue and FE
chr\tChromosome location of binding region
start\tStart coordinate of binding region
end\tEnd coordinate of binding region
summit-100\tSummit - 100bp
summit+100\tSummit + 100bp
summit-1\tSummit of binding region - 1
summit\tSummit of binding region
length\tLength of binding region
abs_summit\tCoordinate of region summit
pileup\tNumber of non-degenerate and position corrected reads at summit
-LOG10(pvalue)\tTransformed Pvalue -log10(Pvalue) for the binding region (e.g. if Pvalue=1e-10, then this value should be 10)
fold_enrichment\tFold enrichment for this region against random Poisson distribution with local lambda
-LOG10(qvalue)\tTransformed Qvalue -log10(Pvalue) for the binding region (e.g. if Qvalue=0.05, then this value should be 1.3)
#FDR(%)\tFalse discovery rate (FDR) as a percentage
"""
    # Create a new spreadsheet
    wb = Spreadsheet.Workbook()

    # Create the sheets
    #
    # data = the actual data from MACS
    ws_data = wb.addSheet(os.path.basename(macs_in)[:min(30,len(os.path.basename(macs_in)))])
    #
    # note = the header data
    ws_notes = wb.addSheet("notes")
    ws_notes.addText("<style font=bold>MACS RUN NOTES:</style>")
    ws_notes.addTabData(header)
    ws_notes.addText("\n<style font=bold>ADDITIONAL NOTES:</style>\nBy default regions are sorted by Pvalue and fold enrichment (in descending order)")
    #
    # legends = static text explaining the column headers
    ws_legends = wb.addSheet("legends")
    ws_legends.addText(legends_text)

    # Add data to the "data" sheet
    ws_data.addText(str(data))

    # Insert formulae columns
    #
    # Copy of "chr" column
    ws_data.insertColumn(4,title="chr",insert_items="=B?")
    #
    # Summit-100
    ws_data.insertColumn(5,title="abs_summit-100",insert_items="=L?-100")
    #
    # Summit+100
    ws_data.insertColumn(6,title="abs_summit+100",insert_items="=L?+100")
    #
    # Copy of "chr" column
    ws_data.insertColumn(7,title="chr",insert_items="=B?")
    #
    # Summit-1
    ws_data.insertColumn(8,title="summit-1",insert_items="=L?-1")
    #
    # Summit
    ws_data.insertColumn(9,title="summit",insert_items="=L?")

    # Write the spreadsheet to file
    wb.save(xls_out)

