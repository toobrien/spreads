from    math                    import  log
from    numpy                   import  cumsum, mean, std
import  plotly.graph_objects    as      go
from    sys                     import  argv
from    scipy.stats             import  kurtosis, skew
from    time                    import  time
from    util                    import  get_continuous


if __name__ == "__main__":

    t0      = time()
    symbol  = argv[1]
    recs    = get_continuous(symbol, "1900-01-01", "2100-01-01", 0)
    y       = [ r[4] for r in recs ]
    text    = [ r[1] for r in recs ]
    logs    = [ log(y[i] / y[i - 1]) for i in range(1, len(y)) ]
    pcts    = [ y[i] / y[i - 1] - 1 for i in range(1, len(y)) ]
    y_      = cumsum(logs)
    
    '''
    fig = go.Figure()

    fig.add_trace(
        {
            "x":    list(range(len(y))),
            "y":    y,
            "text": text,
            "name": "es"
        }
    )

    fig.add_trace(
        {
            "x":    list(range(len(y_))),
            "y":    y_,
            "text": text[1:]
        }
    )

    fig.show()
    '''

    avg     = mean(logs)
    stdev   = std(logs)
    kur     = kurtosis(logs)
    ske     = skew(logs)
    avg_a   = mean(pcts)
    stdev_a = std(pcts)

    print(f"symbol:         {symbol}")
    print(f"start:          {text[0]}")
    print(f"end:            {text[-1]}")
    print(f"days:           {len(logs)}")
    print(f"years:          {len(logs) / 256:.2f}\n")

    print(f'{"":15}{"daily":>15}{"annual":>15}\n')

    print("arithmetic\n")

    print(f'{"avg:":15}{avg_a:15.4f}{avg_a * 256:15.4f}')
    print(f'{"std:":15}{stdev_a:15.4f}{stdev_a * 16:15.4f}\n')
    
    print("geometric\n")

    print(f'{"avg:":15}{avg:15.4f}{avg * 256:15.4f}')
    print(f'{"std:":15}{stdev:15.4f}{stdev * 16:15.4f}')
    print(f'{"kurtosis:":15}{kur:15.4f}{kur / 256:15.4f}')
    print(f'{"skew:":15}{ske:15.4f}{ske / 16:15.4f}\n')

    print(f"{time() - t0:0.1f}s")

    pass