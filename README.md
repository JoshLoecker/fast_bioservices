# Fast Bioservices

## Inspiration
This package is inspired by [cokelear/bioservices](https://github.com/cokelaer/bioservices). It currently supports functions from [biodbnet](https://biodbnet-abcc.ncifcrf.gov/), but much faster.

## Known Issues
If too many requests are attempted, rate limiting and IP-based blockin for an unknown about of time may occur. There is a hard limit of 10 requests per second built into the `biodbnet` component of this package, based on [this change](https://github.com/cokelaer/bioservices/blob/1bdf220f38bdd325234173ae16ab385c9b6d364c/doc/ChangeLog.rst?plain=1#L393-L394)

