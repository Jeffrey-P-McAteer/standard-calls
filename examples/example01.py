# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "standard_calls @ file:///${PROJECT_ROOT}/target/release/standard_calls-0.1.0-cp39-abi3-win_amd64.whl"
# ]
# ///

# neighbors.toml will need to list neighbors, list if clients can ask for the list of our own neighbors,...
# identity.toml will have to identify hardware or software PKI capabilities.
# on import read /etc/standard-calls/neighbors.toml, $STANDARD_CALLS_NEIGHBORS_TOML, ~/.config/standard-calls/neighbors.toml
# on import read /etc/standard-calls/identity.toml, $STANDARD_CALLS_IDENTITY_TOML, ~/.config/standard-calls/identity.toml
import standard_calls

# Client regular-usage ideas
standard_calls.configure_identity(standard_calls.Anonymous_PKI)

for neighbor in standard_calls.get_neighbors():
    if neighbor.is_alive():
        print(f'{neighbor} is online + we can call functions on it!')
        # Neighbors by default allow transitive connections through themselves, and recieving sides are free to add
        # transitive neighbors to their own list of neighbors.
        # <neighbor>.get_neighbors will not return the calling Neighbor to make avoidance of circular dependency chains easier.
        for sub_neighbor in neighbor.get_neighbors():
            pass # Should get_neighbors() take an argument for depth? Yeah that sounds good.
    else:
        print(f'{neighbor} is listed in a config file but is offline :(')

# neighbors allows us to specify a sub-set of neighbors to reach out to; this will be uncommon but necessary for eg HPC server clusters and/or infosec reasons
# versions allows a broad-granularity specification of allowed versions to return. It's a list so 4-5 concrete versions may be specified; may also need a negation
#          syntax like ['>=2.0', '!==2.1'] to use the latest but dis-allow an insecure 2.1 from being selected.
# satisfying_tests is a list of callables which recieve a canidate call and return a boolean; True if the call is allowed, false if it does not perform
#                  what was requested. This allows a highly-specific query of known-good behavior enabled by testing at the call-aquire site.
abs_call = standard_calls.find_call("abs", neighbors=[], versions=['>=0.0'], satisfying_tests=[lambda call: call(-1) == 1 and call(2) == 2])
print(f'abs_call(-7) = {abs_call(-7)}')


# Client inspect/debug-usage ideas

abs_call = standard_calls.find_call("abs", neighbors=[], versions=['>=0.0'], satisfying_tests=[lambda call: call(-1) == 1 and call(2) == 2])

# Graph execution from one call to its child calls, labeling the selected pieces of work with meta-data names.
# The call to trace is given as a lambda in case we want to compose multiple (eg lambda: abs_call(get_stock_value('XYZ')) )
# which would ask the neighbors prio
standard_calls.graph_subcalls_to_png(lambda: abs_call(-5), 'path/to/graph.png', width=1024, height=800, subcall_labels=[
    'node-name', 'execution-duration', 'node-pki-public-key', 
])
standard_calls.graph_subcalls_to_mp4(lambda: abs_call(-5), 'path/to/animation.mp4', width=1024, height=800, subcall_labels=[
    'node-name', 'execution-duration', 'node-pki-public-key', 
])



# Server usage ideas
standard_calls.configure_identity(standard_calls.Anonymous_PKI)

async def my_function(a,b,c):
    print(f'Doing work with {a} and {b}')
    # Within the call, standard_calls global functions can lookup + return neighbor information.... ? Perf/stack inspection thoughts?

    calling_neighbor_ip = standard_calls.get_calling_neighbor_ip()
    calling_neighbor_public_key = standard_calls.get_calling_neighbor_public_key()
    
    # This is a no-op unless running from standard_calls.graph_subcalls*,
    # in which case this is evaluated and returned as a labeled calculation in the subcall graph item.
    standard_calls.graph_declare_calc(f'{a} + {b} = {a+b}')
    
    # If find_call is executed _within_ a standard call, the server will delay by a random amount of time (5-50ms) and print a warning letting developers know that
    # interior calls should be looked up once at service start-up; if a neighbor goes down while a call is running that will throw a runtime error on the caller side.
    # Because a common pattern is to re-try on server failure, 
    sub_function = standard_calls.find_call("abs", neighbors=[], versions=['>=0.0'], satisfying_tests=[lambda call: call(-1) == 1 and call(2) == 2])

    retry_http_call = standard_calls.find_recreating_call("http_get", neighbors=[], versions=['>=0.0'], satisfying_tests=[lambda call: call("http://example.org").casefold().startswith('<html'.casefold()) ], maximum_call_recreate_attempts=12)
    # retry_http_call is a wrapper around the object returned by standard_calls.find_call;
    # when a server stops responding and is offline, it re-queries with the passed in parameters and
    # selects a new standard_calls.find_call object satisfying the criteria.

    return 1.0 + a + b + sub_function(c)

standard_calls.serve_forever({'my_function': my_function})


