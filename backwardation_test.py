from util       import get_term_days, term
from statistics import mean, stdev
from sys        import argv

if __name__ == "__main__":

    sym             = argv[1]
    term_days       = get_term_days(sym)
    spreads         = []
    backwardated    = []
    contango        = []

    for i in range(len(term_days)):

        term_day = term_days[i]

        if len(term_day) < 2:

            continue

        spread = term_day[0][term.settle] - term_day[1][term.settle]

        spreads.append(spread)

        if spread > 0:

            backwardated.append(spread)
        
        else:

            contango.append(spread)

    print(sym)
    print(f"samples:      {len(spreads)}")
    print(f"backwardated: {len(backwardated) / len(spreads):0.2f}%")
    print(f"spread avg:   {mean(spreads):0.2f}")
    print(f"spread stdev: {stdev(spreads):0.2f}")

    pass