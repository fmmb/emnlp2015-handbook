# The EMNLP 2015 Handbook

If you're reading this, it's probably because you are about to crate an *ACL handbook. 
I have used the content of Matt Post repositories [ACL 2014](https://github.com/mjpost/acl2014-handbook) and [NAACL 2015](https://github.com/mjpost/naacl15-handbook) as starting points. So, you should start by looking at the information posted there.
The directory structure was kept basically the same, but most scripts have changed either because of EMNLP specific issues or in order to generalize better. 

## Processing steps
Get the information from the softconf START system. Example:
    
    ./scripts/download-proceedings-v2.sh DiscoMT15 Louhi15 LSDSem papers WMT15 WASSA15 CogACLL VL15 tacl-final
 
Search for errors 

    for file in data/*/order; do
      num=$(cat $file | ./scripts/verify_schedule.py > /dev/null 2>&1; echo $?)
      echo "$file\t $num errors"
    done

Generate the bibtex data for each entry in the data directory and create files with the abstracts, one for each paper.

    for name in $(ls data); do
      if [ -d data/$name ]; then
        test -d "auto/$name" && mkdir -p auto/$name
        ./scripts/meta2bibtex.py data/$name/final $name
      fi
    done

Now you can generate the workshop schedules:

    for name in DiscoMT15 Louhi15 LSDSem WMT15 WASSA15 CogACLL VL15; do
      if [ -f data/$name/order ]; then
        test ! -d "auto/$name" && mkdir auto/$name
        echo "Processing $name"
        cat data/$name/order | ./scripts/order2schedule_workshops.py -id $name  > auto/$name/schedule.tex
      else
        echo "data/$name/order not found"
      fi
    done

At later stages of your work you probably will need to add info that has not been properly transferred to your order file, or to correct existing info. That will eventually hapen only for the main conference. For example: during EMNLP 2015, at some point %ext keywords disapeared from the order file, but they are important for getting the paper abstract. So, you will probably need to export info from schedule maker to excel or to google docs, and from there export to a tab separated values file (.TSV). Such .TSV file will contain all the information, so you can use a script to port it to your order file.

    ./scripts/merge-tacl-data/merge-tacl-data.py data/papers/order_original data/papers/schedule.tsv > data/papers/order
  
Now, generate the latex code for the main conference. The "-debug" option can be useful in these scripts

    ./scripts/order2schedule_sessions.py -output_dir auto/papers data/papers/order
    cat data/papers/order | ./scripts/order2schedule_overview.py -output_dir auto/papers

The resulting files must be included in your latex code, using the \input command.

## Some comments about LyX and biblatex

I am using [LyX](http://www.lyx.org) to write my latex code. I find it particularly interesting for tables, but you can stick with latex if you want. In this repository I am keeping both versions, but be aware that the .tex files are being genberated by LyX and may not up-to-date, so look at the modification times.

The handbook requires the usage of [biblatex](https://www.ctan.org/pkg/biblatex). However, current versions of LyX require the following procedure to properly work:

1. Create the file `~/Library/Application\ Support/LyX-2.1/layouts/biblatex.module` with the following content:

        #\DeclareLyXModule{Biblatex-citation-styles}
        #DescriptionBegin
        #A prerequisite for using the biblatex package. This module simply
        #enables the author/year citation styles without actually loading natbib.
        #Biblatex itself needs to be loaded manually. Cf.
        #http://wiki.lyx.org/BibTeX/Biblatex
        #DescriptionEnd
    
        Format 11
    
        # this is biblatex actually
        Provides natbib         1

2. Run Tools->Reconfigure, restart LyX and select the module "Biblatex-citation-styles" from Document->Settings->Modules.

3. choose biber for bib processing

Please take into account that \addbibresource requires an absolute path name


## Notes concerning the data coming from softconf

The publication chairs are responsible for creating the schedule, and consequently, the order files. They will probably use ScheduleMaker, from which you can import the order file. In fact, most of them will probably use excel or google docs to create/change the schedule and then export to ScheduleMaker. You can get all the info, together with the order file, from proceedings.tgz that can be generated from the START system, and will probably be accessed by you using wget or curl.
At some point, changes will mostly focus on the schedule, so downloading a huge file containing everything, just for extracting the order file may not be a good idea. An alternate option is to enter ACLPUB in START, go to the order tab and copy the contents of the order file. However, if the option "Use the Schedule Maker to produce the order file" is selected, you must click "Import order from ScheduleMaker", making sure that the option "Use the Schedule Maker to produce the order file" is remains selected. This way, you can generate the order file, even though it will not be the information source for the proceedings. You can then copy the result content to your local order file. 


## PDF quality: Printing vs. web

After producing the printing version, containing the best quality graphics (18.6Mb), I decided to produce a lightweight version for the web (8.1 Mb) simply by using images with lower quality. The lower quality images were stored in the content/images-web directory. The file content/ads-web.lyx in the alternate lower quality version of the content/ads.lyx file.


## Generating placards, chair names and useful signs

    ./scripts/make_placards.py papers

    ./scripts/make_chair_names.py data/papers/order > misc/placards/chair_names.tex
    pdflatex misc/placards/chair_names.tex
    
    
