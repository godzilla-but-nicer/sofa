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

rule parse_nsf:
    input:
        expand("data/nsf/xml/{year}/", year=range(config["nsf"]["start_year"], 
                                                  config["nsf"]["end_year"])
    output:
        "data/nsf/nsf_awards.csv"
    script:
        "scripts/parse_nsf.py"
    