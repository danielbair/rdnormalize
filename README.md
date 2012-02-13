rdnormalize.py
==============

rdnormalize is a python script to normalize carts in a rivendell library to a 
given loudness level as per the EBU r128 loundness standard. 

Requires: libebur128 from https://github.com/jiixyj/libebur128

usage: rdnormalize.py [-h] [-v] [-l LUFS] [-g GROUP] [--drop-columns] [--debug]

Normalize cuts in a group.

optional arguments:
  -h, --help      show this help message and exit
  -v              Turn on verbose output
  -l LUFS         Target loudness level. Defaults to the recommended -23.
  -g GROUP        Group to set gain levels in. Use 'ALL' to include all
                  groups.
  --drop-columns  Remove extra columns added to your database by this script.
                  This will not restore your previous gain levels and will
                  require previously normalized cuts to be re-analyzed if you
                  run this script again.
  --debug         Turn on debug output

The author recommends to import audio at a peak normalization of -1 dBFS when
using the WAV format, then use this script to lower the playback gain level.
See http://tech.ebu.ch/loudness for more information.

Example: rdnormalize.py -g ALL -l -12 -v

