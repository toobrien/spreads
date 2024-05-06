from    math                    import  log
from    numpy                   import  cumsum, mean, std
import  plotly.graph_objects    as      go
from    sys                     import  argv
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
    avg_a   = mean(pcts)
    stdev_a = std(pcts)

    print(f"avg (ari):      {avg_a:0.2f}")
    print(f"std (ari):      {stdev_a}")
    print(f"avg (ari_y):    {avg_a * 256:0.2f}")
    print(f"std (ari_y):    {stdev_a * 16:0.2f}")
    print(f"avg (log):      {avg:0.4f}")
    print(f"std (log):      {stdev:0.4f}")
    print(f"avg (log_y):    {avg * 256:0.4f}")
    print(f"std (log_y):    {stdev * 16:0.4f}")
    print(f"days:           {len(logs)}")
    print(f"years:          {len(logs) / 256:0.2f}\n")
    print(f"{time() - t0:0.1f}s")

    pass
