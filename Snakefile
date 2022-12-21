configfile: "workflow/config.yaml"

rule download_arxiv:
    input:
        "data/"
    output:
        collab="data/arxiv_collaboration.pajek",
        cite="data/arxiv_citation.pajek"
    shell:
        "curl {config[arxiv][collab]} -o {output.collab} && "
        "curl {config[arxiv][cite]} -o {output.cite}"

# if you want to parse the xml locally
rule parse_nsf:
    input:
        expand("data/nsf/xml/{year}/", year=range(config["nsf"]["start_year"], 
                                                  config["nsf"]["end_year"]))
    output:
        "data/nsf/nsf_awards.csv"
    script:
        "scripts/parse_nsf.py"

# if you just want to download a csv for 1993-2003
rule download_parsed_nsf:
    input:
        "data/nsf"
    output:
        "data/nsf/nsf_awards.csv"
    shell:
        "curl -o data/nsf/nsf_awards.csv https://godzillabutnicer.com/wp-content/uploads/2022/12/nsf_awards.csv"

