def sum_matrix(m1, m2):
    r = []
    for r1, r2 in zip(m1, m2):
        r.append([])
        for c1, c2 in zip(r1, r2):
            r[len(r) - 1].append(c1 + c2)
            # r[len(r) - 1]. \
            # append(c1 + c2)
    return r


def main():
    m1 = [[1, 1, 1], [1, 1, 1], [1, 1, 1]]
    m2 = [[2, 2, 2], [2, 2, 2], [2, 2, 2]]
    r = sum_matrix(m1, m2)
    print r

if __name__ == '__main__':
    main()


# >>> import pydevd
# >>> p = pydevd.PyDB()
# >>> p.ready_to_run
# False
# >>> p.ready_to_run = True
# >>> p.ready_to_run
# True
# >>> p.run('/Users/noahnegrey/Documents/sum_matrix.py')
# [[3, 3, 3], [3, 3, 3], [3, 3, 3]]
