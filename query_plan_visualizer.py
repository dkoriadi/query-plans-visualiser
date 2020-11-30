import json

from anytree import Node, RenderTree


class Cost(float):
    """
    A class that wraps around float for all cost values
    """
    def __new__(cls, x):
        x = max(x, 0)  # cost can never be negative
        x = round(x, 2)  # set to 2 d.p. for easy representation
        return super().__new__(cls, x)


def _generate_ids_and_cost(current_plan, name_counter=None):
    """
    Traverse through a subplan and put a human-readable ID on each subplan root
    Also gets the cost of current plan's root operator itself, without child costs
    """
    # Start a new dict if this is a non-recursive call
    if name_counter is None:
        name_counter = {}
    current_plan_name = current_plan.get('Node Type')

    # increment is used to prevent duplicate names
    current_name_increment = name_counter.get(current_plan_name, 1)

    # Use the plan's name and its current increment to generate a human readable ID
    current_plan['id'] = "{}_{}".format(
        current_plan_name, current_name_increment)

    # increment the counter
    name_counter[current_plan_name] = current_name_increment + 1

    # traverse children plans and do the same
    children_plans = current_plan.get('Plans')
    children_costs = 0
    if children_plans:
        for child_plan in children_plans:
            _generate_ids_and_cost(child_plan, name_counter)
            children_costs += Cost(child_plan.get('Total Cost'))
    current_plan_cost = current_plan.get('Total Cost') - children_costs
    # Get cost of current operator
    current_plan['cost'] = Cost(current_plan_cost)


def _generate_children_nodes(current_plan, children_plans, plan_nodes):
    """
    Traverse through a subplan and place children nodes
    """
    current_plan_id = current_plan.get('id')

    if (not children_plans):  # if this plan is a leaf plan
        current_plan_relation_name = current_plan.get('Relation Name')
        if (current_plan_relation_name):
            current_plan_node = plan_nodes[current_plan_id]
            plan_nodes[current_plan_relation_name] = Node(
                current_plan_relation_name, parent=current_plan_node, is_relation=True)
        return

    # this has to be pre-order traversal or the plan generated will not be accurate
    for child_plan in children_plans:
        child_plan_id = child_plan.get('id')
        plan_nodes[child_plan_id] = Node(
            child_plan_id, parent=plan_nodes[current_plan_id], is_relation=False, raw_plan=child_plan)
        grandchildren_plans = child_plan.get('Plans')
        _generate_children_nodes(child_plan, grandchildren_plans, plan_nodes)


def visualize_query_plan(query_plan):
    """
    Provide a query plan as a JSON array with only one element
    """
    # Get the first plan
    first_plan = query_plan[0].get('Plan')

    # Store the total cost of the plan first
    plan_total_cost = first_plan.get('Total Cost', 0)

    # generate a unique ID and get cost for each operator in the query plan
    _generate_ids_and_cost(first_plan)

    # Get the ID of the first plan
    first_plan_id = first_plan.get('id')

    # Initialize a dictionary to store all nodes in the query plan
    plan_nodes = {}

    # Store first plan in the dictionary
    plan_nodes[first_plan_id] = Node(
        first_plan_id, is_relation=False, raw_plan=first_plan)

    # Get the children of the first plan
    children_plans = first_plan.get('Plans')

    # Traverse the children with the context of first plan
    _generate_children_nodes(first_plan, children_plans, plan_nodes)

    # Get the node for the first plan
    first_plan_node = plan_nodes[first_plan_id]

    # print(RenderTree(first_plan_node))
    # Print the plan as a normal Python string for fewer dependencies
    # Optionally, the plan can be converted and exported as an image for visualisation 
    # (requires Graphviz to be installed)
    szQEPTree = str()
    for pre, _, node in RenderTree(first_plan_node):
        if (not node.is_relation):
            current_operator_name = node.raw_plan.get('Node Type')
            current_node_cost = node.raw_plan.get('cost')
            current_node_cardinality = node.raw_plan.get('Plan Rows')
            current_node_filter = node.raw_plan.get("Filter")
            node_label = "{} || Cost: {} || Cardinality: {} || Filter: {}".format(
                current_operator_name, current_node_cost, current_node_cardinality, current_node_filter)
            szQEPTree += "{}{}\n".format(pre, node_label)
        else:
            szQEPTree += "{} Relation: {}\n".format(pre, node.name)
    return szQEPTree


if __name__ == '__main__':
    # Get the sample query plan as a Python object
    with open('sample_query_plan.json') as f:
        query_plan = json.load(f)

    # Test the visualizer
    szQEPTree = visualize_query_plan(query_plan)
    print(szQEPTree)
