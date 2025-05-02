#!/usr/bin/env python

import sys
import os
import traceback
import logging
import importlib
import argparse
import argcomplete
import socket

# Set global HTTP timeouts to 10 seconds
socket.setdefaulttimeout(10)

CONGRESS_ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    args = parse_arguments()
    process_arguments(args)
    configure_logging(args)

    task_name, options = parse_task_and_options()

    try:
        run_task(task_name, options)
    except Exception as exception:
        import utils
        utils.admin(exception)


def parse_arguments():
    parser = argparse.ArgumentParser(description="USC Run CLI Tool")
    parser.add_argument("data_type", choices=["bills", "committee_meetings", "govinfo", "nominations", "statutes", "votes"], help="Type of data to process")
    parser.add_argument("--bill_id", help="Bill ID to process (e.g., s968-112)", required=False).completer = billid_completer
    parser.add_argument("--bulkdata", help="Specify the bulk data type for govinfo (e.g., BILLSTATUS)", required=False).completer = bulkdata_completer
    parser.add_argument("--collections", help="Specify the collection type for govinfo (e.g., STATUTES)", required=False).completer = collections_completer
    parser.add_argument("--congress", help="Specify the congress number (e.g., 112)", required=False)
    parser.add_argument("--force", action="store_true", help="Suppress use of cache for network-retrieved resources")
    parser.add_argument("--granules", help="Specify the granule", required=False).completer = granule_completer
    parser.add_argument("--limit", help="Limit the number of items to process", type=int, required=False)
    parser.add_argument("--list", action="store_true", help="List of collection names", required=False).completer = list_completer
    parser.add_argument("--log", choices=["info", "debug", "error"], default="info", help="Set logging level")
    parser.add_argument("--nomination-id", help="Nomination ID to process (e.g., 112-1)", required=False).completer = nominations_completer
    parser.add_argument("--store", help="Specify the storage type (e.g.: pdf,mods,xml,txt)", required=False, choices=['mods'])
    parser.add_argument("--volumes", "--volume", help="Specify the volume number for statutes, e.g. 65, 65-86", required=False).completer = volumes_completer
    parser.add_argument("--years", "--year", help="Specify the year for statutes, e.g. 1951, 1951-1972", required=False).completer = years_completer
    parser.add_argument("--textversions", "--extracttext", '--linkpdf', required=False).completer = statutes_completer

    argcomplete.autocomplete(parser, always_complete_options=False)
    return parser.parse_args()


def process_arguments(args):
    if args.data_type == "govinfo" and args.bulkdata:
        print(f"Processing govinfo with bulkdata={args.bulkdata}")
    elif args.data_type == "govinfo":
        print("Processing govinfo without bulkdata")
    else:
        print(f"Processing {args.data_type}")

    if args.force:
        print("Force flag is enabled")

    print(f"Log level set to {args.log}")


def configure_logging(args):
    log_level = args.log.upper()
    logging.basicConfig(format='%(asctime)s %(message)s' if args.force else '%(message)s', level=log_level)


def parse_task_and_options():
    task_name = sys.argv[1]
    options = {}

    for arg in sys.argv[2:]:
        if arg.startswith("--"):
            key, value = (arg.split('=') + [True])[:2]
            key = key.lstrip("--").lower()
            options[key] = value if value not in ['True', 'False'] else value == 'True'

    return task_name, options


def run_task(task_name, options):
    sys.path.append(os.path.join(CONGRESS_ROOT, "tasks"))
    task_mod = __import__(task_name)

    if 'patch' in options:
        apply_patch(options['patch'], task_name)

    task_mod.run(options)


def apply_patch(patch_name, task_name):
    patch_mod = importlib.import_module(patch_name)
    patch_func = getattr(patch_mod, 'patch', None)

    if patch_func is None or not callable(patch_func):
        logging.error(f"You specified a --patch argument but {patch_name}.patch is not callable or does not exist.")
        sys.exit(1)

    patch_mod.patch(task_name)


# Completers
def bulkdata_completer(prefix, parsed_args, **kwargs):
    return ["BILLSTATUS", "OTHERDATA"] if parsed_args.data_type == "govinfo" else None


def collections_completer(prefix, parsed_args, **kwargs):
    return ["STATUTES", "OTHERCOLLECTIONS"] if parsed_args.data_type == "govinfo" else None


def billid_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "bills" else None


def volumes_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "statutes" else None


def years_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "statutes" else None


def list_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "govinfo" else None


def statutes_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "statutes" else None


def granule_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "govinfo" else None


def nominations_completer(prefix, parsed_args, **kwargs):
    return [] if parsed_args.data_type == "nominations" else None


if __name__ == "__main__":
    main()
