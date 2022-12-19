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

rule download_nsf_data:
    input:
        "data/"
    output:
        "data/nsf_grants.json"
    script:
        # script takes arguments: api-url start_year end_year
        "scripts/download_nsf.py {config.nsf.start_year} {config.nsf.end_year}"
    