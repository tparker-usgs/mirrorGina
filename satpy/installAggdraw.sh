#!/bin/sh

wget http://effbot.org/media/downloads/aggdraw-1.1-20051010.zip 
unzip aggdraw-1.1-20051010.zip
cd aggdraw-1.1-20051010

patch -p1 <<EOF
--- aggdraw-1.1-20051010/setup.py   2017-05-19 19:55:33.400382012 +0000
+++ aggdraw-1.1-20051010-tweaked/setup.py   2017-05-19 19:55:36.165382012 +0000
@@ -18,7 +18,7 @@
 VERSION = "1.1-20051010"
 
 # tweak as necessary
-FREETYPE_ROOT = "../../kits/freetype-2.1.10"
+FREETYPE_ROOT = "/usr"
 
 if not os.path.isdir(FREETYPE_ROOT):
     print "===", "freetype support disabled"
EOF

export CFLAGS="-fpermissive"
python setup.py install


