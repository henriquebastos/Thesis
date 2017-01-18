class GenericObject:
    def __init__(self, class_name, name):
     # variables=None, functions=None, function_variables=None):
        self.class_name = class_name
        self.name = name
        self.variables = {}
        self.functions = []
        self.function_variables = {}

    def __repr__(self):
        s = 'ClassName: {0}'.format(self.class_name)
        s += ', Name: {0}'.format(self.name)
        s += ', Variables: {0}'.format(self.variables)
        s += ', Functions: {0}'.format(self.functions)
        s += ', Function Variables: {0}'.format(self.function_variables)
        return s

    def add_variable(self, variable, result):
        self.variables[variable] = result
    
    def insert(self, name, variables, functions):  
        self.generic_object = self.generic_object.insert(name, variables, functions)
