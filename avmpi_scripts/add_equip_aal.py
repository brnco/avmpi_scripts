'''
add an equipment record to an asset action log
by scanning the barcode
'''

import argparse
import services.airtable.airtable as airtable


def scan_barcode() -> str:
    '''
    returns the barcode from user input
    '''
    barcode = input("Barcode: ")
    return barcode


def attach_equipment_to_aal(args: argparse.Namespace):
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
    atbl_base = airtable.connect_one_base("Assets")
    atbl_tbl_aal = atbl_base["Physical Asset Action Log"]
    atbl_tbl_eqp = atbl_base["ALL SI AV EQUIPMENT"]
    while True:
        atbl_rec_aal = airtable.find(aal_auto_id, "Auto ID #", atbl_tbl_aal, True)
        print("Please Enter the Barcode below")
        print("Or type 'exit' to close")
        barcode = scan_barcode()
        if barcode.lower() in ['exit']:
            return
        atbl_rec_eqp = airtable.find(barcode, "Equip. Barcode", atbl_tbl_eqp, True)
        if not atbl_rec_eqp:
            print(f"unable to find equipment with barcode {barcode}")
            print("please try again")
            continue
        if args.field == 'asset_action':
            field = 'Equipment Used - Asset Action'
        elif args.field == 'digitization':
            field = 'Equipment Used - Digitization'
        try:
            eqp_list = atbl_rec_aal['fields'][field]
            eqp_list.append(atbl_rec_eqp['id'])
        except KeyError:
            eqp_list = [atbl_rec_eqp['id']]
        atbl_tbl_aal.update(atbl_rec_aal['id'], {field: eqp_list})


def init() -> argparse.Namespace:
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
    parser.add_argument('-f', '--field', dest='field',
                        choices=['asset_action', 'digitization'],
                        help="which field in Asset Action Record to add equipment to\n"
                        "'asset_action' = Equipment Used - Asset Action\n"
                        "'digitization' = Equipment Used - Digitization")
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
