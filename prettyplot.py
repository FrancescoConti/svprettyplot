# parser for SV module headers

import re
from collections import OrderedDict
import pydotplus

TOKENS = OrderedDict([
    ( 'MODULE_KEYWORD',       r'.*module\s*'                                                                                                      ),
    ( 'MODULE_NAME',          r'\A(\D\w*)\s*'                                                                                                     ),
    ( 'PARAMETER_LIST_START', r'\A\#\(\s*'                                                                                                        ),
    ( 'PARAMETER_LIST_COMMA', r'\A\,\s*'                                                                                                          ),
    ( 'PARAMETER_DECL',       r'\Aparameter\s*(logic|wire|reg|int|integer)?\s*(signed|unsigned)?(\D\w*)\s*=\s*(\w+)\s*'                           ),
    ( 'PORT_LIST_START',      r'\A\(\s*'                                                                                                          ),
    ( 'PORT_LIST_COMMA',      r'\A\,\s*'                                                                                                          ),
    ( 'PORT_DECL',            r'\A(input|output|inout)?\s*(logic|wire|reg|int|integer)?\s*(signed|unsigned)?\s*(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\w+)\s*(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?'),
    ( 'PORT_DECL_INTF',       r'\A(\D\w*)\.(\D\w*)\s+(\D\w*)\s*(\[\s*[\w\-\+\*\/\%]+\s*\:\s*[\w\-\+\*\/\%]+\s*\]\s*)?'                            ),
    ( 'LIST_STOP',            r'\A\)\s*'                                                                                                          ),
    ( 'DECL_END',             r'\A\;\s*'                                                                                                          )
])

MATCHES = OrderedDict([
    ( 'MODULE_KEYWORD',       (  ) ),
    ( 'MODULE_NAME',          ( 'name', ) ),
    ( 'PARAMETER_LIST_START', (  ) ),
    ( 'PARAMETER_LIST_COMMA', (  ) ),
    ( 'PARAMETER_DECL',       ( 'type', 'sign', 'name', 'value', ) ),
    ( 'PORT_LIST_START',      (  ) ),
    ( 'PORT_LIST_COMMA',      (  ) ),
    ( 'PORT_DECL',            ( 'direction', 'type', 'sign', 'packed0', 'packed1', 'packed2', 'packed3', 'name', 'unpacked', ) ),
    ( 'PORT_DECL_INTF',       ( 'interface', 'modport', 'name', 'unpacked', ) ),
    ( 'LIST_STOP',            (  ) ),
    ( 'DECL_END',             (  ) )
])

FOLLOWS = OrderedDict([
    ( 'ROOT',                 ( 'MODULE_KEYWORD', ) ),
    ( 'MODULE_KEYWORD',       ( 'MODULE_NAME', ) ),
    ( 'MODULE_NAME',          ( 'PARAMETER_LIST_START', 'PORT_LIST_START', ) ),
    ( 'PARAMETER_LIST_START', ( 'PARAMETER_DECL', ) ),
    ( 'PARAMETER_LIST_COMMA', ( 'PARAMETER_DECL', ) ),
    ( 'PARAMETER_DECL',       ( 'PARAMETER_LIST_COMMA', 'LIST_STOP', ) ),
    ( 'PORT_LIST_START',      ( 'PORT_DECL_INTF', 'PORT_DECL', ) ),
    ( 'PORT_LIST_COMMA',      ( 'PORT_DECL_INTF', 'PORT_DECL', ) ),
    ( 'PORT_DECL',            ( 'PORT_LIST_COMMA', 'LIST_STOP', ) ),
    ( 'PORT_DECL_INTF',       ( 'PORT_LIST_COMMA', 'LIST_STOP', ) ),
    ( 'LIST_STOP',            ( 'DECL_END', 'PORT_LIST_START', ) ),
    ( 'DECL_END',             (  ) )
])

# specific to HWPEs
INTERFACES_INCOMING_MODPORTS = ( 'slave', 'sink', 'monitor' )
INTERFACES_OUTGOING_MODPORTS = ( 'master', 'source' )

def tokenize_systemverilog(code, verbose=True):
    # set up token list
    tokens = []
    # look for "model" keyword
    curr_token = 'ROOT'
    # tokenize & parse
    while True:
        flag = True
        for next_token in FOLLOWS[curr_token]:
            pattern = TOKENS[next_token]
            split = re.split(pattern, code, maxsplit=1)
            if len(split) > 1:
                flag = False
                break
        if flag:
            print("ERROR @%s" % next_token)
            # print("FOLLOWS: %s" % (FOLLOWS[curr_token]))
            print("REMAINING CODE:", code)
            return None
        # next code is given by split[-1]
        code = split[-1]
        token = OrderedDict([])
        token['token_type'] = next_token
        for i,m in enumerate(MATCHES[next_token]):
            token[m] = split[1+i]
        tokens.append(token)
        if verbose:
            print(token)
        # update state
        curr_token = next_token
        # catch end of module declaration
        if next_token == 'DECL_END':
            break
    return tokens

def interpret_systemverilog(tokens):
    module = OrderedDict([])
    # much easier than a real parsing!!!
    for t in tokens:
        if t['token_type'] == 'MODULE_NAME':
            module['name'] = t['name']
            module['parameters'] = []
            module['input_ports'] = []
            module['output_ports'] = []
            module['inout_ports'] = []
            module['interfaces'] = []
            module['incoming_interfaces'] = []
            module['outgoing_interfaces'] = []
        elif t['token_type'] == 'PARAMETER_DECL':
            p = OrderedDict([])
            p['name'] = t['name']
            p['value'] = t['value']
            module['parameters'].append(p)
        elif t['token_type'] == 'PORT_DECL':
            p = OrderedDict([])
            p['name'] = t['name']
            p['type'] = t['type']
            p['sign'] = t['sign']
            p['packed0'] = t['packed0'] if t['packed0'] is not None else ''
            p['packed1'] = t['packed1'] if t['packed1'] is not None else ''
            p['packed2'] = t['packed2'] if t['packed2'] is not None else ''
            p['packed3'] = t['packed3'] if t['packed3'] is not None else ''
            p['unpacked'] = t['unpacked']
            module['%s_ports' % t['direction']].append(p)
        elif t['token_type'] == 'PORT_DECL_INTF':
            p = OrderedDict([])
            p['name'] = t['name']
            p['interface'] = t['interface']
            p['modport'] = t['modport']
            if p['modport'] in INTERFACES_INCOMING_MODPORTS:
                module['incoming_interfaces'].append(p)
            elif p['modport'] in INTERFACES_OUTGOING_MODPORTS:
                module['outgoing_interfaces'].append(p)
            else:
                module['interfaces'].append(p)
    return module

with open("/Users/fconti/hwpe-stream/rtl/basic/hwpe_stream_fence.sv", "r") as f:
    code = f.read()

tokens = tokenize_systemverilog(code)
module = interpret_systemverilog(tokens)

# module = {'name': 'mod'}
graph = pydotplus.graphviz.Dot('module', graph_type='digraph', rankdir='LR')
s =  '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="10">'
# title
s += '<TR><TD PORT="t"><FONT FACE="Helvetica Neue Bold">%s</FONT></TD></TR>\n' % (module['name'])
# other rows
n_in = len(module['input_ports']) + len(module['incoming_interfaces'])
n_out = len(module['output_ports']) + len(module['outgoing_interfaces'])
all_ins = module['input_ports'] + module['incoming_interfaces']
all_outs = module['output_ports'] + module['outgoing_interfaces']
mcm = n_in * n_out
for i in range(mcm):
    s += '<TR>\n'
    if i % n_out == 0:
        s += '<TD ROWSPAN="%d" PORT="i%d"><FONT COLOR="white">%s</FONT></TD>\n' % (n_out, i//n_out, all_ins[i//n_out]['name'])
    if i % n_in == 0:
        s += '<TD ROWSPAN="%d" PORT="o%d"><FONT COLOR="white">%s</FONT></TD>\n' % (n_in, i//n_in, all_outs[i//n_in]['name'])
    s += '</TR>\n'
s += '</TABLE>>'
graph.add_node(pydotplus.graphviz.Node(module['name'], label=s, shape='none', fontname='Helvetica Neue'))

# inbound nodes/edges
s =  '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="10">\n'
for i in range(len(all_ins)):
    s += '<TR><TD PORT="i%d">%s</TD></TR>' % (i, all_ins[i]['name'])
s += '</TABLE>>'
graph.add_node(pydotplus.graphviz.Node('inputs', label=s, shape='none', fontname='Helvetica Neue'))
for i in range(len(all_ins)):
    graph.add_edge(pydotplus.graphviz.Edge(('inputs:i%d' % i, module['name']+':i%d' % i)))

# outbound nodes/edges
s =  '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="10">\n'
for i in range(len(all_outs)):
    try:
        s += '<TR><TD PORT="o%d"><FONT FACE="Consolas Bold">%s</FONT>%s %s</TD></TR>' % (i, all_outs[i]['type'], all_outs[i]['packed0']+all_outs[i]['packed1']+all_outs[i]['packed2']+all_outs[i]['packed3'], all_outs[i]['name'])
    except KeyError:
        s += '<TR><TD PORT="o%d"><FONT FACE="Consolas Bold">%s</FONT> %s</TD></TR>' % (i, all_outs[i]['interface'], all_outs[i]['name'])
s += '</TABLE>>'
graph.add_node(pydotplus.graphviz.Node('outputs', label=s, shape='none', fontname='Consolas'))
for i in range(len(all_outs)):
    graph.add_edge(pydotplus.graphviz.Edge((module['name']+':o%d' % i, 'outputs:o%d' % i)))

with open("prova.pdf", "wb") as f:
    f.write(graph.create_pdf())
