import argparse
import os
import re
import pandas as pd
import sys

def options():
    parser = argparse.ArgumentParser(description="A Python script that will take one or multiple bibtex files as exported by the NASA ADS service and will replace their bib-code with something more usefull.")
    general = parser.add_argument_group('Arguments')
    general.add_argument('-i', '--input', type=str, required=True,
                         help='Input bibtex file, e.g. file1.bib')
    general.add_argument('-o', '--output', type=str, required=True,
                         help='(Path)+filename (e.g. outfile.bib or /path/to/dir/outfile.bib) of output bibtex file. If only a filename is given, will store it in the current directory.')
    return parser.parse_args()

def get_full_bib(file_name):
    """ Input: file_name (string) indicating the path of the input bib file
        Returns: The input bib file as a string """

    with open(file_name, "r") as f:
        return f.read()

def remove_bad_chars(string):
    """ removes all characters that are not '_', 'A-aZ-z' or '0-9'
        returns remaining characters in lowercase
    """
    return re.sub('[^A-Za-z0-9_]+', '', string).lower()

def fix_chime(string):
    """ If it is a chime/frb or chime/pulsar paper, just return chime """

    if "chime" in string.lower():
        key_components = string.split("_")
        key_components[0] = "chime"
        return "_".join(key_components)
    else:
        return string

def get_key(entry):
    """ Get the current key from an entry,
        i.e. extract 'lastname_2021_NatAs' from @ARTICLE{lastname_2021_NatAs, """
    for line in entry.split():
        if "@" in line and "{" in line and "," in line:
            key = line
            break
    if not "{" in key:
        raise ValueError("No '{' found in the key, I was expecting something like '@ARTICLE{lastname_year_publisher,'")
    key = key.split("{")[-1]

    if "," == key[-1]:
        key = key[:-1]
    else:
        raise ValueError("Last char was not ',' - I was expecting something like '@ARTICLE{lastname_year_publisher,'")

    return key

def extend_key_with_vol(key, entry):
    """ If it exists, append the volume to the current key, else return
        the original key """

    vol = ""
    for line in entry.split("\n"):
        if "volume =" in line:
            vol = line
            vol = remove_bad_chars(vol.split("=")[-1])
            break

    if not (vol == ""):
        return "{}_{}".format(key, vol)
    else:
        return key

def extend_key_with_pagenum(key, entry):
    """ If it exists, append the pagenumber to the current key, else return
        the original key """

    pagenum = ""
    for line in entry.split("\n"):
        if "pages =" in line:
            pagenum = line
            pagenum = remove_bad_chars(pagenum.split("=")[-1].split("-")[0])
            break

    if not (pagenum == ""):
        return "{}_{}".format(key, pagenum)
    else:
        return key

def create_bib_entries(file_name):
    """ From a input filename, read the input bib file into a string, extract
        the current keys from the entries and returns [keys], [entries] """

    bib = get_full_bib(file_name).split("\n\n") # split between bib entries
    entries = [x for x in bib if len(x) > 1] # remove empty entries
    keys = []
    for item in entries:
        key = get_key(item)
        key = remove_bad_chars(key)
        key = fix_chime(key)
        keys.append(key)

    return keys, entries


def fix_exceptions(df):
    """ Given a pandas dataframe with the columns 'keys' and 'entries', make a
    custom key if a specified 'doi' is in the entry."""

    # list of exceptions in [(doi1, custom_key1),
    #                        (doi2, custom_key2)]
    excepts = [("10.1093/mnras/stab3051", "james_2021_mnras_zdmdistribution"),\
               ("10.1093/mnrasl/slab117", "james_2021_mnras_frbstarformation"),\
               ("10.1038/s41586-018-0867-7", "chime_2019_natur_lowfreqobs"),\
               ("10.1038/s41586-018-0864-x", "chime_2019_natur_secondrepeatfrb"),\
               ("10.1038/s41586-020-2398-2", "chime_2020_natur_periodicactivity"),\
               ("10.1038/s41586-020-2863-y", "chime_2020_natur_galacticfrb")]

    for index, row in df.iterrows():
        for e in excepts:
            if e[0] in row["entries"]:
                df.loc[index, "keys"] = e[-1]

    return df


def create_df(keys, entries):
    """ Given a list of keys and entries, create a pandas dataframe. Next,
        To avoid duplicates add volume numbers to conflicting keys. If there are
        still issues, also add the page number. Returns the dataframe with the headers
        'final_key' (which are all unique) and the corresponding original entries. """

    df = pd.DataFrame(data={"keys":keys,\
                       "entries":entries})

    df = fix_exceptions(df)
    df = df.sort_values(by=["keys"])

    # for the conflicting keys, add a new column with the keys + volume number
    df_dup = df[df.duplicated(subset=['keys'], keep=False)].copy()
    df_dup["keys_vol"] = ""
    for i, row in df_dup.iterrows():
        row["keys_vol"] = extend_key_with_vol(row["keys"], row["entries"])

    # if there are still duplicate keys, also add pagenumber
    df_dup_ext = df_dup[df_dup.duplicated(subset=['keys_vol'], keep=False)].copy()
    df_dup_ext["keys_vol_pagenum"] = ""
    for i, row in df_dup_ext.iterrows():
        row["keys_vol_pagenum"] = extend_key_with_pagenum(row["keys_vol"], row["entries"])

    # if there is still an error I suspect that there are duplicate entries in the
    # input bib file
    if df_dup_ext[df_dup_ext.duplicated(subset=['keys_vol_pagenum'], keep=False)].shape[0] > 0:
        df_error = df_dup_ext[df_dup_ext.duplicated(subset=['keys_vol_pagenum'], keep=False)].copy()
        print("Found bib entries with the same author, year, journal, volume and pages")
        print("Printing the conflicting bib entries and exiting program.")
        print("Please edit the input bib file and change/remove the duplicate")
        for i, row in df_error.iterrows():
            print(row["entries"])
        sys.exit()

    # create three datasets with the shortests keys possible without duplicates
    # and put those in a new column with the same headername
    df_ayj = df[~df['keys'].isin(df_dup['keys'])].copy() # ayj = author year journal
    df_ayjv = df_dup[~df_dup['keys_vol'].isin(df_dup_ext['keys_vol'])].copy() # ayjv = author year journal volume
    df_ayjvp = df_dup_ext.copy()

    df_ayj["final_key"] = df_ayj["keys"]
    df_ayjv["final_key"] = df_ayjv["keys_vol"]
    df_ayjvp["final_key"] = df_ayjvp["keys_vol_pagenum"]

    assert df.shape[0] == (df_ayj.shape[0] + df_ayjv.shape[0] + df_ayjvp.shape[0])
    assert df_ayj.shape[0] == (df.shape[0] - df_dup.shape[0])

    # append the three dataframes (some can be empty, but that is not a problem)
    df_final = pd.concat([df_ayj, df_ayjv, df_ayjvp])
    df_final = df_final.sort_values(by=["final_key"])

    return df_final

def update_key(key, entry):
    """Function which updates the first line of a bib entry given a new key.
    e.g., turns:
    @ARTICLE{Kirsten_2020_NatAs,
       author = {{Kirsten}, F. and {Snelders}, M ...
       ...
    }
    into:
    @ARTICLE{key,
       author = {{Kirsten}, F. and {Snelders}, M ...
       ...
    }

    Args:
        key: A string containing a new key.
        entry: A string which needs to be updated

    Returns:
        An updated bib entry in string format.

    """

    components = entry.split("\n")
    first_line = components[0]
    new_line = first_line.split("{")[0] + "{" + key + ","
    components[0] = new_line

    return "\n".join(components)

def write_new_bib(df, outfile):
    """Function which writes a pandas dataframe to a bibtex file.

    Args:
        df: A pandas dataframe containing the headers 'final_key' and 'entries'
        outfile: A string indicating the output (path+)filename.

    Returns:
        Nothing.

    """

    # create the outfile
    with open(outfile, "w") as f:
        for i, row in df.iterrows():
            key, entry = row["final_key"], row["entries"]
            # update the first line of the original entry
            new_entry = update_key(key, entry)
            f.write(new_entry)
            f.write("\n\n")

    return

def main(args):
    """To do; write docstring"""

    infile = args.input
    outfile = args.output

    # it's not allowed to overwrite the input bib file
    assert outfile != infile

    key, entries = create_bib_entries(infile)
    df = create_df(key, entries)
    write_new_bib(df, outfile)

if __name__ == "__main__":
    args = options()
    main(args)
