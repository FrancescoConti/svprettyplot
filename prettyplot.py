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
    # ( 'PORT_DECL',            r'\A(input|output|inout)?\s*(logic|wire|reg|int|integer)?\s*(signed|unsigned)?\s*(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?(\w+)\s*(\[\s*\w+\s*\:\s*\w+\s*\]\s*)?'),
    ( 'PORT_DECL', r'\A(input|output|inout)?\s*(\w+)?\s*(signed|unsigned)?\s*(\[\s*[\w\-\+\*\/\%]+\s*\:\s*[\w\-\+\*\/\%]+\s*\]\s*)?(\[\s*[\w\-\+\*\/\%]+\s*\:\s*[\w\-\+\*\/\%]+\s*\]\s*)?(\[\s*[\w\-\+\*\/\%]+\s*\:\s*[\w\-\+\*\/\%]+\s*\]\s*)?(\[\s*[\w\-\+\*\/\%]+\s*\:\s*[\w\-\+\*\/\%]+\s*\]\s*)?(\w+)\s*(\[\s*[\w\-\+\*\/\%]+\s*\:\s*[\w\-\+\*\/\%]+\s*\]\s*)?'),
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

DEFAULT_FONT = "Helvetica Neue"

INTERFACE_MAP = {
    # 'hwpe_stream_intf_stream' : 'HWPE-Stream',
    # 'hwpe_stream_intf_tcdm'   : 'HWPE-Mem',
    # 'hwpe_ctrl_intf_periph'   : 'HWPE-Periph',
}

def write_nodes(module, port_list_name, shorthand_prefix, set_name=None, kind='port', direction='in', font_face=DEFAULT_FONT):
    if len(module[port_list_name])==0:
        return ''
    if set_name is None:
        set_name = port_list_name
    if direction == 'in':
        align = "RIGHT"
    else:
        align = "LEFT"
    s = ''
    if kind == 'port':
        for i in range(len(module[port_list_name])):
            s += '<TR><TD PORT="%s%d" ALIGN="%s"><FONT FACE="%s Bold">%s</FONT>%s %s</TD></TR>' % (shorthand_prefix, i, align, font_face, module[port_list_name][i]['type'], module[port_list_name][i]['packed0']+module[port_list_name][i]['packed1']+module[port_list_name][i]['packed2']+module[port_list_name][i]['packed3'], module[port_list_name][i]['name'])
    else:
        for i in range(len(module[port_list_name])):
            try:
                intf_name = INTERFACE_MAP[module[port_list_name][i]['interface']]
            except KeyError:
                intf_name = module[port_list_name][i]['interface']
            s += '<TR><TD PORT="%s%d" ALIGN="%s"><FONT FACE="%s Bold">%s</FONT> %s</TD></TR>' % (shorthand_prefix, i, align, font_face, intf_name, module[port_list_name][i]['name'])
    return s

def add_edges(module, port_list_name, shorthand_prefix, set_name=None, kind='port', direction='in', font_face=DEFAULT_FONT):
    if len(module[port_list_name])==0:
        return
    if set_name is None:
        set_name = port_list_name
    if kind == 'port':
        if direction == 'in':
            for i in range(len(module[port_list_name])):
                graph.add_edge(pydotplus.graphviz.Edge(('%s:%s%d' % (set_name, shorthand_prefix, i), module['name']+':%s%d' % (shorthand_prefix, i)), arrowhead='tee'))
        else:
            for i in range(len(module[port_list_name])):
                graph.add_edge(pydotplus.graphviz.Edge((module['name']+':%s%d' % (shorthand_prefix, i), '%s:%s%d' % (set_name, shorthand_prefix, i)), arrowtail='tee', dir='back'))
    else:
        if direction == 'in':
            for i in range(len(module[port_list_name])):
                graph.add_edge(pydotplus.graphviz.Edge(('%s:%s%d' % (set_name, shorthand_prefix, i), module['name']+':%s%d' % (shorthand_prefix, i)), penwidth=3))
        else:
            for i in range(len(module[port_list_name])):
                graph.add_edge(pydotplus.graphviz.Edge((module['name']+':%s%d' % (shorthand_prefix, i), '%s:%s%d' % (set_name, shorthand_prefix, i)), penwidth=3))

with open("/Users/fconti/hwpe-stream/rtl/fifo/hwpe_stream_fifo.sv", "r") as f:
    code = f.read()

tokens = tokenize_systemverilog(code)
module = interpret_systemverilog(tokens)

# module = {'name': 'mod'}
graph = pydotplus.graphviz.Dot('module', graph_type='digraph', rankdir='LR')
s =  '<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="10">'
# title
s += '<TR><TD PORT="t" COLSPAN="2"><FONT FACE="Helvetica Neue Bold">%s</FONT></TD></TR>\n' % (module['name'])
# port rows
n_in  = max(len(module['input_ports']), 1)
n_out = max(len(module['output_ports']), 1)
for i in range(0, n_in * n_out):
    s += '<TR>\n'
    if i % n_out == 0:
        if i//n_out < len(module['input_ports']):
            s += '<TD ROWSPAN="%d" PORT="i%d"><FONT COLOR="white">%s</FONT></TD>\n' % (n_out, i//n_out, module['input_ports'][i//n_out]['name'])
    if i % n_in == 0:
        if i//n_in < len(module['output_ports']):
            s += '<TD ROWSPAN="%d" PORT="o%d"><FONT COLOR="white">%s</FONT></TD>\n' % (n_in, i//n_in, module['output_ports'][i//n_in]['name'])
    s += '</TR>\n'
# interface rows (incoming, outgoing)
n_in  = max(len(module['incoming_interfaces']), 1)
n_out = max(len(module['outgoing_interfaces']), 1)
for i in range(0, n_in * n_out):
    s += '<TR>\n'
    if i % n_out == 0:
        if i//n_out < len(module['incoming_interfaces']):
            s += '<TD ROWSPAN="%d" PORT="ii%d"><FONT COLOR="white">%s</FONT></TD>\n' % (n_out, i//n_out, module['incoming_interfaces'][i//n_out]['name'])
    if i % n_in == 0:
        if i//n_in < len(module['outgoing_interfaces']):
            s += '<TD ROWSPAN="%d" PORT="io%d"><FONT COLOR="white">%s</FONT></TD>\n' % (n_in, i//n_in, module['outgoing_interfaces'][i//n_in]['name'])
    s += '</TR>\n'
# interface rows -- the rest
n = len(module['interfaces'])
for i in range(0, n):
    s += '<TR>\n'
    s += '<TD ROWSPAN="1" PORT="iri%d"><FONT COLOR="white">%s</FONT></TD>\n' % (i, module['interfaces'][i]['name'])
    s += '<TD ROWSPAN="1" PORT="iro%d"><FONT COLOR="white">%s</FONT></TD>\n' % (i, module['interfaces'][i]['name'])
    s += '</TR>\n'
s += '</TABLE>>'
graph.add_node(pydotplus.graphviz.Node(module['name'], label=s, shape='none', fontname='Helvetica Neue'))


s =  '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="9">\n'
s += write_nodes(module, 'input_ports', 'i', direction='in', set_name='inputs')
s += write_nodes(module, 'incoming_interfaces', 'ii', kind='interface', direction='in', set_name='inputs')
# s += write_nodes(module, 'interfaces', 'iri', set_name='incoming_rest_interfaces', kind='interface', direction='in', set_name='inputs')
s += '</TABLE>>'
graph.add_node(pydotplus.graphviz.Node('inputs', label=s, shape='none', fontname=DEFAULT_FONT, labeljust='r'))

s =  '<<TABLE BORDER="0" CELLBORDER="0" CELLSPACING="9">\n'
s += write_nodes(module, 'output_ports', 'o', direction='out', set_name='outputs')
s += write_nodes(module, 'outgoing_interfaces', 'io', kind='interface', direction='out', set_name='outputs')
# s += write_nodes(module, 'interfaces', 'iro', set_name='outgoing_rest_interfaces', kind='interface', direction='out', set_name='outputs')
s += '</TABLE>>'
graph.add_node(pydotplus.graphviz.Node('outputs', label=s, shape='none', fontname=DEFAULT_FONT, labeljust='l'))

add_edges(module, 'input_ports', 'i', direction='in', set_name='inputs')
add_edges(module, 'incoming_interfaces', 'ii', kind='interface', direction='in', set_name='inputs')
add_edges(module, 'output_ports', 'o', direction='out', set_name='outputs')
add_edges(module, 'outgoing_interfaces', 'io', kind='interface', direction='out', set_name='outputs')

with open("prova.pdf", "wb") as f:
    f.write(graph.create_pdf())
