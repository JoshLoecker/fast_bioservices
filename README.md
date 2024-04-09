# Fast Bioservices

## Inspiration
This package is inspired by [cokelear/bioservices](https://github.com/cokelaer/bioservices). It currently supports functions from [biodbnet](https://biodbnet-abcc.ncifcrf.gov/), but much faster.


## Planned Additions
In theory, I would like to duplicate the modules offered by coklear/bioservices. As this may not be possible, the most useful (to me) modules are listed below

- [ ] [BiGG Database](http://bigg.ucsd.edu/)
- [X] [bioDBnet](https://biodbnet-abcc.ncifcrf.gov/)
- [ ] [BioModels](https://www.ebi.ac.uk/biomodels/)
- [ ] [KEGG](https://www.kegg.jp/kegg/rest/)

## Known Issues
If too many requests are attempted, rate limiting and IP-based blockin for an unknown about of time may occur. There is a hard limit of 10 requests per second built into the `biodbnet` component of this package, based on [this change](https://github.com/cokelaer/bioservices/blob/1bdf220f38bdd325234173ae16ab385c9b6d364c/doc/ChangeLog.rst?plain=1#L393-L394)