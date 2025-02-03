import pyhop
import json

def check_enough (state, ID, item, num):
	if getattr(state,item)[ID] >= num: return []
	return False

def produce_enough (state, ID, item, num):
	return [('produce', ID, item), ('have_enough', ID, item, num)]

pyhop.declare_methods ('have_enough', check_enough, produce_enough)

def produce (state, ID, item):
	return [('produce_{}'.format(item), ID)]

pyhop.declare_methods ('produce', produce)

def make_method (name, rule):
	def method (state, ID):
		subtasks = []

		if "Requires" in rule:
			for tool, num in rule["Requires"].items():
				subtasks.append(('have_enough', ID, tool, num))

		if "Consumes" in rule:
			for item, num in rule["Consumes"].items():
				subtasks.append(('have_enough', ID, item, num))

		subtasks.append(('op_' + name.replace(" ", "_"), ID))

		return subtasks

	return method

def declare_methods (data):
	# some recipes are faster than others for the same product even though they might require extra tools
	# sort the recipes so that faster recipes go first

	# your code here
	# hint: call make_method, then declare the method to pyhop using pyhop.declare_methods('foo', m1, m2, ..., mk)	
	methods = {}
	for recipe_name, rule in data["Recipes"].items():
		product = next(iter(rule["Produces"].keys()))

		if product not in methods:
			methods[product] = []

		methods[product].append((recipe_name, rule))

	for product, recipes in methods.items():
		recipes.sort(key=lambda x: x[1]["Time"])
		
		method_list = [make_method(name, rule) for name, rule in recipes]
		pyhop.declare_methods("produce_" + product, *method_list)
						

def make_operator (rule):
    def operator (state, ID):
        if state.time[ID] <= 0:
            return False
		
        if 'Requires' in rule.keys():
            required_tool = (next(iter(rule['Requires'])))
            if getattr(state, required_tool)[ID] == 0:
                return False
			
        product = (next(iter(rule['Produces'].keys())))
        getattr(state, product)[ID] += rule['Produces'][product]

        if 'Consumes' in rule.keys():
            for item in rule['Consumes']:
                getattr(state, item)[ID] -= rule['Consumes'][item]


        state.time[ID] -= rule['Time']
        return state

    return operator

def declare_operators (data):
	# your code here
	# hint: call make_operator, then declare the operator to pyhop using pyhop.declare_operators(o1, o2, ..., ok)
	operators = []
	for name, rule in data["Recipes"].items():
		op_name = "op_" + name.replace(" ", "_")  
		operator = make_operator(rule)
		operator.__name__ = op_name
		operators.append(operator)

	pyhop.declare_operators(*operators)

def add_heuristic(data, ID):
	
	# prune paths when time runs out
	def heuristic_time(state, curr_task, tasks, plan, depth, calling_stack):
		return state.time[ID] <= 0

	# prioritize building best possible axe
	def heuristic_axe(state, curr_task, tasks, plan, depth, calling_stack):
		if ('op_craft_stone_axe_at_bench', 'agent') in tasks:
			return True
		if ('op_craft_wooden_axe_at_bench', 'agent') in tasks:
			return True
		return False
	

	# prioritize gathering wood fastest way possible
	def heuristic_gather(state, curr_task, tasks, plan, depth, calling_stack):
		if ('have_enough', 'agent', 'wood', 1) in tasks:
			if ('op_iron_axe_for_wood', 'agent') in tasks and state.bench[ID] == 0:
				return True
			if ('op_stone_axe_for_wood', 'agent') in tasks and state.bench[ID] == 0:
				return True
			if ('op_wooden_axe_for_wood', 'agent') in tasks and state.bench[ID] == 0:
				return True
		return False
	
	# pensure you only craft these items once
	def heuristic_count_tasks(state, curr_task, tasks, plan, depth, calling_stack):
		tool_tasks = [
			('op_craft_bench', 'bench'),
			('op_craft_furnace_at_bench', 'furnace'),
			('op_craft_iron_pickaxe_at_bench', 'iron_pickaxe'),
			('op_craft_stone_pickaxe_at_bench', 'stone_pickaxe'),
			('op_craft_wooden_pickaxe_at_bench', 'wooden_pickaxe'),
			('op_craft_iron_axe_at_bench', 'iron_axe'),
			('op_craft_stone_axe_at_bench', 'stone_axe'),
			('op_craft_wooden_axe_at_bench', 'wooden_axe'),
		]

		for task, tool in tool_tasks:
			if tasks.count((task, 'agent')) >= 2 or (getattr(state, tool)[ID] >= 1 and (task, 'agent') in tasks):
				return True
		return False

	

	# ensure proper tier progression
	def heuristic_tiers(state, curr_task, tasks, plan, depth, calling_stack):
		tier_upgrades = [
			('op_stone_axe_for_wood', 'wooden_axe'),
			('op_iron_axe_for_wood', 'stone_axe'),
			('op_stone_pickaxe_for_stone', 'wooden_pickaxe'),
			('op_iron_pickaxe_for_stone', 'stone_pickaxe'),
		]

		for task, prerequisite in tier_upgrades:
			if (task, 'agent') in tasks and getattr(state, prerequisite)[ID] == 0:
				return True  
		return False


	pyhop.add_check(heuristic_time)
	pyhop.add_check(heuristic_axe)
	pyhop.add_check(heuristic_gather)
	pyhop.add_check(heuristic_count_tasks)
	pyhop.add_check(heuristic_tiers)
	




def set_up_state (data, ID, time=0):
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

if __name__ == '__main__':
	rules_filename = 'crafting.json'

	with open(rules_filename) as f:
		data = json.load(f)

	state = set_up_state(data, 'agent', time=250) # allot time here
	goals = set_up_goals(data, 'agent')

	declare_operators(data)
	declare_methods(data)
	add_heuristic(data, 'agent')

	# pyhop.print_operators()
	# pyhop.print_methods()

	# Hint: verbose output can take a long time even if the solution is correct; 
	# try verbose=1 if it is taking too long
	pyhop.pyhop(state, goals, verbose=3)
	# pyhop.pyhop(state, [('have_enough', 'agent', 'cart', 1),('have_enough', 'agent', 'rail', 20)], verbose=3)