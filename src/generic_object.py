class GenericObject:
    def __init__(self, class_name, name, instance_id):
     # variables=None, functions=None, function_variables=None):
        self.class_name = class_name
        self.name = [name]
        self.instance_id = instance_id
        self.variables = {}
        self.functions = []
        self.function_variables = {}

    def __repr__(self):
        s = '\n\t\t\tClassName: {0}\n'.format(self.class_name)
        s += '\t\t\tName: {0}\n'.format(self.name)
        s += '\t\t\tInstance Id: {0}\n'.format(self.instance_id)
        s += '\t\t\tVariables: {0}\n'.format(self.variables)
        s += '\t\t\tFunctions: {0}\n'.format(self.functions)
        s += '\t\t\tFunction Variables: {0}\n'.format(self.function_variables)
        return s

    def add_variable(self, variable, result):
        if '.' in variable:
            variable = variable.split('.')[1]
        if 'self.' in result:
            result = result.split('self.')[1]
        if '.' in result:
            new_result = ''
            for r in result.split('.')[1:-1]:
                new_result = r + '.'
            result = new_result + result.split('.')[-1]
        self.variables[variable] = result

    def add_function(self, function):
        if function not in self.functions:
            self.functions.append(function)

    def add_function_variable(self, function, variable, result):
        self.add_function(function)
        if function not in self.function_variables:
            self.function_variables[function] = {}
        self.function_variables[function][variable] = result

    def get_variable(self, variable):
        if variable in self.variables:
            return self.variables[variable]
        return None
    
    # def insert(self, name, variables, functions):  
    #     self.generic_object = self.generic_object.insert(name, variables, functions)
