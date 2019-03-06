from docutils import nodes
from docutils.parsers.rst import Directive
import os
import prettyplot

class SVPrettyPlot(Directive):

    required_arguments = 1
    optional_arguments = 1

    def run(self, path, genimg_path='_build/genimg'):
        basename = os.path.basename(path)
        s = ".. _%s:\n" % basename
        s += ".. figure:: %s/%s.pdf\n" % (genimg_path, basename)
        s += ":figwidth: 70%\n"
        s += ":width: 70%\n"
        s += ":align: center\n"
        paragraph_node = nodes.paragraph(text=s)
        try:
            os.makedirs(genimg_path)
        except FileExistsError:
            pass
        prettyplot.sv_prettyplot(path, '%s/%s.pdf' % (genimg_path, basename))
        return [paragraph_node]

def setup(app):
    app.add_directive("svprettyplot", SVPrettyPlot)
    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
