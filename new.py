from    datetime    import  datetime
import  numpy       as      np
import  polars      as      pl
from    sys         import  argv
from    time        import  time
from    util        import  get_futc


pl.Config.set_tbl_cols(-1)
pl.Config.set_tbl_rows(-1)


if __name__ == "__main__":

    t0      = time()
    years   = int(argv[1])
    sym     = argv[2]
    start   = f"{(datetime.now().year - years)}-01-01"
    df      = get_futc(sym, start)

    print(f"{time() - t0:0.1f}s")

    pass
    
