#!/bin/bash
#
# Command line arguments are book directory names used on START
# It will enter within the data directory before doing stuff
# Examples: papers srw tutorials demos BEA8 SSST-7 Meta4NLP2013 MWE2013 LASM2013 EVENTS WVL13 CLfL NLP4ITA2013 WASSA2013
# EMNLP2015 arguments: papers WMT15 WASSA15 DiscoMT15 Louhi15 LSDSem CogACLL VL15 TACL demos tutorials

if [ ! -d "./data" ]; then
   echo "Error: directory ./data does not exist."
   exit 1
elif [ -d "./data/proceedings" ]; then
  echo "Error: a directory named proceeding already exists. please delete it"
  exit 1
fi

cd ./data

while test $# -gt 0; do
   # basename shouldn't be necessary, but just in case since we're doing some RMing
   conf=$(basename $1)
   echo "processing $conf"
   tarball=/tmp/$conf.tgz
   wget -O $tarball --no-check-certificate https://www.softconf.com/emnlp2015/$conf/manager/aclpub/proceedings.tgz
   if [[ $? -ne 0 ]]; then
     echo "Couldn't download $conf's tarball ($tarball), WTF?!"
     test -s $tarball || rm $tarball
     shift
     continue
   fi
   if [ ! -s ./$conf.tgz ] || [ $tarball -nt ./$conf.tgz ]; then 
     echo "Copying a newer version of the file and uncompressing it"
     cp -p $tarball ./$conf.tgz
     rm -rf $conf
     tar -xzf ./$conf.tgz proceedings/{order,meta,final/*/*.txt}
     mv -f proceedings $conf
   else
    echo "Files for $conf do not differ"
   fi
   shift
done
