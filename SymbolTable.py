from StaticError import *
from Symbol import *
from functools import *

def simulate(list_of_commands): 
    if (not list_of_commands): #input rỗng thì return rỗng
        return []
    if all(c in ['PRINT', 'RPRINT'] for c in list_of_commands):
        return [""]*len(list_of_commands)
    def is_valid_identifier(name):
        return (name and name[0].islower() and 
                all(c.islower() or c.isupper() or c.isdigit() or c == '_' for c in name))
    def is_valid_type(typ):
        return typ in ['number', 'string']

    def is_valid_number(value):
        return value.isdigit()

    def is_valid_string(value):
        if len(value) < 2: 
            return False
        if not (value.startswith("'") and value.endswith("'") ):
            return False
        inner = value[1:-1]
        return all(c.isalnum() for c in inner)
    def parse_command(cmd):
        parts = cmd.split(' ', 2)
        if not parts:
            return None
        code = parts[0]
        if not (code in  ['BEGIN', 'END', 'PRINT', 'RPRINT','LOOKUP','ASSIGN', 'INSERT']): #Nếu cụm từ đầu ko thuộc nhóm này thì invalid command
            return "Invalid command", []
        if code in ['BEGIN', 'END', 'PRINT', 'RPRINT']:
            if len(parts) != 1:
                return None
            return (code, [])
        if code == 'LOOKUP':
            if len(parts) != 2 or not is_valid_identifier(parts[1]):
                return None
            return (code, [parts[1]])
        if code == 'INSERT':
            if len(parts) != 3 or not is_valid_identifier(parts[1]) or not is_valid_type(parts[2]):
                return None
            return (code, [parts[1], parts[2]])
        if code == 'ASSIGN':
            if len(parts) != 3 or not is_valid_identifier(parts[1]):
                return None
            if not (is_valid_number(parts[2]) or is_valid_string(parts[2]) or is_valid_identifier(parts[2])):
                return None
            return (code, [parts[1], parts[2]])
        return None

    def find_symbol(symbols, name, level):
        def search(index):
            if index < 0:
                return (level, None)
            current_scope = symbols[index]
            found = list(filter(lambda sym: sym.name == name, current_scope))
            return (index, found[0]) if found else search(index - 1)
        return search(len(symbols) - 1)

    def check_type_match(symbol, value, symbols):
        if not symbol:
            return 'undeclared'

        if is_valid_number(value):
            return 'true' if symbol.typ == 'number' else 'mismatch'
        if is_valid_string(value):
            return 'true' if symbol.typ == 'string' else 'mismatch'
        

        _, value_symbol = find_symbol(symbols, value, len(symbols))
        if not value_symbol:
            return 'undeclared'
        return 'true' if value_symbol.typ == symbol.typ else 'mismatch'


    def process_command(cmd, symbols, level):
        parsed = parse_command(cmd)
        if not parsed:
            raise InvalidInstruction(cmd)

        code, args = parsed

        if code=="Invalid command":
                raise InvalidInstruction("Invalid command")
        if code == 'INSERT':
            name, typ = args
            current_symbols = symbols[-1] if symbols else []
            if any(sym.name == name for sym in current_symbols):
                raise Redeclared(cmd)
            new_scope = current_symbols + [Symbol(name, typ)]
            return ('success', symbols[:-1] + [new_scope], level)

        if code == 'ASSIGN':
            name, value = args
            _, symbol = find_symbol(symbols, name, len(symbols))
            match_result = check_type_match(symbol, value, symbols)
            if match_result == 'undeclared':
                raise Undeclared(cmd)
            if match_result == 'mismatch':
                raise TypeMismatch(cmd)
            return ('success', symbols, level)

        if code == 'BEGIN':
            return ('', symbols + [[]], level + 1)

        if code == 'END':
            if len(symbols) == 1:
                raise UnknownBlock()
            return ('', symbols[:-1], level - 1)

        if code == 'LOOKUP':
            level_found, symbol = find_symbol(symbols, args[0], len(symbols))
            if not symbol:
                raise Undeclared(cmd)
            return (str(level_found), symbols, level)
        
        if code == 'PRINT':
            flat_symbols = [(i, sym) for i, syms in enumerate(symbols) for sym in syms]
            def update_active(active_syms, item):
                i, sym = item
                return (
                [(s, l) for s, l in active_syms if s.name != sym.name] + [(sym, i)]
                if not any(s.name == sym.name and l > i for s, l in active_syms)
                else active_syms
                )
            final_symbols = reduce(update_active, flat_symbols, [])
            printed1 = ' '.join(f'{sym.name}//{l}' for sym, l in final_symbols).strip()
            return (printed1 if printed1 else "", symbols, level)

            #printed1 = ' '.join(f'{sym.name}//{l}' for sym, l in final_symbols).strip()
            #return (printed1, symbols, level)
        '''
        if code == "PRINT":
            flat_symbols = [(i, sym) for i, syms in enumerate(symbols) for sym in syms]

            def update_active(acc, item):
                active_syms, entries = acc
                i, sym = item
                if not any(s.name == sym.name and l > i for s, l in active_syms):
                    new_active = [(s, l) for s, l in active_syms if s.name != sym.name] + [(sym, i)]
                    return (new_active, entries + [f"{sym.name}//{i}"])
                else:
                    return (active_syms, entries)

            final_active, final_entries = reduce(update_active, flat_symbols, ([], []))
            printed1 = ' '.join(final_entries).strip()
            return (printed1, symbols, level)
        '''



        if code == 'RPRINT':
            flattened = [
                (sym, len(symbols) - 1 - i)
        for i, scope in enumerate(reversed(symbols))
        for sym in reversed(scope)
    ]
            def update_active_rprint(active_syms, item):
                sym, lvl = item
                return active_syms + [(sym, lvl)] if all(s.name != sym.name for s, _ in active_syms) else active_syms
            final_symbols2 = reduce(update_active_rprint, flattened, [])
            printed2 = ' '.join(f'{sym.name}//{lvl}' for sym, lvl in final_symbols2).strip()
            return (printed2 if printed2 else "", symbols, level)
            #return (printed2.strip(), symbols, level)  # Với PRINT
            #printed2 = ' '.join(f'{sym.name}//{lvl}' for sym, lvl in final_symbols2).strip()
            #return (printed2, symbols, level)



        raise InvalidInstruction(cmd)

    def process_commands(commands, symbols=None, level=0, results=None):
        symbols = [[]] if symbols is None else symbols
        results = [] if results is None else results

        def step(state, cmd):
            symbols, level, results, error = state
            if error is not None:
                return (symbols, level, results, error)
            try:
                result, new_symbols, new_level = process_command(cmd, symbols, level)
                new_results = (
                    results + [result]
                    if (cmd in ["PRINT", "RPRINT"] and result is not None)
                    else results + ([result] if result else [])
                )
                return (new_symbols, new_level, new_results, None)
            except StaticError as e:
                return (symbols, level, results, str(e))

        symbols_out, level_out, results_out, error = reduce(
            step, commands, (symbols, level, results, None)
        )

        if error:
            return [error]
        if len(symbols_out) > 1:
            raise UnclosedBlock(len(symbols_out) - 1)
        return results_out

    return process_commands(list_of_commands)
