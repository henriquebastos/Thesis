class GenericObject:
    def __init__(self, class_name, name, instance_id, simple_id):
     # variables=None, functions=None, function_variables=None):
        self.class_name = class_name
        self.name = [name]
        self.instance_id = instance_id
        self.simple_id = simple_id
        self.variables = {}
        self.object_variables = {}
        self.functions = []
        self.function_variables = {}

    def __repr__(self):
        s = 'ClassName: {0}\n'.format(self.class_name)
        s += 'Name: {0}\n'.format(self.name)
        s += 'Id: {0}\n'.format(self.simple_id)
        s += 'Variables:\n'
        for k,v in self.variables.iteritems():
            s += '    {0}\n'.format(v)
        s += 'Functions:\n'
        for f in self.functions:
            s += '    {0}:\n'.format(f)
            if f in self.function_variables:
                for k,v in self.function_variables[f].iteritems():
                    s += '        {0}\n'.format(v)
        # s += 'Functions:\n'
        # for k,v in self.function_variables.iteritems():
            # s += '    {0}:\n'.format(k)
            # for k2,v2 in v.iteritems():
            #     s += '        {0}\n'.format(v2)
        return s

    def add_variable(self, variable, result, class_name=None, simple_id=None):
        if '.' in variable:
            variable = variable.split('.')[1]
        if 'self.' in result:
            result = result.split('self.')[1]
        if '.' in result:
            new_result = ''
            for r in result.split('.')[1:-1]:
                new_result = r + '.'
            result = new_result + result.split('.')[-1]
        if class_name is None and simple_id is None:
            self.variables[variable] = result
        else:
            self.variables[variable] = '{0}={1}_{2}'.format(variable, class_name, simple_id)
            self.object_variables[variable] = result

    def add_function(self, function):
        if function not in self.functions:
            self.functions.append(function)

    def add_function_variable(self, function, variable, result):
        self.add_function(function)
        if function not in self.function_variables:
            self.function_variables[function] = {}
        self.function_variables[function][variable] = result

    def get_variable(self, variable):
        if variable in self.object_variables:
            return self.object_variables[variable]
        return None

    def get_children(self, class_types, generic_objects):
        children = []
        for name,value in self.object_variables.iteritems():
            if 'instance at' in value:
                class_name = value.split(' instance')[0].split('.')[1]
                instance_id = value.split(' instance at ')[1].split('>')[0]
                if class_name in class_types:
                    children.append(generic_objects[instance_id])
        children.reverse()
        return children

    
    # def insert(self, name, variables, functions):  
    #     self.generic_object = self.generic_object.insert(name, variables, functions)
