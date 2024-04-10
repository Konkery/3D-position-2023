import time
#import dill

#def _pickle_method(method):
#    func_name = method.im_func.__name__
#    obj = method.im_self
#    cls = method.im_class
#    return dill.copy(func_name, obj, cls)

#dill.pickle.Pickler.save_instance_method = _pickle_method

# Определяем классы
class ClassA:
    def run(self):
        global count1, count2
        for _ in range(10):
            count1 += 1
            count2 += 10
            time.sleep(1)

class ClassB:
    def run(self):
        global count1
        for _ in range(10):
            print(f"ClassB: count1 = {count1}")
            time.sleep(1)

class ClassC:
    def run(self):
        global count2
        for _ in range(10):
            print(f"ClassC: count2 = {count2}")
            time.sleep(1)
