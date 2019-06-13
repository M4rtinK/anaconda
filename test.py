class Foo(object):

    @property
    def bar(self, aa=None):
        if aa is None:
            return "aa"
        else:
            return lambda x: x

f = Foo()
print(f.bar)
print(f.bar("bb"))
