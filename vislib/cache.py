import inspect
import logging
import time
import types
import warnings

from django.conf import settings
from django.core.cache import cache as django_cache

class debug_cache(object):
    ignore = [ 'to_slug', 'repodownloadsize' ] # ignore keys starting with these

    def __getattr__(self, attr):
        def wraps(f):
            def i(*args, **kwargs):
                if not any([ args[0].startswith(ig) for ig in debug_cache.ignore ]):
                    logging.info("CACHE %s: args=%s, kwargs=%s" % (attr, args, kwargs))
                value = f(*args, **kwargs)
                return value
            return i
        return wraps(getattr(django_cache, attr))

if getattr(settings, 'DEBUG_CACHE', False):
    cache = debug_cache()
else:
    cache = django_cache


def cachewrap(key_args=None, timeout=60*5, generation=None, update_for_func=None):
    """
    A decorator that uses the name of the function, combined with the values
    of arguments listed in `key_args` to store and retrieve objects in the
    cache.

    If a value for the key generated for a function call already exists,
    execution of the function is bypassed and the value in the cache store
    returned.

    The specifiable attributes are:

        key_args -- a list of attributes that should, combined with the
            function name, uniquely identify a cacheable object
        timeout -- how long it takes the item to expire in seconds
        generation -- name of the field within `key_args` which can be
            given a generation number that expires the cache if the
            generation has passed (i.e., all data on the same objects
            with the same common identifier can be "expired" and re-
            fetched).
        update_for_func -- update the key for the given function, but never
            short-circuit the function call. useful for calls that
            update data where the updated data is returned.

    !WARNING! Because the decorator relies so heavily on function names, its current
    programming does not support using other decorators along with
    `cachewrap`. Using multiple decorators will cause indescriptive
    cache keys, possibly collisions with other keys and loss of dependability
    on `update_for_func` for any `cachewrap` decorators referring
    to the one with multiple decorators.
    """

    def inner(func):
        def wrapper(*args, **kwargs):
            # 'generation' remains constant throughout all cached functions,
            # but its corresponding value is common to everything that should
            # be refreshed when the cache for that generation is cleared.
            gen = None
            if generation:
                generation_key = extract_param_by_name(func, args, kwargs, generation)
                gen = get_generation(generation, generation_key)

            function_name = (update_for_func and update_for_func.func_name) or func.func_name
            params = (extract_param_by_name(func, args, kwargs, label) for label in key_args)
            key = _make_cache_key(function_name, params, gen)

            # If the function has a force parameter, we skip any attempt to get an old object from the cache,
            # and create a new object in the cache.
            is_globally_cleared = globals().get('force_clear_cache', False)
            force = ('force' in kwargs.keys() and kwargs['force']) or is_globally_cleared

            if not update_for_func and not force:
                obj = cache.get(key)
                if obj is not None:
                    last_updated, value = obj
                    update_latest_data_time(last_updated)
                    return value

            last_updated = time.time()
            value = func(*args, **kwargs)

            # Force element to something we can store.  Use a tuple because
            # it's efficient like you might want if you're using a generator.
            if isinstance(value, types.GeneratorType):
                value = tuple(value)

            # The default max storage size for memcached is 1MB.  Don't attempt
            # to store anything larger than that or we'll get errors from it.
            try:
                cache.set(key, (last_updated, value), timeout)
            except:
                warnings.warn("Server error from memcached when setting cache. "
                    "Was the object brought into '{key}' too large?".format(key=key))

            update_latest_data_time(last_updated)
            return value
        # make old function name accessible to functions using `update_for_func`
        # instead of seeing just "wrapper" as the function name
        wrapper.func_name = func.func_name

        # make all the arguments available
        wrapper.key_args = key_args
        wrapper.timeout = timeout
        wrapper.generation = generation
        return wrapper
    return inner

def _get_generation_key(name, key):
    return u'generation.{name}.{key}'.format(name=name, key=key)

DEFAULT_GENERATION = 0
def get_generation(name, key):
    return cache.get(_get_generation_key(name, key)) or DEFAULT_GENERATION

def increment_generation(name, key):
    generation_key = _get_generation_key(name, key)
    try:
        cache.incr(generation_key)  # this is said to be very fast
    except:
        # We assume that an exception is because the key wasn't found.  The error
        # raised here can be different depending on what library implements the
        # increment function.
        cache.set(generation_key, DEFAULT_GENERATION+1)

def update_latest_data_time(last_updated):
    """Updates the `latest_data_time` global variable."""
    global latest_data_time
    # If it's not set already (because it's not being used by enclosing scope) just set it
    if not 'latest_data_time' in globals():
        latest_data_time = 0

    if last_updated > latest_data_time:
        latest_data_time = last_updated

def _make_cache_key(function_name, parameters, generation=None):
    key = u'external.%s.%s' % (function_name, '-'.join(map(unicode, parameters)))
    key = key.replace(' ', '-') # spaces are not allowed in the key
    if generation is not None:
        key = u'generation.{generation}.{key}'.format(generation=generation, key=key)
    return key


def extract_param_by_name(f, args, kwargs, param):
    """Find the value of a parameter by name, even if it was passed via *args or is a default value.

    Let's start with a fictional function:
    >>> def my_f(a,b,c='foo'):
    ...
    ...

    Works with kwargs (easy):
    >>> extract_param_by_name(my_f, [], {'a':1}, 'a')
    1

    Works with args (not obvious):
    >>> extract_param_by_name(my_f, [2], {}, 'a')
    2

    Works with default kwargs (bet you didn't think about that one):
    >>> extract_param_by_name(my_f, [], {}, 'c')
    'foo'

    But of course you can override that:
    >>> extract_param_by_name(my_f, [99,98,97], {}, 'c')
    97

    In different ways:
    >>> extract_param_by_name(my_f, [], {'c':'gar'}, 'c')
    'gar'

    And dies with "grace" when you do something silly:
    >>> extract_param_by_name(my_f, [], {}, 'a')
    Traceback (most recent call last):
    ...
    LoggerBadCallerParametersException: ("Caller didn't provide a required positional parameter '%s' at index %d", 'a', 0)
    >>> extract_param_by_name(my_f, [], {}, 'z')
    Traceback (most recent call last):
    ...
    LoggerUnknownParamException: ('Unknown param %s(%r) on %s', <type 'str'>, 'z', 'my_f')
    """
    if param in kwargs:
        return kwargs[param]
    else:
        argspec = inspect.getargspec(f)
        if param in argspec.args:
            param_index = argspec.args.index(param)
            if len(args) > param_index:
                return args[param_index]

            if argspec.defaults is not None:
                # argsec.defaults holds the values for the LAST entries of argspec.args
                defaults_index = param_index - len(argspec.args) + len(argspec.defaults)
                if 0 <= defaults_index < len(argspec.defaults):
                    return argspec.defaults[defaults_index]

            raise LoggerBadCallerParametersException("Caller didn't provide a required positional parameter '%s' at index %d", param, param_index)
        else:
            raise LoggerUnknownParamException("Unknown param %s(%r) on %s", type(param), param, f.__name__)

class LoggerUnknownParamException(Exception):
    pass

class LoggerBadCallerParametersException(Exception):
    pass
