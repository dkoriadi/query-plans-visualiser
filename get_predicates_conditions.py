import sqlparse


def get_token_type(token):
    return type(token).__name__.lower()


def get_tokens(node, columns_to_get=[], clauses_to_change=[]):
    clauses_to_search = ['where', 'on', 'group by', 'order by']
    comparisons_to_find = ['<', '<=', '>',  '>=', '!=']
    current_token_type = get_token_type(node)
    if current_token_type in clauses_to_search:
        comparisons = list(filter(lambda token: get_token_type(
            token) == 'comparison', node.tokens))
        for comparison in comparisons:
            tokens_in_comparison = comparison.tokens
            values_of_tokens = list(
                map(lambda token: token.value, tokens_in_comparison))
            if set(values_of_tokens).intersection(set(comparisons_to_find)):
                string_to_keep = ''
                for token_in_comparison in tokens_in_comparison:
                    string_to_keep += token_in_comparison.value
                    if get_token_type(token_in_comparison) == 'identifier':
                        columns_to_get.append(token_in_comparison.value)
                clauses_to_change.append(string_to_keep)

    for sub_token in node.tokens:
        if get_token_type(sub_token).lower() in clauses_to_search:
            get_tokens(sub_token, columns_to_get, clauses_to_change)


def get_var_column(query):
    parsed_query = sqlparse.parse(query)[0]  # this is the 'root' token
    columns_to_get = []
    clauses_to_change = []
    get_tokens(parsed_query, columns_to_get, clauses_to_change)
    print(columns_to_get)
    print(clauses_to_change)
    return columns_to_get, clauses_to_change
