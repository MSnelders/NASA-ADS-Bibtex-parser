# NASA-ADS-Bibtex-parser
A simple python script that will change the (not-as-useful) bib-keys generated by the ADS service into something more useful. 

# Useage:  
Go to the settings of your ADS account and place "%1H_%Y_%q" under "BibTeX Default Export Key Format". Next, export your ADS library. Finally, use 'python bibparser.py -i <infile.bib> -o <outfile.bib>'

# Explanation:

Do you use the NASA ADS (Astrophysics Data System) for your papers but are you frustrated that the default keys are not exactly useful? Look no further. With some instructions in your ADS account and this script you can turn all those keys into something more useful. 

As an example, the default settings of the ADS service generates the following bibtex-entry for this article (with the **key in bold**, https://ui.adsabs.harvard.edu/abs/2020NatAs.tmp..232K/abstract):  
  
@ARTICLE{**2020NatAs.tmp..232K**,  
       author = {{Kirsten}, F. and {Snelders}, M.~P. and {Jenkins}, M. and {Nimmo}, K. and {van den Eijnden}, J. and {Hessels}, J.~W.~T. and {Gawro{\'n}ski}, M.~P. and {Yang}, J.},  
        title = "{Detection of two bright radio bursts from magnetar SGR 1935 + 2154}",  
      journal = {Nature Astronomy},  
     keywords = {Astrophysics - High Energy Astrophysical Phenomena},  
         year = 2020,  
        month = nov,  
          doi = {10.1038/s41550-020-01246-3},  
archivePrefix = {arXiv},  
       eprint = {2007.05101},  
 primaryClass = {astro-ph.HE},  
       adsurl = {https://ui.adsabs.harvard.edu/abs/2020NatAs.tmp..232K},  
      adsnote = {Provided by the SAO/NASA Astrophysics Data System}  
}  


It is actually possible to change the settings in your ADS account to generate more useful keys. To do so, go to https://ui.adsabs.harvard.edu/user/settings/application and update your "BibTeX Default Export Key Format". If this is changed to "%1H_%Y_%q" the generated keys will now be in the format of "Lastname_year_joural", e.g.:  
@ARTICLE{Kirsten_2020_NatAs,

While this is already a huge step forward it can cause some issues; it is now possible that multiple entries have the same key. This happens for example with:  
  
@ARTICLE{Chime/FrbCollaboration_2020_Natur,  
       author = {{Chime/Frb Collaboration} and {Amiri}, M. and {Andersen}, B.~C. and {Bandura}, K.~M. and {Bhardwaj}, M. ...},  
        title = "{Periodic activity from a fast radio burst source}",  
      journal = {Nature},  
         year = 2020,  
        month = jun,  
       volume = {582},  
        pages = {351-355},  
}  

and  

@ARTICLE{CHIME/FRBCollaboration_2020_Natur,  
       author = {{CHIME/FRB Collaboration} and {Andersen}, B.~C. and {Bandura}, K.~M. and {Bhardwaj}, M. and ...},  
        title = "{A bright millisecond-duration radio burst from a Galactic magnetar}",  
      journal = {Nature},  
         year = 2020,  
        month = nov,  
       volume = {587},  
        pages = {54-58},  
}  


What this script does is the following:
1. Puts everything into lowercase, Kirsten_2020_NatAs -> kirsten_2020_natas
1. Removes all special characters (except underscores), @ARTICLE{in'tZand_2015_arXix -> @ARTICLE{intzand_2015_arxix 
1. Any paper written by the CHIME/FRBCollaboration gets replaced with chime, CHIME/FRBCollaboration_2020_Natur -> chime_2020_natur
1. In case there are conflincting (duplicate) keys
   1. First adds the volume to the key (if it exists), CHIME/FRBCollaboration_2020_Natur -> chime_2020_natur_587
   1. If there is still a conflict (e.g. https://ui.adsabs.harvard.edu/abs/2017ApJ...844..162T/abstract and https://ui.adsabs.harvard.edu/abs/2017ApJ...844...65T/abstract), also adds the pagenumer to the key, Thompson_2017_ApJ -> thompson_2017_apj_844_65
