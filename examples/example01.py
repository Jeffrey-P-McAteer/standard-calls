# /// script
# requires-python = ">=3.10"
# dependencies = [
# ]
# ///

# on import read /etc/standard-calls/neighbors.toml, $STANDARD_CALLS_NEIGHBORS_TOML, ~/.config/standard-calls/neighbors.toml
# on import read /etc/standard-calls/identity.toml, $STANDARD_CALLS_IDENTITY_TOML, ~/.config/standard-calls/identity.toml
import standard_calls

# Client usage ideas
standard_calls.configure_identity(standard_calls.Anonymous_PKI)

for neighbor in standard_calls.get_neighbors():
    if neighbor.is_alive():
        print(f'{neighbor} is online + we can call functions on it!')
    else:
        print(f'{neighbor} is listed in a config file but is offline :(')

# neighbors allows us to specify a sub-set of neighbors to reach out to; this will be uncommon but necessary for eg HPC server clusters and/or infosec reasons
# versions allows a broad-granularity specification of allowed versions to return. It's a list so 4-5 concrete versions may be specified; may also need a negation
#          syntax like ['>=2.0', '!==2.1'] to use the latest but dis-allow an insecure 2.1 from being selected.
# satisfying_tests is a list of callables which recieve a canidate call and return a boolean; True if the call is allowed, false if it does not perform
#                  what was requested. This allows a highly-specific query of known-good behavior enabled by testing at the call-aquire site.
abs_call = standard_calls.find_call("abs", neighbors=[], versions=['>=0.0'], satisfying_tests=[lambda call: call(-1) == 1 and call(2) == 2])
print(f'abs_call(-7) = {abs_call(-7)}')


# Server usage ideas
standard_calls.configure_identity(standard_calls.Anonymous_PKI)

async def my_function(a,b,c):
    print(f'Doing work with {a} and {b}')
    # Within the call, standard_calls global functions can lookup + return neighbor information.... ? Perf/stack inspection thoughts?

    return a + b + c

standard_calls.serve_forever({'my_function': my_function})


