configfile: "workflow/config.yaml"

rule download_nsf_data:
    input:
        "data/"
    output:
        "data/nsf_grants.json"
    script:
        "scripts/download_nsf.py [config.start_year] [config.end_year]"
    