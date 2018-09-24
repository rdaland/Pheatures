class SimpleBoolArray():
    """
    This is a simple and very limited class representing a boolean array.
    It is included here for code portability. The interface emulates
    the syntax of numpy arrays. It only implements the subset of functionality
    necessary for this program, so I don't recommend using it elsewhere.

    This is SIGNIFICANTLY slower than the numpy implementation. If performance
    is important to you, you can set the USE_NUMPY variable at the top of
    this file to True to use a numpy implementation instead, which will of 
    course require having numpy installed.
    """
    def __init__(self, shape, data):
        self.shape = shape
        self.data = data

    @classmethod
    def zeros(self, shape, dtype=None):
        return SimpleBoolArray(
            shape, [[False for i in range(shape[0])] for j in range(shape[1])]
        )

    @classmethod
    def dot(self, m1, m2):
        """
        Gets the standard matrix product.
        """
        if m1.shape[1] != m2.shape[0]:
            raise "m1.cols != m2.rows, dot is not defined"
        new_data = []
        for i in range(m1.shape[0]):
            row = []
            for j in range(m2.shape[1]):
                entry = False
                for k in range(m1.shape[1]):
                    entry = entry or (m1[i, k] and m2[k, j])
                row.append(entry)
            new_data.append(row)
        return SimpleBoolArray((m1.shape[0], m2.shape[1]), new_data)      

    def __getitem__(self, key):
        row_idx, col_idx = key
        rows = []
        result = []

        if type(row_idx) == slice:
            row_start = row_idx.start or 0
            row_stop = row_idx.stop or self.shape[0]
            row_step = row_idx.step or 1
            for i in range(row_start, row_stop, row_step):
                rows.append(self.data[i])
        else:
            rows = [self.data[row_idx]]

        for row in rows:
            val = row[col_idx]
            result.extend([val] if type(val) == bool else val)

        return result[0] if len(result) == 1 else result

    def __setitem__(self, key, value):
        if type(key) == tuple:
            self.data[key[0]][key[1]] = value
        else:
            self.data[key] = value

    def __mul__(self, m):
        """
        Does element-wise multiplcation
        """
        if self.shape != m.shape:
            raise "Matrices must be the same shape for multiplication"
        new_data = []
        for i in range(self.shape[0]):
            row = []
            for j in range(self.shape[1]):
                row.append(self[i, j] and m[i, j])
            new_data.append(row)
        return SimpleBoolArray(self.shape, new_data)

    def __invert__(self):
        new_data = []
        for i in range(self.shape[0]):
            row = []
            for j in range(self.shape[1]):
                row.append(not self[i, j])
            new_data.append(row)
        return SimpleBoolArray(self.shape, new_data)

    def __str__(self):
        shape_str = 'Matrix{0}'.format(self.shape)
        dat_str = '\n\t'.join(str(row) for row in self.data)
        return('{0}[\n\t{1}]'.format(shape_str,dat_str))
