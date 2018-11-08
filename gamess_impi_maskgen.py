#!/usr/bin/env python3
"""
Created on Mon Jul 16 2018

@author: Vladimir Mironov
"""
from __future__ import print_function
import sys
import getopt

def mkmasks(ntasks, ncores, groupsize=1, htcores=False, readable=False):
    """make masks for running GAMESS FMO simulations on multicore environment"""

    assert ncores % ntasks == 0, \
            "ncores should be a multiple of ntasks: " \
            "ncores = %i, ntasks = %i" % (ncores, ntasks)

    assert ntasks % groupsize == 0, \
            "ntasks should be a multiple of groupsize: " \
            "ntasks = %i, groupsize = %i" % (ntasks, groupsize)

    masks_tmp = []
    masks = [[0]]*(2*ntasks)

    cores_per_task = int(ncores/ntasks)

    for i in range(2*ntasks):

        if htcores:
            core_start = (i*cores_per_task) % (ncores)
        else:
            core_start = (i*cores_per_task) % (ncores*4)

        core_end = core_start+cores_per_task

        mask_task = list(range(core_start, core_end)) + \
                    list(range(core_start+2*ncores, core_end+2*ncores))

        if htcores:
            mask_task = mask_task + list(range(core_start+ncores, core_end+ncores)) + \
                                    list(range(core_start+3*ncores, core_end+3*ncores))

        masks_tmp.append(mask_task)

    for i in range(0, ntasks, groupsize):
        masks[2*i:2*i+groupsize] = masks_tmp[i:i+groupsize]
        masks[2*i+groupsize:2*i+2*groupsize] = masks_tmp[i+ntasks:i+ntasks+groupsize]

    masks_bitmap = map(list_to_bitmap, masks)

    print_hex_masks(masks_bitmap, ncores, readable)

def list_to_bitmap(int_list):
    """Convert list of numbers to integer bitmap"""
    res = 0
    for elem in int_list:
        res = set_bit(res, elem)
    return res

def print_hex_masks(masks, ncores=0, readable=False):
    """Print the masks in hexadecimal format"""
    strend = ""
    if not readable:
        print("I_MPI_PIN_DOMAIN=[\\")
        strend = "]"

    strmasks = \
        map( \
            lambda x: \
                max(ncores-len(hex(x))+2, 0)*" " + "\'%x\'" % x if readable \
                else "\'%x\'" % x, \
            masks)
    print(",\\\n".join(strmasks) + strend)

def set_bit(number, offset):
    """Set the `offset` bit in the binary representation of `number` to 1"""
    return number | (1 << offset)

def main(argv, name):
    """wrapper to mkmasks"""
    ntasks = -1
    ncores = -1
    groupsize = -1
    htcores = False
    readable = False
    try:
        opts, _ = getopt.getopt(argv, "ht:c:g:xv")
    except getopt.GetoptError:
        print_help(name)
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_help(name)
            sys.exit()
        elif opt in "-c":
            ncores = int(arg)
        elif opt in "-t":
            ntasks = int(arg)
        elif opt in "-g":
            groupsize = int(arg)
        if opt == '-x':
            htcores = True
        if opt == '-v':
            readable = True

    if groupsize == -1:
        groupsize = ntasks

    if ntasks == -1:
        print('Please, specify number of tasks!')
        sys.exit(3)

    if ncores == -1:
        print('Please, specify number of cores!')
        sys.exit(4)

    mkmasks(ntasks, ncores, groupsize, htcores, readable)

def print_help(name):
    """Prints help for this script"""
    print("Usage: %s -t <ntasks> -c <ncores> [-g <groupsize>] [-x]" % name)
    print("\t-h                    Print this help")
    print("\t-t <ntasks>           Number of GAMESS workers (w/o DDI data servers) per node")
    print("\t-c <ncores>           Number of physical cores per node")
    print("\t-g <groupsize>        Value of DDI_LOGICAL_NODE_SIZE variable")
    print("\t-x                    Whether HyperThreads should be used for workers")
    print("\t-v                    More readable format")

if __name__ == "__main__":
    main(sys.argv[1:], sys.argv[0])
