import argparse
import pandas as pd
import requests
import yaml

# handle command line interface. overkill for sure
ap = argparse.ArgumentParser("NSF Award Downloader",
                             description="Downloads all NSF award data from start to end year")
ap.add_argument("start_year")
ap.add_argument("end_year")
ap.add_argument("-v", "--verbose",
                action="store_true")
args = ap.parse_args()

# NSF limits to 200 responses from the api so we need to break up the dates
# into chunks. Months seems reasonable.

# convert to valid dates for the api
start_date = f"01/01/{args.start_year}"
end_date = f"02/01/{args.end_year}"

# GET nsf data. https://www.research.gov/common/webapi/awardapisearch-v1.htm
url_base = "http://api.nsf.gov/services/v1/awards.json"

print_fields = """id,agency,awardeeCity,awardeeName,awardeeStateCode,coPDPI,
                  date,estimatedTotalAmt,fundsObligatedAmt,title,piFirstName,
                  piMiddeInitial,piLastName"""

parameters = {"dateStart": start_date,
              "dateEnd": end_date,
              "printFields": print_fields}

data = requests.get(url_base, params=parameters)

# print something about whether it worked
if args.verbose:
    not_error = "serviceNotification" not in data.json()["response"].keys()

    if not_error:
        response_type = "Success!"
    else:
        # conforming to https://www.research.gov/common/webapi/awardapisearch-v1.htm
        response_type = data.json()["response"]["serviceNotification"][0]["notificationMessage"]

    print(f"GET {start_date} - {end_date}: {response_type}")

# save as dataframe
nsf_df = pd.DataFrame(data.json()["response"]["award"])
nsf_df.to_csv("data/test.csv")
