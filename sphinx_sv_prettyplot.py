from docutils import nodes
from docutils.parsers.rst import Directive
import os
import svprettyplot.prettyplot as prettyplot
from docutils.parsers.rst.directives.images import Image
from sphinx.util.docutils import SphinxDirective
from sphinx.ext.graphviz import figure_wrapper
from sphinx.errors import SphinxError
from docutils.parsers.rst import directives

class SVPrettyPlot(Image, SphinxDirective):

    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = False

    option_spec = Image.option_spec.copy()
    option_spec['caption'] = directives.unchanged
    has_content = True

    def run(self):
        path = self.arguments[0]
        try:
            genimg_path = self.arguments[1] or '_build/genimg'
        except IndexError:
            genimg_path = '_build/genimg'

        document = self.state.document

        # Store code in a special docutils node and pick up at rendering
        # node = svprettyplotnode()

        basename = os.path.basename(path)
        inner_node = nodes.image(uri='%s/%s.pdf' % (genimg_path, basename), figwidth='95%', width='95%', align='center')

        node = inner_node

        try:
            os.makedirs(genimg_path)
        except FileExistsError:
            pass
        prettyplot.sv_prettyplot(path, '%s/%s.pdf' % (genimg_path, basename))

        self.arguments = ["dummy"]
        (inner_node['image_node'],) = Image.run(self)

        return [node]

def setup(app):
    app.add_directive("svprettyplot", SVPrettyPlot)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
