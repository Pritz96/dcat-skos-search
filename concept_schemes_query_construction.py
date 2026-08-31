from SPARQLBurger.SPARQLQueryBuilder import *
import os

VALID_FIELDS = {
    "notation": "?notation",
    "prefLabel": "?prefLabel",
    "definition": "?definition",
}


def escape_literal(value: str) -> str:
    """Escape a string so it's safe to embed inside a SPARQL string literal."""
    return value.replace("\\", "\\\\").replace('"', '\\"')


def build_concept_scheme_query(dcat_uris, search_term="", traverse=True, search_fields=None, comment=""):
    """
    search_fields: list of any combination of "notation", "prefLabel", "definition".
                   Defaults to all three if None. Controls which fields the
                   search_term is matched against -- results are still
                   returned with all three fields regardless.
    """
    if search_fields is None:
        search_fields = list(VALID_FIELDS.keys())

    invalid = set(search_fields) - VALID_FIELDS.keys()
    if invalid:
        raise ValueError(f"Unknown search field(s): {invalid}. Valid options: {list(VALID_FIELDS.keys())}")
    if not search_fields:
        raise ValueError("At least one search field must be provided")

    query = SPARQLSelectQuery(distinct=True)
    query.add_prefix(Prefix(prefix="skos", namespace="http://www.w3.org/2004/02/skos/core#"))
    query.add_prefix(Prefix(prefix="dcat", namespace="http://www.w3.org/ns/dcat#"))
    query.add_variables(variables=["?resource", "?notation", "?prefLabel", "?definition"])

    where = SPARQLGraphPattern()
    path = "(dcat:dataset|dcat:catalog)*" if traverse else "(dcat:dataset|dcat:catalog)"

    where.add_triples(triples=[
        Triple(subject="?dcatUri", predicate=path, object="?resource"),
        Triple(subject="?resource", predicate="a", object="skos:ConceptScheme"),
    ])

    uri_list = ", ".join(f"<{uri}>" for uri in dcat_uris)
    where.add_filter(Filter(expression=f"?dcatUri IN ({uri_list})"))

    for prop, var in [("skos:notation", "?notation"),
                       ("skos:prefLabel", "?prefLabel"),
                       ("skos:definition", "?definition")]:
        opt = SPARQLGraphPattern(optional=True)
        opt.add_triples(triples=[Triple(subject="?resource", predicate=prop, object=var)])
        where.add_nested_graph_pattern(opt)

    where.add_binding(Binding(value=f'"{escape_literal(search_term)}"', variable="?searchTerm"))

    conditions = [
        f"CONTAINS(LCASE(STR({VALID_FIELDS[field]})), LCASE(?searchTerm))"
        for field in search_fields
    ]
    where.add_filter(Filter(expression=" || ".join(conditions)))

    query.set_where_pattern(graph_pattern=where)

    query_text = query.get_text()   # assign first

    if comment:
        comment_block = "\n".join(f"# {line}" for line in comment.splitlines())
        query_text = f"{comment_block}\n{query_text}"

    return query_text   # return the variable, not query.get_text() again

    return query.get_text()

def save_query(query_text, filename, folder="concept_scheme_queries"):
    os.makedirs(folder, exist_ok=True)
    if not filename.endswith(".rq"):
        filename += ".rq"
    path = os.path.join(folder, filename)
    with open(path, "w") as f:
        f.write(query_text)
    return path


q1=build_concept_scheme_query(
    dcat_uris=["http://environment.data.gov.uk"],
    search_term="rate",
    search_fields=["notation", "definition"], comment="Search for all ConceptSchemes under the top level based on notation and definition"
)
save_query(q1,"q1")


q2=build_concept_scheme_query(
    dcat_uris=["http://environment.data.gov.uk"],
    search_term="nitrate",
    search_fields=["prefLabel"], comment="Search for all ConceptSchemes under the top level based on prefLabel"
)
save_query(q2,"q2")


q3=build_concept_scheme_query(
    dcat_uris=["http://environment.data.gov.uk"],
    search_term="mean", comment = "Search for all ConceptSchemes under the top level based on notation, prefLabel and definition"
)
save_query(q3,"q3")

q4=build_concept_scheme_query(
    dcat_uris=["http://environment.data.gov.uk"],
    search_term="rate",
    traverse=False,
    search_fields=["notation", "definition"], comment="Search for all ConceptSchemes AT THE TOP LEVEL ONLY based on notation and definition"
)
save_query(q4,"q4")

q5=build_concept_scheme_query(
    dcat_uris=["http://environment.data.gov.uk/water-quality", "http://environment.data.gov.uk/ecology-and-fish"],
    search_term="rate",
    traverse=True,
    search_fields=["notation", "definition"], comment="Search for all ConceptSchemes under water-quality OR ecology-and-fish (with downwards traversal)"
)
save_query(q5,"q5")

q6=build_concept_scheme_query(
    dcat_uris=["http://environment.data.gov.uk/water-quality", "http://environment.data.gov.uk/ecology-and-fish"],
    search_term="rate",
    traverse=False,
    search_fields=["notation", "definition"], comment="Search for all ConceptSchemes under water-quality OR ecology-and-fish (without downwards traversal)"
)
save_query(q6,"q6")