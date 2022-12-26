import pandas as pd
import xml.etree.ElementTree as et
from glob import glob
from tqdm import tqdm

# This script assumes that user has downloaded years 1993-2003 from
# https://nsf.gov/awardsearch/download.jsp
# and have unzipped them into data/nsf/xml/

# start and end years for analysis
start_year = 1999
end_year = 2019

# a little helper function for parsing the xml by tag
def parse(root, tag):
    found = root.find(tag)
    if found is not None:
        return found.text
    else:
        return ""


# now we have to handle all of these fuxking xml files
rows = []
for year in range(start_year, end_year + 1):
    bad_reads = 0
    year_files = glob(f"data/nsf/xml/{year}/*.xml")
    for fxml in year_files:

        # some of the xml won't parse and thats none of my business
        try:
            tree = et.parse(fxml)
        except:
            bad_reads +=1

        award = tree.getroot()[0]

        # pull out the stuff we think is interesting. ireally hate xml
        row = {}
        if award.find("Investigator") is not None:
            pi = award.find("Investigator")
            row["first_name"] = parse(pi, "FirstName")
            row["middle_initial"] = parse(pi, "PI_MID_INIT")
            row["last_name"] = parse(pi, "LastName")

        row["award_type"] = parse(award, "TRAN_TYPE")
        row["award_amount"] = parse(award, "AwardAmount")
        row["title"] = parse(award, "AwardTitle")
        row["agency"] = parse(award, "AGENCY")
        row["award_start"] = parse(award, "AwardEffectiveDate")
        row["award_end"] = parse(award, "AwardExpirationDate")

        if award.find("Institution") is not None:
            inst = award.find("Institution")
            row["institution"] = parse(inst, "Name")
            row["country"] = parse(inst, "CountryName")
            row["state"] = parse(inst, "StateName")

        # add to big list of rows
        rows.append(row)

    print(f"Bad Reads for {year}: {bad_reads}")
    
# convert to dataframe
nsf_df = pd.DataFrame(rows)
nsf_df.to_csv(f"data/nsf/nsf_awards.csv")