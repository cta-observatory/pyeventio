from eventio import EventIOFile
import warnings


def find_type(f, eventio_type):
    o = next(f)
    while not isinstance(o, eventio_type):
        o = next(f)

    if not isinstance(o, eventio_type):
        raise ValueError('Type {} not found'.format(eventio_type))

    return o


def collect_toplevel_of_type(f, eventio_type):
    return list(yield_toplevel_of_type(f, eventio_type))


def yield_toplevel_of_type(f, eventio_type):
    try:
        for o in f:
            if isinstance(o, eventio_type):
                yield o
    except EOFError:
        warnings.warn("File seems to be truncated")


def find_all_subobjects(f, structure, level=0):
    '''
    Find all subobjects expected in structure.
    So if you want all AdcSums, use
    structure = [Event, TelescopeEvent, ADCSums]
    '''
    objects = []
    elem = structure[level]

    try:
        for o in f:
            if isinstance(o, structure[-1]):
                objects.append(o)
            elif isinstance(o, elem):
                objects.extend(find_all_subobjects(o, structure, level + 1))
    except EOFError:
        warnings.warn("File seems to be truncated")
    return objects


def yield_all_subobjects(f, structure, level=0):
    '''
    Find all subobjects expected in structure.
    So if you want all AdcSums, use
    structure = [Event, TelescopeEvent, ADCSums]
    '''
    elem = structure[level]

    for o in f:
        if isinstance(o, structure[-1]):
            yield o
        elif isinstance(o, elem):
            yield from yield_all_subobjects(o, structure, level + 1)


def yield_all_objects_depth_first(f, level=0):
    '''yield subobjects of type, regardless of structure'''

    if isinstance(f, EventIOFile) or f.header.only_subobjects:
        for o in f:
            yield o, level
            yield from yield_all_objects_depth_first(o, level + 1)


def yield_subobjects(f, eventio_type):
    '''yield subobjects of type, regardless of structure'''
    if isinstance(f, eventio_type):
        yield f
    else:
        if isinstance(f, EventIOFile) or f.header.only_subobjects:
            for o in f:
                yield from yield_subobjects(o, eventio_type)


def yield_n_subobjects(f, eventio_type, n=3):
    for i, obj in enumerate(yield_subobjects(f, eventio_type), start=1):
        if i >= n:
            yield obj
            return

        yield obj
