'''
add an equipment record to an asset action log
by scanning the barcode
'''

import argparse
import services.airtable.airtable as airtable


def scan_barcode():
    '''
    returns the barcode from user input
    '''
    barcode = input("Barcode: ")
    return barcode


def attach_equipment_to_aal(args):
    '''
    manages the process
    '''
    aal_auto_id = args.auto_id
    if not aal_auto_id:
        aal_auto_id = input("Please Enter the 4-digit Auto ID \n"
        "for this Asset Action Log: ")
    try:
        aal_auto_id = int(aal_auto_id)
    except Exception:
        print("there was a problem with that Auto ID")
        print("please ensure it's just a 4-digit integer")
    atbl_conf = airtable.config()
    atbl_tbl_aal = airtable.connect_one_table("Physical Asset Action Log", atbl_conf)
    atbl_tbl_eqp = airtable.connect_one_table("ALL SI AV EQUIPMENT", atbl_conf)
    atbl_rec_aal = airtable.find(aal_auto_id, "Auto ID", atbl_tbl_aal, True)
    while True:
        print("Please Enter the Barcode below")
        print("Or type 'exit' to close")
        barcode = scan_barcode()
        if barcode.lower() in ['exit']:
            return
        atbl_rec_eqp = airtable.find(barcode, "Equip. Barcode", atbl_tbl_eqp, True)
        atbl_rec_aal['fields']['Equipment Used - Asset Action'] = [atbl_rec_eqp['id']]
        atbl_rec_aal.save()


def init():
    '''
    get the CLI arguments etc
    '''
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-q', '--quiet', dest='quiet',
                        action='store_true', default=False,
                        help="run script in quiet mode. "
                        "only print warnings and errors to command line")
    parser.add_argument('-v', '--verbose', dest='verbose',
                        action='store_true', default=False,
                        help="run script in verbose mode. "
                        "print all log messages to command line")
    parser.add_argument('--auto_id', dest='auto_id',
                        default=None,
                        help="the 4-digit autonumber for the Asset "
                        "Action Log that you'd like to attach the "
                        "equipment to")
    args = parser.parse_args()
    return args


def main():
    '''
    do the thing
    '''
    print("starting...")
    args = init()
    attach_equipment_to_aal(args)
    
    


if __name__ == "__main__":
    main()
