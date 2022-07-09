from enum       import IntEnum
from math       import log
from statistics import mean
from sys        import argv
from typing     import List
from util       import filter_by_sea, get_db, get_term_days, term


DB          = get_db()
DATE_FMT    = "%Y-%m-%d"


class reg_record(IntEnum):

    date         = 0
    contract_val = 1
    spread_val   = 2


def regress(mode: str, reg_records: List):

    differenced = []

    # difference series

    if mode == "abs":

        for i in range(1, len(reg_records)):

            differenced.append(
                (
                    reg_records[i][reg_record.date],
                    reg_records[i][reg_record.contract_val] - reg_records[i - 1][reg_record.contract_val],
                    reg_records[i][reg_record.spread_val] - reg_records[i - 1][reg_record.spread_val]
                )
            )

    elif mode == "pct":

        for i in range(1, len(reg_records)):

            differenced.append(
                (
                    reg_records[i][reg_record.date],
                    log(reg_records[i][reg_record.contract_val] / reg_records[i - 1][reg_record.contract_val]),
                    log(reg_records[i][reg_record.spread_val] / reg_records[i - 1][reg_record.spread_val])
                )
            )

    # alpha, beta

    x       = [ r[reg_record.contract_val] for r in differenced ]
    y       = [ r[reg_record.spread_val] for r in differenced ]
    xy      = [ x_i * y_i for x_i, y_i in zip(x, y) ]
    x_2     = [ x_i**2 for x_i in x ]
    
    x_mu    = mean(x)
    y_mu    = mean(y)
    xy_mu   = mean(xy)
    x_2_mu  = mean(x_2)

    beta    = (x_mu * y_mu - xy_mu) / (x_mu**2 - x_2_mu)
    alpha   = y_mu - beta * x_mu

    # coefficient of determination

    sq_err_model    = [ (y_i - (beta * x_i))**2 for x_i, y_i in zip(x, y)   ]
    sq_err_mean     = [ (y_i - y_mu)**2         for y_i      in y           ]
    
    r_2             = 1 - (sum(sq_err_model) / sum(sq_err_mean))

    return differenced, alpha, beta, r_2


def app(
    mode:           str,
    symbol:         str,
    contracts:      List, 
    start:          str, 
    end:            str,
    num_records:    int
):

    term_days   = get_term_days(DB, symbol, start, end)
    filtered    = filter_by_sea(term_days, contracts)
    reg_records = []

    # calculate settlements

    if len(contracts) == 3:

        # reverse calendar
        
        for term_day in filtered:

            reg_records.append(
                (
                    term_day[0][term.date],
                    term_day[0][term.settle],
                    term_day[1][term.settle] - term_day[2][term.settle]
                )
            )

    elif len(contracts) == 4:

        # butterfly

        for term_day in filtered:

            reg_records.append(
                (
                    term_day[0][term.date],
                    term_day[0][term.settle],
                    term_day[1][term.settle] - 2 * term_day[2][term.settle] + term_day[3][term.settle]
                )
            )

    # regression calculation

    differenced, alpha, beta, r_2 = regress(mode, reg_records)

    # display output

    print("alpha:".ljust(12), f"{alpha:12.3f}")
    print("beta:".ljust(12), f"{beta:12.3f}")
    print("r^2:".ljust(12), f"{r_2:12.3f}\n")

    if num_records == -1:

        filtered = filtered[1:]

    elif num_records == 0:

        return

    else: 

        filtered    = filtered[-num_records - 1:]
        differenced = differenced[-num_records:]

    print(
        "date".rjust(12),
        "c_stl".rjust(12),
        "s_stl".rjust(12),
        "c_chg".rjust(12),
        "s_chg".rjust(12),
        "\n"
    )

    for r_rec, d_rec in zip(reg_records, differenced):

        print(
            r_rec[reg_record.date].rjust(12),
            f"{r_rec[reg_record.contract_val]:12.3f}",
            f"{r_rec[reg_record.spread_val]:12.3f}",
            f"{d_rec[reg_record.contract_val]:12.3f}",
            f"{d_rec[reg_record.spread_val]:12.3f}"
        )

    pass


if __name__ == "__main__":

    mode        = argv[1]
    contract    = argv[2]   # HON2022
    spread      = argv[3]   # HON2022:HOQ2022
    start       = argv[4]   # yyyy-mm-dd
    end         = argv[5]   # yyyy-mm-dd
    num_records = -1

    if len(argv) == 7:
    
        num_records = int(argv[6])

    symbol    = contract[0:-5]
    contracts = [ contract, *(spread.split(":")) ]
    contracts = [ 
        (
            contract[-5:-4],    # month
            contract[-4:]       # year
        )
        for contract in contracts
    ]

    for i in range(1, len(contracts)):

        cur  = contracts[i]
        prev = contracts[i - 1]

        if  cur[1] < prev[1] or \
            (cur[1] == prev[1] and cur[0] < prev[0]):

            print("error: contracts must be in chronological order")
            exit(1)

    app(mode, symbol, contracts, start, end, num_records)