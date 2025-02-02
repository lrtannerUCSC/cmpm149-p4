import pyhop
import json

#   Basic checks
def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

# Methods
def make_method(name, rule):
    def method(state, ID):
        subtasks = []
        if 'Requires' in rule:
            for req, qty in rule['Requires'].items():
                subtasks.append(('have_enough', ID, req, qty))
        if 'Consumes' in rule:
            for cons, qty in rule['Consumes'].items():
                subtasks.append(('have_enough', ID, cons, qty))
        subtasks.append(('op_{}'.format(name.replace(" ", "_")), ID))
        return subtasks
    return method

def declare_methods(data):
    # some recipes are faster than others for the same product even though they might require extra tools
	# sort the recipes so that faster recipes go first

	# your code here
	# hint: call make_method, then declare the method to pyhop using pyhop.declare_methods('foo', m1, m2, ..., mk)	
	for name, rules in data['Recipes'].items():
		if isinstance(rules, dict):  # Convert single dictionary to list for uniform handling
			rules = [rules]

		sorted_rules = sorted(rules, key=lambda r: r.get('Time', float('inf')))
		methods = [make_method(name, rule) for rule in sorted_rules]
		
		pyhop.declare_methods(f'produce_{name.replace(" ", "_")}', *methods)


#    Operation methods
def op_punch_for_wood(state, ID):
    if state.time[ID] >= 4:
        state.wood[ID] += 1
        state.time[ID] -= 4
        return state
    return False

def op_craft_wooden_pickaxe(state, ID):
    if state.time[ID] >= 1 and state.bench[ID] >= 1 and state.plank[ID] >= 3 and state.stick[ID] >= 2:
        state.wooden_pickaxe[ID] += 1
        state.plank[ID] -= 3
        state.stick[ID] -= 2
        state.time[ID] -= 1
        return state
    return False



def op_wooden_axe_for_wood(state, ID):
    if state.time[ID] >= 2 and state.wooden_axe[ID] >= 1:
        state.wood[ID] += 1
        state.time[ID] -= 2
        return state
    return False

def op_craft_plank(state, ID):
    if state.time[ID] >= 1 and state.wood[ID] >= 1:
        state.plank[ID] += 4
        state.wood[ID] -= 1
        state.time[ID] -= 1
        return state
    return False

def op_craft_stick(state, ID):
    if state.time[ID] >= 1 and state.plank[ID] >= 2:
        state.stick[ID] += 4
        state.plank[ID] -= 2
        state.time[ID] -= 1
        return state
    return False

def op_craft_bench(state, ID):
    if state.time[ID] >= 1 and state.plank[ID] >= 4:
        state.bench[ID] += 1
        state.plank[ID] -= 4
        state.time[ID] -= 1
        return state
    return False



pyhop.declare_operators(
    op_punch_for_wood,
    op_craft_wooden_pickaxe,
    op_wooden_axe_for_wood,
    op_craft_plank,
    op_craft_stick,
    op_craft_bench,
)


def make_operator(rule):
    def operator(state, ID):
        if state.time[ID] < rule['Time']:
            return False 
        if 'Consumes' in rule:
            for cons, qty in rule['Consumes'].items():
                if getattr(state, cons)[ID] < qty:
                    return False 

        if 'Requires' in rule:
            for req, qty in rule['Requires'].items():
                if getattr(state, req)[ID] < qty:
                    return False 

        if 'Consumes' in rule:
            for cons, qty in rule['Consumes'].items():
                getattr(state, cons)[ID] -= qty

        for prod, qty in rule['Produces'].items():
            getattr(state, prod)[ID] += qty

        state.time[ID] -= rule['Time']
        return state
    return operator

def declare_operators(data):
    operators = [make_operator(rule) for name, rules in data['Recipes'].items() for rule in (rules if isinstance(rules, list) else [rules])]
    pyhop.declare_operators(*operators)

# Recipe functions
def produce_wood(state, ID):
    """Choose the best way to gather wood."""
    if state.iron_axe[ID] > 0:
        return [('op_iron_axe_for_wood', ID)]
    elif state.wooden_axe[ID] > 0:
        return [('op_wooden_axe_for_wood', ID)]
    elif state.stone_axe[ID] > 0:
        return [('op_stone_axe_for_wood', ID)]
    else:
        return [('op_punch_for_wood', ID)]  # Default to punching if no tool is available


def produce_plank(state, ID):
    return [('have_enough', ID, 'wood', 1), ('op_craft_plank', ID)]

def produce_stick(state, ID):
    return [('have_enough', ID, 'plank', 2), ('op_craft_stick', ID)]

def produce_bench(state, ID):
    return [('have_enough', ID, 'plank', 4), ('op_craft_bench', ID)]

def produce_wooden_pickaxe(state, ID):
    return [
        ('have_enough', ID, 'bench', 1),
        ('have_enough', ID, 'plank', 3),
        ('have_enough', ID, 'stick', 2),
        ('op_craft_wooden_pickaxe', ID)
    ]




pyhop.declare_methods('produce_plank', produce_plank)
pyhop.declare_methods('produce_stick', produce_stick)
pyhop.declare_methods('produce_bench', produce_bench)
pyhop.declare_methods('produce_wooden_pickaxe', produce_wooden_pickaxe)
pyhop.declare_methods('produce_wood', produce_wood)

# heuristic
def add_heuristic(data, ID):
    # prune search branch if heuristic() returns True
	# do not change parameters to heuristic(), but can add more heuristic functions with the same parameters: 
	# e.g. def heuristic2(...); pyhop.add_check(heuristic2)
    def heuristic(state, curr_task, tasks, plan, depth, calling_stack):
        if state.time[ID] <= 0:
            return True 
        return False

    pyhop.add_check(heuristic)

# set up stuff
def set_up_state(data, ID, time=0):
    state = pyhop.State('state')
    state.time = {ID: time}

    for item in data['Items']:
        setattr(state, item, {ID: 0})

    for item in data['Tools']:
        setattr(state, item, {ID: 0})

    for item, num in data['Initial'].items():
        setattr(state, item, {ID: num})

    return state

def set_up_goals (data, ID):
	goals = []
	for item, num in data['Goal'].items():
		goals.append(('have_enough', ID, item, num))

	return goals

# if __name__ == '__main__':
# 	rules_filename = 'crafting.json'

# 	with open(rules_filename) as f:
# 		data = json.load(f)

# 	state = set_up_state(data, 'agent', time=239) # allot time here
# 	goals = set_up_goals(data, 'agent')

# 	declare_operators(data)
# 	declare_methods(data)
# 	add_heuristic(data, 'agent')

# 	# pyhop.print_operators()
# 	# pyhop.print_methods()

# 	# Hint: verbose output can take a long time even if the solution is correct; 
# 	# try verbose=1 if it is taking too long
# 	pyhop.pyhop(state, goals, verbose=3)
# 	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)



if __name__ == '__main__':
    rules_filename = 'crafting.json'

    with open(rules_filename) as f:
        data = json.load(f)

    test_cases = [
        # (Test Name, Initial State, Goal, Time Constraint)
        ("A", {'plank': 1}, {'plank': 1}, 0),
        ("B", {}, {'plank': 1}, 300),
        ("C", {'plank': 3, 'stick': 2}, {'wooden_pickaxe': 1}, 10),
        #("D", {}, {'iron_pickaxe': 1}, 100),
        # ("E", {}, {'cart': 1, 'rail': 10}, 175),
        # ("F", {}, {'cart': 1, 'rail': 20}, 250),
    ]

    for test_name, initial_state, goal, max_time in test_cases:
        print(f"\nTest {test_name}: Given {initial_state}, Achieve {goal} [Time <= {max_time}]")

        # Set up the state with the given initial items
        state = set_up_state(data, 'agent', time=max_time)
        for item, count in initial_state.items():
            setattr(state, item, {'agent': count})

        # Set up the goals
        goals = set_up_goals({'Goal': goal}, 'agent')

        # Run Pyhop
        result = pyhop.pyhop(state, goals, verbose=3)

        # Check if the test passes based on time constraints and successful execution
        if result is not False and state.time['agent'] >= 0:
            print(f"Test {test_name} PASSED")
        else:
            print(f"Test {test_name} FAILED")
